// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

/* Host unit tests for the firmware core: mode ladder, FDIR, command queue, OTA. */
#include <stdio.h>
#include <string.h>
#include "../common/wl_cmdq.h"
#include "../common/wl_fdir.h"
#include "../common/wl_modes.h"
#include "../common/wl_ota.h"

static int checks = 0, failures = 0;
#define CHECK(c)                                                             \
  do {                                                                       \
    checks++;                                                                \
    if (!(c)) {                                                              \
      failures++;                                                            \
      printf("FAIL %s:%d: %s\n", __FILE__, __LINE__, #c);                    \
    }                                                                        \
  } while (0)

static wl_inputs_t healthy(void) {
  wl_inputs_t in;
  memset(&in, 0, sizeof in);
  in.fc_ok = in.packs_ok = in.heavy_compute_ok = in.light_compute_ok = in.thruster_ok = in.temp_ok = 1;
  in.sunlit = in.sun_biased = in.wings_deployed = in.optics_ok = 1;
  in.soc_pct = 90;
  return in;
}

static void test_modes(void) {
  wl_state_t s;
  wl_inputs_t in = healthy();
  wl_modes_init(&s);
  CHECK(s.mode == WL_MODE_LAUNCH);
  in.sep_timer_done = 1;
  CHECK(wl_modes_step(&s, &in) == 1 && s.mode == WL_MODE_DEPLOY);
  in.deploy_done = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_COMMISSION);
  in.commissioning_ok = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL);
  in.science_requested = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE && s.allow_heavy_compute && s.level == 0);
  /* eclipse: heavy compute off, payloads still allowed at level 0 */
  in.sunlit = 0;
  in.soc_pct = 80;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_ECLIPSE && !s.allow_heavy_compute && s.allow_payloads);
  /* burn needs sunlight, sun bias, wings and charge */
  in.sunlit = 1;
  in.science_requested = 0;
  in.burn_requested = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_BURN && s.allow_thruster && !s.allow_payloads && !s.allow_heavy_compute);
  in.sun_biased = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL && !s.allow_thruster); /* burn refused without a sun-biased attitude */
  in.sun_biased = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_BURN);
  in.sunlit = 0; /* the thruster never runs in eclipse */
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_ECLIPSE && !s.allow_thruster);
  in.burn_requested = 0;
  in.sunlit = 1;
  /* low charge -> safe, with hysteresis */
  in.soc_pct = 15;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE);
  in.soc_pct = 30;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE);
  in.soc_pct = 46;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL);
  /* heavy compute lost: level 1 */
  in.heavy_compute_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.level == 1 && !s.allow_heavy_compute);
  in.soc_pct = 90;
  in.science_requested = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE_LITE && !s.allow_heavy_compute && s.allow_light_compute && s.allow_payloads); /* imaging continues on the CM5 */
  in.light_compute_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL); /* no compute for imaging at all */
  in.light_compute_ok = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE_LITE);
  in.heavy_compute_ok = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE && s.allow_heavy_compute); /* the Jetson coming back restores full science */
  in.heavy_compute_ok = 0;
  /* packs lost: safe, level 2 */
  in.packs_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE && s.level == 2);
  /* flight controller dead: survival, level 3; recovery goes through safe */
  in.fc_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SURVIVAL && s.level == 3 && !s.allow_payloads);
  in = healthy();
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE);
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL);
  /* thermal violation forces safe */
  in.temp_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE);
}

