// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

/* A/B over-the-air update state machine with confirm-or-rollback (pure logic, host-testable).
 * Flash access, hashing and the actual boot switch are supplied by the HAL; this module decides what is allowed and when to roll back. */
#ifndef WL_OTA_H
#define WL_OTA_H
#include <stdint.h>

typedef enum {
  WL_OTA_IDLE = 0,
  WL_OTA_RECEIVING,
  WL_OTA_STAGED,     /* all bytes received, hash not yet verified */
  WL_OTA_VERIFIED,   /* hash matches, ready to switch */
  WL_OTA_TRIAL,      /* new slot booted once, waiting for confirm */
  WL_OTA_CONFIRMED,  /* update accepted */
  WL_OTA_ROLLED_BACK
} wl_ota_state_t;

typedef struct {
  wl_ota_state_t state;
  uint8_t active_slot;    /* 0 = A, 1 = B: slot the node currently boots */
  uint8_t staged_slot;    /* slot being written */
  uint32_t expected_size;
  uint32_t received;
  uint32_t trial_deadline_s;
  uint32_t trial_start_s;
  uint32_t confirm_timeout_s;
  uint8_t previous_slot;
} wl_ota_t;

void wl_ota_init(wl_ota_t *o, uint8_t active_slot);
/* target slot must be the inactive one */
int wl_ota_begin(wl_ota_t *o, uint8_t slot, uint32_t size);
/* chunk must arrive at the next expected offset; duplicates (offset < received) are accepted and ignored; gaps are rejected */
int wl_ota_chunk(wl_ota_t *o, uint32_t offset, uint32_t len);
/* hash_ok: result of the HAL hash comparison against the signed manifest */
int wl_ota_verify(wl_ota_t *o, int hash_ok);
/* switch to the new slot for one trial boot */
int wl_ota_commit(wl_ota_t *o, uint32_t now_s, uint32_t confirm_timeout_s);
/* the booted image confirms itself */
int wl_ota_confirm(wl_ota_t *o);
/* call periodically; returns 1 when a rollback happened (the caller must then boot the previous slot) */
int wl_ota_tick(wl_ota_t *o, uint32_t now_s);

#endif
