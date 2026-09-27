// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

#include "wl_modes.h"
#include <string.h>

#define SOC_SAFE_ENTER 20u   /* below this: safe mode */
#define SOC_SAFE_EXIT 45u    /* hysteresis: leave safe mode above this */
#define SOC_SCIENCE_MIN 50u
#define SOC_BURN_MIN 40u
#define SOC_ECLIPSE_MIN 35u

void wl_modes_init(wl_state_t *s) {
  memset(s, 0, sizeof *s);
  s->mode = WL_MODE_LAUNCH;
  s->level = 0;
}

const char *wl_mode_name(wl_mode_t m) {
  static const char *const names[] = {"LAUNCH", "DEPLOY", "COMMISSION", "NOMINAL", "SCIENCE",
                                      "BURN",   "ECLIPSE", "SAFE",       "SURVIVAL", "SCIENCE_LITE"};
  return names[m];
}

static void outputs(wl_state_t *s, const wl_inputs_t *in) {
  /* level from health, permissions from mode and level */
  if (!in->fc_ok)
    s->level = 3;
  else if (!in->packs_ok)
    s->level = 2;
  else if (!in->heavy_compute_ok)
    s->level = 1;
  else
    s->level = 0;
  s->allow_payloads = 0;
  s->allow_heavy_compute = 0;
  s->allow_light_compute = 0;
  s->allow_thruster = 0;
  switch (s->mode) {
    case WL_MODE_NOMINAL:
    case WL_MODE_SCIENCE:
      s->allow_payloads = s->level <= 2;
      s->allow_heavy_compute = s->level == 0 && s->mode == WL_MODE_SCIENCE;
      s->allow_light_compute = in->light_compute_ok && s->mode == WL_MODE_SCIENCE;
      break;
    case WL_MODE_SCIENCE_LITE:
      s->allow_payloads = 1;
      s->allow_light_compute = 1;
      break;
    case WL_MODE_BURN:
      s->allow_thruster = 1; /* every other load is cut in burn mode */
      break;
    case WL_MODE_ECLIPSE:
      s->allow_payloads = s->level <= 1;
      break;
    case WL_MODE_COMMISSION:
      s->allow_payloads = 1;
      break;
    default:
      break; /* LAUNCH, DEPLOY, SAFE, SURVIVAL: essential loads only */
  }
}

int wl_modes_step(wl_state_t *s, const wl_inputs_t *in) {
  const wl_mode_t old = s->mode;
  wl_mode_t m = old;

  /* Overrides in strict priority order: the supervisor's view wins over everything. */
  wl_inputs_t chk = *in;
  if (chk.soc_pct > 100) chk.soc_pct = 0; /* out-of-range value means unknown: treat as empty */
  in = &chk;
  if (!in->fc_ok) {
    if (old != WL_MODE_SURVIVAL) s->resume_mode = (old == WL_MODE_LAUNCH || old == WL_MODE_DEPLOY) ? old : WL_MODE_SAFE;
    m = WL_MODE_SURVIVAL;
  } else if (old == WL_MODE_SURVIVAL) {
    m = s->resume_mode; /* flight controller is back: resume the launch/deploy sequence, otherwise recover through safe mode */
  } else if (old == WL_MODE_LAUNCH) {
    if (in->sep_timer_done) m = WL_MODE_DEPLOY;
  } else if (old == WL_MODE_DEPLOY) {
    if (in->deploy_done) m = WL_MODE_COMMISSION;
  } else {
    const int critical = !in->packs_ok || !in->temp_ok || in->soc_pct < SOC_SAFE_ENTER;
    if (critical) {
      m = WL_MODE_SAFE;
    } else if (old == WL_MODE_SAFE) {
      if (in->soc_pct >= SOC_SAFE_EXIT && in->packs_ok && in->temp_ok) m = WL_MODE_NOMINAL;
    } else if (old == WL_MODE_COMMISSION) {
      if (in->commissioning_ok) m = WL_MODE_NOMINAL;
    } else if (!in->sunlit) {
      if (old == WL_MODE_BURN)
        m = WL_MODE_ECLIPSE; /* the thruster runs only in sunlight */
      else if (in->soc_pct >= SOC_ECLIPSE_MIN)
        m = WL_MODE_ECLIPSE;
      else
        m = WL_MODE_SAFE;
    } else {
      /* sunlit and healthy: choose the most useful permitted mode */
      if (in->burn_requested && in->thruster_ok && in->sun_biased && in->wings_deployed && in->soc_pct >= SOC_BURN_MIN)
        m = WL_MODE_BURN;
      else if (in->science_requested && in->optics_ok && in->soc_pct >= ((old == WL_MODE_SCIENCE || old == WL_MODE_SCIENCE_LITE) ? SOC_SCIENCE_MIN - 5 : SOC_SCIENCE_MIN) && (old != WL_MODE_BURN || !in->burn_requested) &&
               (in->heavy_compute_ok || in->light_compute_ok))
        m = in->heavy_compute_ok ? WL_MODE_SCIENCE : WL_MODE_SCIENCE_LITE; /* keep imaging alive on the light computer */
      else
        m = WL_MODE_NOMINAL;
    }
  }
  s->mode = m;
  outputs(s, in);
  return m != old;
}