static void test_fdir(void) {
  wl_fdir_t f;
  wl_fdir_event_t ev[4];
  wl_fdir_init(&f, 1000, 5000);
  wl_fdir_monitor(&f, 1, 1, 0);   /* node 1 has a redundant unit */
  wl_fdir_monitor(&f, 2, 0, 0);   /* node 2 does not */
  uint32_t t = 0;
  int n;
  /* healthy heartbeats: no events */
  for (t = 100; t <= 900; t += 100) {
    wl_fdir_heartbeat(&f, 1, t);
    wl_fdir_heartbeat(&f, 2, t);
  }
  CHECK(wl_fdir_tick(&f, 900, ev, 4) == 0);
  /* node 1 goes silent: one action per timeout period, in escalation order */
  wl_action_t got1[6];
  int k = 0;
  for (t = 1000; t < 9000 && k < 6; t += 100) {
    wl_fdir_heartbeat(&f, 2, t); /* node 2 stays alive */
    n = wl_fdir_tick(&f, t, ev, 4);
    for (int i = 0; i < n; i++)
      if (ev[i].node == 1) got1[k++] = ev[i].action;
  }
  CHECK(k == 5);
  CHECK(got1[0] == WL_ACT_RETRY && got1[1] == WL_ACT_RESTART_COMPONENT && got1[2] == WL_ACT_POWER_CYCLE &&
        got1[3] == WL_ACT_SWITCH_REDUNDANT && got1[4] == WL_ACT_DEGRADE);
  CHECK(f.degraded[1] == 1);
  /* no further events for a degraded node */
  CHECK(wl_fdir_tick(&f, 20000, ev, 4) == 1 && ev[0].node == 2); /* node 2 has been silent since 9000 */
  /* node without a redundant unit skips SWITCH_REDUNDANT */
  wl_fdir_t g;
  wl_fdir_init(&g, 1000, 5000);
  wl_fdir_monitor(&g, 3, 0, 0);
  wl_action_t acts[6];
  k = 0;
  for (t = 1100; t < 12000 && k < 6; t += 100) {
    n = wl_fdir_tick(&g, t, ev, 4);
    for (int i = 0; i < n; i++) acts[k++] = ev[i].action;
  }
  CHECK(k == 4 && acts[0] == WL_ACT_RETRY && acts[1] == WL_ACT_RESTART_COMPONENT && acts[2] == WL_ACT_POWER_CYCLE &&
        acts[3] == WL_ACT_DEGRADE);
  /* a node that recovers heals after the healthy period and starts again from retry */
  wl_fdir_t h;
  wl_fdir_init(&h, 1000, 3000);
  wl_fdir_monitor(&h, 4, 1, 0);
  n = wl_fdir_tick(&h, 1500, ev, 4);
  CHECK(n == 1 && ev[0].action == WL_ACT_RETRY && h.stage[4] == 1);
  for (t = 1600; t <= 6000; t += 100) {
    wl_fdir_heartbeat(&h, 4, t);
    wl_fdir_tick(&h, t, ev, 4);
  }
  CHECK(h.stage[4] == 0);
  n = wl_fdir_tick(&h, 9000, ev, 4);
  CHECK(n == 1 && ev[0].action == WL_ACT_RETRY);
}

static void test_cmdq(void) {
  wl_cmdq_t q;
  wl_cmd_t c, out;
  int expired = 0;
  wl_cmdq_init(&q);
  memset(&c, 0, sizeof c);
  c.trigger_type = WL_TRIG_TIME;
  c.cmd_apid = 0x140;
  c.trigger_value = 200;
  CHECK(wl_cmdq_load(&q, 5, &c) == 0);
  c.trigger_value = 100;
  c.cmd_apid = 0x141;
  CHECK(wl_cmdq_load(&q, 9, &c) == 0);
  c.trigger_value = 150;
  c.cmd_apid = 0x142;
  c.mode_mask = 1u << WL_MODE_SCIENCE; /* only in science mode */
  CHECK(wl_cmdq_load(&q, 12, &c) == 0);
  CHECK(wl_cmdq_load(&q, 64, &c) == -1);
  CHECK(wl_cmdq_count(&q) == 3);
  CHECK(wl_cmdq_pop_due(&q, 50, 0, WL_MODE_NOMINAL, &out, &expired) == 0); /* nothing due yet */
  CHECK(wl_cmdq_pop_due(&q, 300, 0, WL_MODE_NOMINAL, &out, &expired) == 1 && out.cmd_apid == 0x141); /* earliest first */
  CHECK(wl_cmdq_pop_due(&q, 300, 0, WL_MODE_NOMINAL, &out, &expired) == 1 && out.cmd_apid == 0x140);
  CHECK(wl_cmdq_pop_due(&q, 300, 0, WL_MODE_NOMINAL, &out, &expired) == 0); /* science-only command stays queued */
  CHECK(wl_cmdq_count(&q) == 1);
  CHECK(wl_cmdq_pop_due(&q, 300, 0, WL_MODE_SCIENCE, &out, &expired) == 1 && out.cmd_apid == 0x142);
  /* validity window and orbit triggers */
  memset(&c, 0, sizeof c);
  c.trigger_type = WL_TRIG_ORBIT;
  c.trigger_value = 9000;
  c.cmd_apid = 0x150;
  c.valid_until = 500;
  wl_cmdq_load(&q, 1, &c);
  CHECK(wl_cmdq_pop_due(&q, 100, 8000, WL_MODE_NOMINAL, &out, &expired) == 0);
  CHECK(wl_cmdq_pop_due(&q, 100, 9500, WL_MODE_NOMINAL, &out, &expired) == 1 && out.cmd_apid == 0x150);
  wl_cmdq_load(&q, 2, &c);
  CHECK(wl_cmdq_pop_due(&q, 600, 9500, WL_MODE_NOMINAL, &out, &expired) == 0 && expired == 1); /* expired: dropped */
  CHECK(wl_cmdq_count(&q) == 0);
  wl_cmdq_load(&q, 3, &c);
  CHECK(wl_cmdq_cancel(&q, 3) == 0 && wl_cmdq_count(&q) == 0);
}

