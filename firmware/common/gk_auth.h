/* Telecommand authentication: CRC, structure, validity window, replay protection and Ed25519 signature.
 * Host-testable pure C99; the signature primitive is TweetNaCl (firmware/third_party/tweetnacl, public domain). */
#ifndef GK_AUTH_H
#define GK_AUTH_H
#include <stdint.h>
#include <stddef.h>

#define GK_AUTH_MAX_JUMP 1000000u /* largest accepted counter step: one mistyped counter cannot lock the link for ever */
#define GK_AUTH_KEYS 2 /* current and previous operational key */

typedef enum {
  GK_AUTH_OK = 0,
  GK_AUTH_BAD_LEN = -1,
  GK_AUTH_BAD_CRC = -2,
  GK_AUTH_NOT_TC = -3,
  GK_AUTH_EXPIRED = -4,
  GK_AUTH_REPLAY = -5,
  GK_AUTH_BAD_SIG = -6,
  GK_AUTH_NO_KEY = -7,
  GK_AUTH_BAD_HEADER = -8,
  GK_AUTH_JUMP = -9
} gk_auth_result_t;

typedef struct {
  uint8_t pubkey[GK_AUTH_KEYS][32];
  uint8_t key_valid[GK_AUTH_KEYS]; /* 0/1 */
  uint32_t last_counter;           /* highest accepted counter (persist in FRAM) */
} gk_auth_t;

void gk_auth_init(gk_auth_t *a);
/* Install a new key in slot 0 and demote the old one to slot 1 (call only after verifying a key_rotate command). */
void gk_auth_rotate(gk_auth_t *a, const uint8_t new_pub[32]);
/* Check a complete telecommand packet. On success updates last_counter and returns GK_AUTH_OK. */
int gk_auth_check(gk_auth_t *a, const uint8_t *pkt, size_t len, uint32_t now_coarse);

#endif
