#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include "../generated/wollemi_proto.h"

static void hex(const uint8_t *b, int n) { for (int i = 0; i < n; i++) printf("%02x", b[i]); printf("\n"); }
static int unhex(const char *s, uint8_t *out) { int n = (int)strlen(s) / 2; for (int i = 0; i < n; i++) { unsigned v; sscanf(s + 2 * i, "%2x", &v); out[i] = (uint8_t)v; } return n; }

int main(int argc, char **argv) {
  uint8_t buf[512];
  if (argc >= 2 && !strcmp(argv[1], "pack")) {
    wl_hdr_t h; memset(&h, 0, sizeof h);
    h.seq = 42; h.coarse = 0x11223344; h.fine = 0x5566; h.clock_quality = 3; h.priority = 1;
    wl_beacon_t b; memset(&b, 0, sizeof b);
    b.mode = 2; b.node_health = 0xA5; b.batt_a_mv = 7400; b.batt_b_mv = 7390; b.batt_c_mv = 3300; b.bus_a_mv = 7350;
    b.solar_ma = 1234; b.temp_body_dc = -153; b.uptime_s = 86400u * 400u; b.reset_count = 7;
    int n = wl_beacon_pack(buf, sizeof buf, &b, &h); hex(buf, n);
    wl_hdr_t t; memset(&t, 0, sizeof t);
    t.seq = 9; t.coarse = 1000; t.fine = 2; t.clock_quality = 2; t.priority = 1; t.counter = 77; t.valid_until = 5000;
    for (int i = 0; i < 64; i++) t.sig[i] = (uint8_t)i;
    wl_burn_schedule_t bs; memset(&bs, 0, sizeof bs);
    bs.start_coarse = 123456; bs.duration_s = 7200; bs.dir_x_mm = -1000; bs.dir_y_mm = 5; bs.dir_z_mm = 32767; bs.thrust_pct = 80;
    n = wl_burn_schedule_pack(buf, sizeof buf, &bs, &t); hex(buf, n);
    return 0;
  }
  if (argc >= 3 && !strcmp(argv[1], "unpack")) {
    uint8_t pkt[512]; int n = unhex(argv[2], pkt);
    wl_hdr_t h; wl_beacon_t b; memset(&h, 0, sizeof h); memset(&b, 0, sizeof b);
    int r = wl_beacon_unpack(pkt, (size_t)n, &b, &h);
    printf("%d %u %u %u %u %u %u %u %u %d %u %u %u %u\n", r, b.mode, b.node_health, b.batt_a_mv, b.batt_b_mv, b.batt_c_mv,
           b.bus_a_mv, b.solar_ma, (unsigned)b.temp_body_dc & 0xFFFF, (int)b.temp_body_dc, b.uptime_s, b.reset_count, h.seq, h.coarse);
    return 0;
  }
  return 1;
}
