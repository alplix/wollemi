/* Heartbeat monitoring and staged FDIR escalation (pure logic, host-testable). */
#ifndef WL_FDIR_H
#define WL_FDIR_H
#include <stdint.h>

#define WL_FDIR_NODES 8

typedef enum {
  WL_ACT_NONE = 0,
  WL_ACT_RETRY,            /* ask again / re-send */
  WL_ACT_RESTART_COMPONENT,
  WL_ACT_POWER_CYCLE,
  WL_ACT_SWITCH_REDUNDANT,
  WL_ACT_DEGRADE           /* give up on the node and lower the degradation level */
} wl_action_t;

typedef struct {
  uint8_t node;
  wl_action_t action;
} wl_fdir_event_t;

typedef struct {
  uint32_t timeout_ms;         /* heartbeat silence that counts as a failure */
  uint32_t healthy_reset_ms;   /* continuous health needed to reset the escalation */
  uint32_t last_hb_ms[WL_FDIR_NODES];
  uint32_t last_fail_ms[WL_FDIR_NODES];
  uint32_t healthy_since_ms[WL_FDIR_NODES];
  uint8_t stage[WL_FDIR_NODES];       /* 0 = healthy, 1..5 = escalation stage reached */
  uint8_t monitored[WL_FDIR_NODES];
  uint8_t redundant[WL_FDIR_NODES];   /* a redundant unit exists (skips SWITCH_REDUNDANT otherwise) */
  uint8_t degraded[WL_FDIR_NODES];
} wl_fdir_t;

void wl_fdir_init(wl_fdir_t *f, uint32_t timeout_ms, uint32_t healthy_reset_ms);
void wl_fdir_monitor(wl_fdir_t *f, uint8_t node, uint8_t has_redundant, uint32_t now_ms);
void wl_fdir_heartbeat(wl_fdir_t *f, uint8_t node, uint32_t now_ms);
/* Evaluate all nodes; write at most max events and return how many were produced. */
int wl_fdir_tick(wl_fdir_t *f, uint32_t now_ms, wl_fdir_event_t *out, int max);

#endif
