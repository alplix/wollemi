/* Time-tagged command queue with absolute-time and orbit-position triggers (pure logic, host-testable). */
#ifndef GK_CMDQ_H
#define GK_CMDQ_H
#include <stdint.h>

#define GK_CMDQ_SLOTS 64

typedef enum { GK_TRIG_NONE = 0, GK_TRIG_TIME = 1, GK_TRIG_ORBIT = 2 } gk_trigger_t;

typedef struct {
  uint8_t used;
  uint8_t trigger_type;
  uint32_t trigger_value;   /* TAI seconds, or orbit position in 0.01 degree units */
  uint16_t cmd_apid;
  uint8_t args[16];
  uint16_t mode_mask;       /* bit per gk_mode_t in which the command may run; 0 = any mode */
  uint32_t valid_until;     /* drop the entry if not started before this TAI time; 0 = never */
} gk_cmd_t;

typedef struct {
  gk_cmd_t slot[GK_CMDQ_SLOTS];
} gk_cmdq_t;

void gk_cmdq_init(gk_cmdq_t *q);
/* Store a command in a numbered slot (replaces the slot). Returns 0 on success, -1 for a bad slot. */
int gk_cmdq_load(gk_cmdq_t *q, uint16_t slot, const gk_cmd_t *cmd);
int gk_cmdq_cancel(gk_cmdq_t *q, uint16_t slot);
/* Pop the next due command (earliest trigger first). Skips and drops expired entries; returns 1 if a command was produced.
 * Commands whose mode_mask forbids the current mode stay queued. */
int gk_cmdq_pop_due(gk_cmdq_t *q, uint32_t now_tai, uint32_t orbit_pos, uint8_t mode, gk_cmd_t *out, int *expired);
int gk_cmdq_count(const gk_cmdq_t *q);

#endif
