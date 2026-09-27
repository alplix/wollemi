/* Telecommand authentication: CRC, structure, validity window, replay protection and Ed25519 signature.
 * Host-testable pure C99; the signature primitive is TweetNaCl (firmware/third_party/tweetnacl, public domain). */
#ifndef WL_AUTH_H
#define WL_AUTH_H
#include <stdint.h>
#include <stddef.h>

#define WL_AUTH_MAX_JUMP 1000000u /* largest accepted counter step: one mistyped counter cannot lock the link for ever */
#define WL_AUTH_KEYS 2 /* current and previous operational key */

typedef enum {
  WL_AUTH_OK = 0,
  WL_AUTH_BAD_LEN = -1,
  WL_AUTH_BAD_CRC = -2,
  WL_AUTH_NOT_TC = -3,
  WL_AUTH_EXPIRED = -4,
  WL_AUTH_REPLAY = -5,
  WL_AUTH_BAD_SIG = -6,
  WL_AUTH_NO_KEY = -7,
  WL_AUTH_BAD_HEADER = -8,
  WL_AUTH_JUMP = -9
} wl_auth_result_t;

typedef struct {
  uint8_t pubkey[WL_AUTH_KEYS][32];
  uint8_t key_valid[WL_AUTH_KEYS]; /* 0/1 */
  uint32_t last_counter;           /* highest accepted counter (persist in FRAM) */
} wl_auth_t;

void wl_auth_init(wl_auth_t *a);
/* Install a new key in slot 0 and demote the old one to slot 1 (call only after verifying a key_rotate command). */
void wl_auth_rotate(wl_auth_t *a, const uint8_t new_pub[32]);
/* Check a complete telecommand packet. On success updates last_counter and returns WL_AUTH_OK. */
int wl_auth_check(wl_auth_t *a, const uint8_t *pkt, size_t len, uint32_t now_coarse);

#endif
