#include "wl_fdir.h"
#include <string.h>

void wl_fdir_init(wl_fdir_t *f, uint32_t timeout_ms, uint32_t healthy_reset_ms) {
  memset(f, 0, sizeof *f);
  f->timeout_ms = timeout_ms;
  f->healthy_reset_ms = healthy_reset_ms;
}

void wl_fdir_monitor(wl_fdir_t *f, uint8_t node, uint8_t has_redundant, uint32_t now_ms) {
  if (node >= WL_FDIR_NODES) return;
  f->monitored[node] = 1;
  f->redundant[node] = has_redundant;
  f->last_hb_ms[node] = now_ms;
  f->healthy_since_ms[node] = now_ms;
}

void wl_fdir_heartbeat(wl_fdir_t *f, uint8_t node, uint32_t now_ms) {
  if (node >= WL_FDIR_NODES || !f->monitored[node] || f->degraded[node]) return;
  f->last_hb_ms[node] = now_ms;
  if (f->stage[node] && f->healthy_since_ms[node] == 0) f->healthy_since_ms[node] = now_ms;
}

/* Escalation ladder: retry -> restart component -> power-cycle -> switch redundant -> degrade. */
static wl_action_t next_action(wl_fdir_t *f, uint8_t node) {
  uint8_t s = (uint8_t)(f->stage[node] + 1);
  if (s == 4 && !f->redundant[node]) s = 5; /* no redundant unit: skip straight to degrade */
  if (s > 5) s = 5;
  f->stage[node] = s;
  static const wl_action_t ladder[] = {WL_ACT_NONE, WL_ACT_RETRY, WL_ACT_RESTART_COMPONENT, WL_ACT_POWER_CYCLE,
                                       WL_ACT_SWITCH_REDUNDANT, WL_ACT_DEGRADE};
  return ladder[s];
}

int wl_fdir_tick(wl_fdir_t *f, uint32_t now_ms, wl_fdir_event_t *out, int max) {
  int n = 0;
  for (uint8_t node = 0; node < WL_FDIR_NODES; node++) {
    if (!f->monitored[node] || f->degraded[node]) continue;
    const int32_t silent_s = (int32_t)(now_ms - f->last_hb_ms[node]); /* signed: a heartbeat stamped just after 'now' is not silence */
    if (silent_s > 0 && (uint32_t)silent_s > f->timeout_ms) {
      /* one action per timeout period: wait a full timeout before escalating again */
      if (n < max && (f->stage[node] == 0 || now_ms - f->last_fail_ms[node] >= f->timeout_ms)) { /* no room: keep the state, report on the next tick */
        f->last_fail_ms[node] = now_ms;
        f->healthy_since_ms[node] = 0;
        wl_action_t a = next_action(f, node);
        if (a == WL_ACT_DEGRADE) f->degraded[node] = 1;
        out[n].node = node;
        out[n].action = a;
        n++;
      }
    } else if (f->stage[node] != 0) {
      if (f->healthy_since_ms[node] == 0) f->healthy_since_ms[node] = now_ms;
      if (now_ms - f->healthy_since_ms[node] >= f->healthy_reset_ms) f->stage[node] = 0; /* healed */
    }
  }
  return n;
}
