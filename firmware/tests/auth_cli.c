// SPDX-FileCopyrightText: 2026 Wollemi contributors
// SPDX-License-Identifier: Apache-2.0

/* Command-line wrapper around wl_auth_check for cross-language tests.
 * usage: auth_cli <last_counter> <now_coarse> <pubkey_hex> [<prev_pubkey_hex|-> ] <packet_hex>
 * prints the integer result code. */
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../common/wl_auth.h"

static int unhex(const char *s, uint8_t *out, int max) {
  int n = (int)strlen(s) / 2;
  if (n > max) return -1;
  for (int i = 0; i < n; i++) {
    unsigned v;
    sscanf(s + 2 * i, "%2x", &v);
    out[i] = (uint8_t)v;
  }
  return n;
}

int main(int argc, char **argv) {
  if (argc < 6) return 2;
  wl_auth_t a;
  wl_auth_init(&a);
  a.last_counter = (uint32_t)strtoul(argv[1], 0, 10);
  const uint32_t now = (uint32_t)strtoul(argv[2], 0, 10);
  uint8_t pub[32];
  if (unhex(argv[3], pub, 32) != 32) return 2;
  memcpy(a.pubkey[0], pub, 32);
  a.key_valid[0] = 1;
  if (strcmp(argv[4], "-") != 0) {
    if (unhex(argv[4], pub, 32) != 32) return 2;
    memcpy(a.pubkey[1], pub, 32);
    a.key_valid[1] = 1;
  }
  uint8_t pkt[512];
  const int n = unhex(argv[5], pkt, sizeof pkt);
  if (n < 0) return 2;
  printf("%d\n", wl_auth_check(&a, pkt, (size_t)n, now));
  return 0;
}