static void test_ota(void) {
  wl_ota_t o;
  wl_ota_init(&o, 0);
  CHECK(wl_ota_begin(&o, 0, 1000) == -2); /* the running slot may not be overwritten */
  CHECK(wl_ota_begin(&o, 1, 1000) == 0 && o.state == WL_OTA_RECEIVING);
  CHECK(wl_ota_chunk(&o, 0, 400) == 0 && o.received == 400);
  CHECK(wl_ota_chunk(&o, 600, 400) == -2);       /* gap rejected */
  CHECK(wl_ota_chunk(&o, 200, 100) == 0 && o.received == 400); /* duplicate ignored */
  CHECK(wl_ota_chunk(&o, 400, 700) == -3);       /* overrun */
  CHECK(wl_ota_chunk(&o, 400, 600) == 0 && o.state == WL_OTA_STAGED);
  CHECK(wl_ota_verify(&o, 0) == -2 && o.state == WL_OTA_IDLE && o.active_slot == 0); /* bad hash: keep the old image */
  /* good update with confirmation */
  CHECK(wl_ota_begin(&o, 1, 500) == 0);
  wl_ota_chunk(&o, 0, 500);
  CHECK(wl_ota_verify(&o, 1) == 0 && o.state == WL_OTA_VERIFIED);
  CHECK(wl_ota_commit(&o, 1000, 120) == 0 && o.active_slot == 1 && o.state == WL_OTA_TRIAL);
  CHECK(wl_ota_begin(&o, 0, 10) == -1);           /* busy during a trial */
  CHECK(wl_ota_tick(&o, 1100) == 0);
  CHECK(wl_ota_confirm(&o) == 0 && o.state == WL_OTA_CONFIRMED);
  CHECK(wl_ota_tick(&o, 5000) == 0 && o.active_slot == 1);
  /* update that never confirms rolls back */
  CHECK(wl_ota_begin(&o, 0, 500) == 0);
  wl_ota_chunk(&o, 0, 500);
  wl_ota_verify(&o, 1);
  CHECK(wl_ota_commit(&o, 10000, 120) == 0 && o.active_slot == 0);
  CHECK(wl_ota_tick(&o, 10100) == 0);
  CHECK(wl_ota_tick(&o, 10121) == 1 && o.state == WL_OTA_ROLLED_BACK && o.active_slot == 1);
  CHECK(wl_ota_commit(&o, 20000, 60) == -1);       /* cannot commit without a verified image */
}

static void test_review_fixes(void) {
  /* survival recovery during launch/deploy resumes the sequence instead of skipping it */
  wl_state_t s;
  wl_inputs_t in = healthy();
  wl_modes_init(&s);
  in.fc_ok = 0;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SURVIVAL);
  in.fc_ok = 1;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_LAUNCH);
  /* science hysteresis and unknown state of charge */
  wl_modes_init(&s);
  in = healthy();
  in.sep_timer_done = in.deploy_done = in.commissioning_ok = 1;
  in.science_requested = 1;
  for (int i = 0; i < 4; i++) wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE);
  in.soc_pct = 47;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SCIENCE); /* inside the 5 % band */
  in.soc_pct = 255;
  wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_SAFE);    /* 255 = unknown, treated as empty */
  in = healthy();
  in.science_requested = 1;
  in.optics_ok = 0;
  wl_modes_init(&s);
  in.sep_timer_done = in.deploy_done = in.commissioning_ok = 1;
  for (int i = 0; i < 4; i++) wl_modes_step(&s, &in);
  CHECK(s.mode == WL_MODE_NOMINAL); /* optics outside the window: no imaging */
  /* OTA overflow and timer wrap */
  wl_ota_t o;
  wl_ota_init(&o, 0);
  CHECK(wl_ota_begin(&o, 1, 1000) == 0);
  CHECK(wl_ota_chunk(&o, 0, 10) == 0);
  CHECK(wl_ota_chunk(&o, 10, 0xFFFFFFF8u) == -3);
  wl_ota_init(&o, 0);
  wl_ota_begin(&o, 1, 10);
  wl_ota_chunk(&o, 0, 10);
  wl_ota_verify(&o, 1);
  CHECK(wl_ota_commit(&o, 0xFFFFFFF0u, 100) == 0);
  CHECK(wl_ota_tick(&o, 0xFFFFFFF5u) == 0);         /* deadline wraps to 84: must not roll back early */
  CHECK(wl_ota_tick(&o, 0xFFFFFFF0u + 100u) == 1);
  /* FDIR: no event slot -> state is not advanced */
  wl_fdir_t f;
  wl_fdir_event_t ev[1];
  wl_fdir_init(&f, 1000, 5000);
  wl_fdir_monitor(&f, 0, 1, 0);
  wl_fdir_monitor(&f, 1, 1, 0);
  CHECK(wl_fdir_tick(&f, 2000, ev, 1) == 1);
  CHECK(f.stage[1] == 0);
  CHECK(wl_fdir_tick(&f, 2001, ev, 1) == 1 && ev[0].node == 1);
  /* heartbeat stamped slightly after now: no false alarm */
  wl_fdir_heartbeat(&f, 0, 5100);
  CHECK(wl_fdir_tick(&f, 5000, ev, 1) == 0 || ev[0].node != 0);
}

int main(void) {
  test_modes();
  test_fdir();
  test_cmdq();
  test_ota();
  test_review_fixes();
  printf("firmware core: %d checks, %d failures\n", checks, failures);
  return failures ? 1 : 0;
}
