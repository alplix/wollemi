#include "gk_ota.h"
#include <string.h>

void gk_ota_init(gk_ota_t *o, uint8_t active_slot) {
  memset(o, 0, sizeof *o);
  o->state = GK_OTA_IDLE;
  o->active_slot = active_slot & 1u;
  o->previous_slot = o->active_slot;
}

int gk_ota_begin(gk_ota_t *o, uint8_t slot, uint32_t size) {
  if (o->state == GK_OTA_TRIAL || o->state == GK_OTA_RECEIVING) return -1; /* busy */
  if ((slot & 1u) == o->active_slot || size == 0) return -2;               /* never overwrite the running image */
  o->state = GK_OTA_RECEIVING;
  o->staged_slot = slot & 1u;
  o->expected_size = size;
  o->received = 0;
  return 0;
}

int gk_ota_chunk(gk_ota_t *o, uint32_t offset, uint32_t len) {
  if (o->state != GK_OTA_RECEIVING) return -1;
  if (offset > o->received) return -2;                 /* gap: the ground must resend from 'received' */
  if (offset + len <= o->received) return 0;           /* duplicate of data we already have */
  if (offset + len > o->expected_size) return -3;
  o->received = offset + len;
  if (o->received == o->expected_size) o->state = GK_OTA_STAGED;
  return 0;
}

int gk_ota_verify(gk_ota_t *o, int hash_ok) {
  if (o->state != GK_OTA_STAGED) return -1;
  if (!hash_ok) {
    o->state = GK_OTA_IDLE; /* discard the image, keep running the old one */
    return -2;
  }
  o->state = GK_OTA_VERIFIED;
  return 0;
}

int gk_ota_commit(gk_ota_t *o, uint32_t now_s, uint32_t confirm_timeout_s) {
  if (o->state != GK_OTA_VERIFIED) return -1;
  o->previous_slot = o->active_slot;
  o->active_slot = o->staged_slot;
  o->confirm_timeout_s = confirm_timeout_s;
  o->trial_deadline_s = now_s + confirm_timeout_s;
  o->state = GK_OTA_TRIAL;
  return 0;
}

int gk_ota_confirm(gk_ota_t *o) {
  if (o->state != GK_OTA_TRIAL) return -1;
  o->state = GK_OTA_CONFIRMED;
  return 0;
}

int gk_ota_tick(gk_ota_t *o, uint32_t now_s) {
  if (o->state == GK_OTA_TRIAL && now_s >= o->trial_deadline_s) {
    o->active_slot = o->previous_slot; /* no confirmation in time: fall back */
    o->state = GK_OTA_ROLLED_BACK;
    return 1;
  }
  return 0;
}
