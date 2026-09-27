// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

#include "wl_cmdq.h"
#include <string.h>

void wl_cmdq_init(wl_cmdq_t *q) { memset(q, 0, sizeof *q); }

int wl_cmdq_load(wl_cmdq_t *q, uint16_t slot, const wl_cmd_t *cmd) {
  if (slot >= WL_CMDQ_SLOTS || !cmd || cmd->trigger_type == WL_TRIG_NONE) return -1;
  q->slot[slot] = *cmd;
  q->slot[slot].used = 1;
  return 0;
}

int wl_cmdq_cancel(wl_cmdq_t *q, uint16_t slot) {
  if (slot >= WL_CMDQ_SLOTS) return -1;
  q->slot[slot].used = 0;
  return 0;
}

int wl_cmdq_count(const wl_cmdq_t *q) {
  int n = 0;
  for (int i = 0; i < WL_CMDQ_SLOTS; i++) n += q->slot[i].used;
  return n;
}

static int due(const wl_cmd_t *c, uint32_t now_tai, uint32_t orbit_pos) {
  if (c->trigger_type == WL_TRIG_TIME) return now_tai >= c->trigger_value;
  if (c->trigger_type == WL_TRIG_ORBIT) return orbit_pos >= c->trigger_value;
  return 0;
}

int wl_cmdq_pop_due(wl_cmdq_t *q, uint32_t now_tai, uint32_t orbit_pos, uint8_t mode, wl_cmd_t *out, int *expired) {
  int best = -1;
  if (expired) *expired = 0;
  for (int i = 0; i < WL_CMDQ_SLOTS; i++) {
    wl_cmd_t *c = &q->slot[i];
    if (!c->used) continue;
    if (c->valid_until && now_tai > c->valid_until) { /* missed its window: drop it */
      c->used = 0;
      if (expired) (*expired)++;
      continue;
    }
    if (!due(c, now_tai, orbit_pos)) continue;
    if (c->mode_mask && !((c->mode_mask >> mode) & 1u)) continue; /* not allowed now: keep it queued */
    if (best < 0 || (c->trigger_type == WL_TRIG_TIME && q->slot[best].trigger_type == WL_TRIG_TIME &&
                     c->trigger_value < q->slot[best].trigger_value) ||
        (q->slot[best].trigger_type != WL_TRIG_TIME && c->trigger_type == WL_TRIG_TIME))
      best = i;
  }
  if (best < 0) return 0;
  *out = q->slot[best];
  q->slot[best].used = 0;
  return 1;
}
