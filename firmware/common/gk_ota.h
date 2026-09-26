/* A/B over-the-air update state machine with confirm-or-rollback (pure logic, host-testable).
 * Flash access, hashing and the actual boot switch are supplied by the HAL; this module decides what is allowed and when to roll back. */
#ifndef GK_OTA_H
#define GK_OTA_H
#include <stdint.h>

typedef enum {
  GK_OTA_IDLE = 0,
  GK_OTA_RECEIVING,
  GK_OTA_STAGED,     /* all bytes received, hash not yet verified */
  GK_OTA_VERIFIED,   /* hash matches, ready to switch */
  GK_OTA_TRIAL,      /* new slot booted once, waiting for confirm */
  GK_OTA_CONFIRMED,  /* update accepted */
  GK_OTA_ROLLED_BACK
} gk_ota_state_t;

typedef struct {
  gk_ota_state_t state;
  uint8_t active_slot;    /* 0 = A, 1 = B: slot the node currently boots */
  uint8_t staged_slot;    /* slot being written */
  uint32_t expected_size;
  uint32_t received;
  uint32_t trial_deadline_s;
  uint32_t trial_start_s;
  uint32_t confirm_timeout_s;
  uint8_t previous_slot;
} gk_ota_t;

void gk_ota_init(gk_ota_t *o, uint8_t active_slot);
/* target slot must be the inactive one */
int gk_ota_begin(gk_ota_t *o, uint8_t slot, uint32_t size);
/* chunk must arrive at the next expected offset; duplicates (offset < received) are accepted and ignored; gaps are rejected */
int gk_ota_chunk(gk_ota_t *o, uint32_t offset, uint32_t len);
/* hash_ok: result of the HAL hash comparison against the signed manifest */
int gk_ota_verify(gk_ota_t *o, int hash_ok);
/* switch to the new slot for one trial boot */
int gk_ota_commit(gk_ota_t *o, uint32_t now_s, uint32_t confirm_timeout_s);
/* the booted image confirms itself */
int gk_ota_confirm(gk_ota_t *o);
/* call periodically; returns 1 when a rollback happened (the caller must then boot the previous slot) */
int gk_ota_tick(gk_ota_t *o, uint32_t now_s);

#endif
