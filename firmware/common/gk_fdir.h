/* Heartbeat monitoring and staged FDIR escalation (pure logic, host-testable). */
#ifndef GK_FDIR_H
#define GK_FDIR_H
#include <stdint.h>

#define GK_FDIR_NODES 8

typedef enum {
  GK_ACT_NONE = 0,
  GK_ACT_RETRY,            /* ask again / re-send */
  GK_ACT_RESTART_COMPONENT,
  GK_ACT_POWER_CYCLE,
  GK_ACT_SWITCH_REDUNDANT,
  GK_ACT_DEGRADE           /* give up on the node and lower the degradation level */
} gk_action_t;

typedef struct {
  uint8_t node;
  gk_action_t action;
} gk_fdir_event_t;

typedef struct {
  uint32_t timeout_ms;         /* heartbeat silence that counts as a failure */
  uint32_t healthy_reset_ms;   /* continuous health needed to reset the escalation */
  uint32_t last_hb_ms[GK_FDIR_NODES];
  uint32_t last_fail_ms[GK_FDIR_NODES];
  uint32_t healthy_since_ms[GK_FDIR_NODES];
  uint8_t stage[GK_FDIR_NODES];       /* 0 = healthy, 1..5 = escalation stage reached */
  uint8_t monitored[GK_FDIR_NODES];
  uint8_t redundant[GK_FDIR_NODES];   /* a redundant unit exists (skips SWITCH_REDUNDANT otherwise) */
  uint8_t degraded[GK_FDIR_NODES];
} gk_fdir_t;

void gk_fdir_init(gk_fdir_t *f, uint32_t timeout_ms, uint32_t healthy_reset_ms);
void gk_fdir_monitor(gk_fdir_t *f, uint8_t node, uint8_t has_redundant, uint32_t now_ms);
void gk_fdir_heartbeat(gk_fdir_t *f, uint8_t node, uint32_t now_ms);
/* Evaluate all nodes; write at most max events and return how many were produced. */
int gk_fdir_tick(gk_fdir_t *f, uint32_t now_ms, gk_fdir_event_t *out, int max);

#endif
