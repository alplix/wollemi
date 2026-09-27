// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

#include "wl_auth.h"
#include <string.h>
#include "../../protocol/generated/wollemi_proto.h"
#include "../third_party/tweetnacl/tweetnacl.h"

/* TweetNaCl asks for a random source only for key generation and signing; a verifier never calls it. */
void randombytes(unsigned char *x, unsigned long long n) {
  (void)x;
  (void)n;
}

#define WL_SIGNED_MAX 320 /* longest signed prefix (largest telecommand is far below this) */

void wl_auth_init(wl_auth_t *a) { memset(a, 0, sizeof *a); }

void wl_auth_rotate(wl_auth_t *a, const uint8_t new_pub[32]) {
  memcpy(a->pubkey[1], a->pubkey[0], 32);
  a->key_valid[1] = a->key_valid[0];
  memcpy(a->pubkey[0], new_pub, 32);
  a->key_valid[0] = 1;
}

static int verify_sig(const uint8_t sig[64], const uint8_t *msg, size_t msg_len, const uint8_t pk[32]) {
  /* TweetNaCl expects sig||message and writes the message back: keep both on the stack */
  uint8_t sm[64 + WL_SIGNED_MAX];
  uint8_t out[64 + WL_SIGNED_MAX];
  unsigned long long mlen = 0;
  if (msg_len > WL_SIGNED_MAX) return -1;
  memcpy(sm, sig, 64);
  memcpy(sm + 64, msg, msg_len);
  return crypto_sign_open(out, &mlen, sm, 64 + msg_len, pk) == 0 && mlen == msg_len ? 0 : -1;
}

int wl_auth_check(wl_auth_t *a, const uint8_t *pkt, size_t len, uint32_t now_coarse) {
  const size_t min_len = 6 + WL_SEC_LEN + WL_TC_EXTRA + WL_SIG_LEN + 2;
  if (len < min_len) return WL_AUTH_BAD_LEN;
  if (wl_crc16(pkt, len - 2) != wl_g16(pkt + len - 2)) return WL_AUTH_BAD_CRC;
  if ((wl_g16(pkt) >> 13) != 0 || ((wl_g16(pkt) >> 11) & 1u) == 0 || wl_g16(pkt + 4) != len - 7) return WL_AUTH_BAD_HEADER; /* CCSDS version, secondary-header flag, length field */
  if (((wl_g16(pkt) >> 12) & 1u) == 0) return WL_AUTH_NOT_TC;
  const uint32_t counter = wl_g32(pkt + 6 + WL_SEC_LEN);
  const uint32_t valid_until = wl_g32(pkt + 6 + WL_SEC_LEN + 4);
  if (valid_until < now_coarse) return WL_AUTH_EXPIRED;
  if (counter <= a->last_counter) return WL_AUTH_REPLAY; /* cheap checks first, before the expensive signature */
  if (counter - a->last_counter > WL_AUTH_MAX_JUMP) return WL_AUTH_JUMP;
  const size_t signed_len = len - 2 - WL_SIG_LEN;
  const uint8_t *sig = pkt + signed_len;
  int have_key = 0;
  for (int i = 0; i < WL_AUTH_KEYS; i++) {
    if (!a->key_valid[i]) continue;
    have_key = 1;
    if (verify_sig(sig, pkt, signed_len, a->pubkey[i]) == 0) {
      a->last_counter = counter;
      return WL_AUTH_OK;
    }
  }
  return have_key ? WL_AUTH_BAD_SIG : WL_AUTH_NO_KEY;
}
