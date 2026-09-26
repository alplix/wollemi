/* GENERATED from protocol/messages.toml by protocol/gen.py. Do not edit. */
#ifndef GINKGO_PROTO_H
#define GINKGO_PROTO_H
#include <stdint.h>
#include <stddef.h>
#include <string.h>

#define GK_SEC_LEN 8
#define GK_TC_EXTRA 8
#define GK_SIG_LEN 64

#define GK_NODE_SUP 0
#define GK_NODE_FCA 1
#define GK_NODE_FCB 2
#define GK_NODE_MMU 3
#define GK_NODE_PAYL 4
#define GK_NODE_PAYH 5
#define GK_NODE_GND 6
#define GK_NODE_ALL 7

typedef struct {
  uint16_t apid; uint16_t seq; uint32_t coarse; uint16_t fine; uint8_t clock_quality;
  uint8_t priority; uint8_t version; uint32_t counter; uint32_t valid_until; uint8_t sig[GK_SIG_LEN];
} gk_hdr_t;

static inline uint16_t gk_crc16(const uint8_t *d, size_t n) {
  uint16_t crc = 0xFFFF;
  for (size_t i = 0; i < n; i++) {
    crc ^= (uint16_t)d[i] << 8;
    for (int b = 0; b < 8; b++) crc = (crc & 0x8000) ? (uint16_t)((crc << 1) ^ 0x1021) : (uint16_t)(crc << 1);
  }
  return crc;
}
static inline void gk_p16(uint8_t *p, uint16_t v) { p[0] = (uint8_t)(v >> 8); p[1] = (uint8_t)v; }
static inline void gk_p32(uint8_t *p, uint32_t v) { gk_p16(p, (uint16_t)(v >> 16)); gk_p16(p + 2, (uint16_t)v); }
static inline uint16_t gk_g16(const uint8_t *p) { return (uint16_t)((p[0] << 8) | p[1]); }
static inline uint32_t gk_g32(const uint8_t *p) { return ((uint32_t)gk_g16(p) << 16) | gk_g16(p + 2); }
static inline void gk_pf(uint8_t *p, float f) { uint32_t u; memcpy(&u, &f, 4); gk_p32(p, u); }
static inline float gk_gf(const uint8_t *p) { uint32_t u = gk_g32(p); float f; memcpy(&f, &u, 4); return f; }

/* beacon: Survival beacon: minimal state, decodable by any listener; sent by the supervisor even in sun-only mode. */
#define GK_BEACON_APID 0x001
#define GK_BEACON_LEN 36
typedef struct {
  uint8_t mode;
  uint8_t node_health;
  uint16_t batt_a_mv;
  uint16_t batt_b_mv;
  uint16_t batt_c_mv;
  uint16_t bus_a_mv;
  uint16_t solar_ma;
  int16_t temp_body_dc;
  uint32_t uptime_s;
  uint16_t reset_count;
} gk_beacon_t;
static inline int gk_beacon_pack(uint8_t *buf, size_t cap, const gk_beacon_t *m, const gk_hdr_t *h) {
  if (cap < GK_BEACON_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_BEACON_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_BEACON_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  buf[o] = (uint8_t)m->mode; o += 1;
  buf[o] = (uint8_t)m->node_health; o += 1;
  gk_p16(buf + o, (uint16_t)m->batt_a_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->batt_b_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->batt_c_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->bus_a_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->solar_ma); o += 2;
  gk_p16(buf + o, (uint16_t)m->temp_body_dc); o += 2;
  gk_p32(buf + o, (uint32_t)m->uptime_s); o += 4;
  gk_p16(buf + o, (uint16_t)m->reset_count); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_beacon_unpack(const uint8_t *buf, size_t len, gk_beacon_t *m, gk_hdr_t *h) {
  if (len != GK_BEACON_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_BEACON_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->mode = (uint8_t)buf[o]; o += 1;
  m->node_health = (uint8_t)buf[o]; o += 1;
  m->batt_a_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->batt_b_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->batt_c_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->bus_a_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->solar_ma = (uint16_t)gk_g16(buf + o); o += 2;
  m->temp_body_dc = (int16_t)gk_g16(buf + o); o += 2;
  m->uptime_s = (uint32_t)gk_g32(buf + o); o += 4;
  m->reset_count = (uint16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* hk_sup: Supervisor housekeeping. */
#define GK_HK_SUP_APID 0x002
#define GK_HK_SUP_LEN 31
typedef struct {
  uint16_t watchdog_flags;
  uint16_t lcl_trips;
  uint32_t power_state;
  uint16_t last_fdir_action;
  uint32_t cmd_counter;
  uint8_t key_id;
} gk_hk_sup_t;
static inline int gk_hk_sup_pack(uint8_t *buf, size_t cap, const gk_hk_sup_t *m, const gk_hdr_t *h) {
  if (cap < GK_HK_SUP_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_HK_SUP_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_HK_SUP_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->watchdog_flags); o += 2;
  gk_p16(buf + o, (uint16_t)m->lcl_trips); o += 2;
  gk_p32(buf + o, (uint32_t)m->power_state); o += 4;
  gk_p16(buf + o, (uint16_t)m->last_fdir_action); o += 2;
  gk_p32(buf + o, (uint32_t)m->cmd_counter); o += 4;
  buf[o] = (uint8_t)m->key_id; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_hk_sup_unpack(const uint8_t *buf, size_t len, gk_hk_sup_t *m, gk_hdr_t *h) {
  if (len != GK_HK_SUP_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_HK_SUP_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->watchdog_flags = (uint16_t)gk_g16(buf + o); o += 2;
  m->lcl_trips = (uint16_t)gk_g16(buf + o); o += 2;
  m->power_state = (uint32_t)gk_g32(buf + o); o += 4;
  m->last_fdir_action = (uint16_t)gk_g16(buf + o); o += 2;
  m->cmd_counter = (uint32_t)gk_g32(buf + o); o += 4;
  m->key_id = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* hk_fc: Flight controller housekeeping and mode manager state. */
#define GK_HK_FC_APID 0x103
#define GK_HK_FC_LEN 32
typedef struct {
  uint8_t mode;
  uint8_t level;
  uint16_t seq_running;
  uint8_t cpu_load_pct;
  uint16_t ram_free_kb;
  uint32_t cmd_accepted;
  uint32_t cmd_rejected;
  uint8_t clock_quality;
} gk_hk_fc_t;
static inline int gk_hk_fc_pack(uint8_t *buf, size_t cap, const gk_hk_fc_t *m, const gk_hdr_t *h) {
  if (cap < GK_HK_FC_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_HK_FC_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_HK_FC_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  buf[o] = (uint8_t)m->mode; o += 1;
  buf[o] = (uint8_t)m->level; o += 1;
  gk_p16(buf + o, (uint16_t)m->seq_running); o += 2;
  buf[o] = (uint8_t)m->cpu_load_pct; o += 1;
  gk_p16(buf + o, (uint16_t)m->ram_free_kb); o += 2;
  gk_p32(buf + o, (uint32_t)m->cmd_accepted); o += 4;
  gk_p32(buf + o, (uint32_t)m->cmd_rejected); o += 4;
  buf[o] = (uint8_t)m->clock_quality; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_hk_fc_unpack(const uint8_t *buf, size_t len, gk_hk_fc_t *m, gk_hdr_t *h) {
  if (len != GK_HK_FC_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_HK_FC_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->mode = (uint8_t)buf[o]; o += 1;
  m->level = (uint8_t)buf[o]; o += 1;
  m->seq_running = (uint16_t)gk_g16(buf + o); o += 2;
  m->cpu_load_pct = (uint8_t)buf[o]; o += 1;
  m->ram_free_kb = (uint16_t)gk_g16(buf + o); o += 2;
  m->cmd_accepted = (uint32_t)gk_g32(buf + o); o += 4;
  m->cmd_rejected = (uint32_t)gk_g32(buf + o); o += 4;
  m->clock_quality = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* hk_power: Power subsystem sample. */
#define GK_HK_POWER_APID 0x104
#define GK_HK_POWER_LEN 54
typedef struct {
  uint16_t pack_a_mv;
  uint16_t pack_b_mv;
  uint16_t pack_c_mv;
  int16_t pack_a_ma;
  int16_t pack_b_ma;
  int16_t pack_c_ma;
  uint8_t solar_string_ma[12];
  uint8_t soc_a_pct;
  uint8_t soc_b_pct;
  uint32_t load_mw;
  uint32_t gen_mw;
  uint32_t lcl_state;
} gk_hk_power_t;
static inline int gk_hk_power_pack(uint8_t *buf, size_t cap, const gk_hk_power_t *m, const gk_hdr_t *h) {
  if (cap < GK_HK_POWER_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_HK_POWER_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_HK_POWER_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->pack_a_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->pack_b_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->pack_c_mv); o += 2;
  gk_p16(buf + o, (uint16_t)m->pack_a_ma); o += 2;
  gk_p16(buf + o, (uint16_t)m->pack_b_ma); o += 2;
  gk_p16(buf + o, (uint16_t)m->pack_c_ma); o += 2;
  memcpy(buf + o, m->solar_string_ma, 12); o += 12;
  buf[o] = (uint8_t)m->soc_a_pct; o += 1;
  buf[o] = (uint8_t)m->soc_b_pct; o += 1;
  gk_p32(buf + o, (uint32_t)m->load_mw); o += 4;
  gk_p32(buf + o, (uint32_t)m->gen_mw); o += 4;
  gk_p32(buf + o, (uint32_t)m->lcl_state); o += 4;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_hk_power_unpack(const uint8_t *buf, size_t len, gk_hk_power_t *m, gk_hdr_t *h) {
  if (len != GK_HK_POWER_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_HK_POWER_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->pack_a_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->pack_b_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->pack_c_mv = (uint16_t)gk_g16(buf + o); o += 2;
  m->pack_a_ma = (int16_t)gk_g16(buf + o); o += 2;
  m->pack_b_ma = (int16_t)gk_g16(buf + o); o += 2;
  m->pack_c_ma = (int16_t)gk_g16(buf + o); o += 2;
  memcpy(m->solar_string_ma, buf + o, 12); o += 12;
  m->soc_a_pct = (uint8_t)buf[o]; o += 1;
  m->soc_b_pct = (uint8_t)buf[o]; o += 1;
  m->load_mw = (uint32_t)gk_g32(buf + o); o += 4;
  m->gen_mw = (uint32_t)gk_g32(buf + o); o += 4;
  m->lcl_state = (uint32_t)gk_g32(buf + o); o += 4;
  return 0;
}

/* hk_thermal: Temperatures (0.1 degC) at defined sensor points and heater state. */
#define GK_HK_THERMAL_APID 0x105
#define GK_HK_THERMAL_LEN 51
typedef struct {
  uint8_t temp_dc[32];
  uint16_t heater_state;
  uint8_t radiator_state;
} gk_hk_thermal_t;
static inline int gk_hk_thermal_pack(uint8_t *buf, size_t cap, const gk_hk_thermal_t *m, const gk_hdr_t *h) {
  if (cap < GK_HK_THERMAL_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_HK_THERMAL_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_HK_THERMAL_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  memcpy(buf + o, m->temp_dc, 32); o += 32;
  gk_p16(buf + o, (uint16_t)m->heater_state); o += 2;
  buf[o] = (uint8_t)m->radiator_state; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_hk_thermal_unpack(const uint8_t *buf, size_t len, gk_hk_thermal_t *m, gk_hdr_t *h) {
  if (len != GK_HK_THERMAL_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_HK_THERMAL_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  memcpy(m->temp_dc, buf + o, 32); o += 32;
  m->heater_state = (uint16_t)gk_g16(buf + o); o += 2;
  m->radiator_state = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* hk_adcs: Attitude solution, wheel state and pointing mode. */
#define GK_HK_ADCS_APID 0x106
#define GK_HK_ADCS_LEN 49
typedef struct {
  uint8_t quat[16];
  uint8_t rate_mdps[6];
  uint8_t wheel_rpm[8];
  uint8_t pointing_mode;
  uint16_t sun_angle_cdeg;
} gk_hk_adcs_t;
static inline int gk_hk_adcs_pack(uint8_t *buf, size_t cap, const gk_hk_adcs_t *m, const gk_hdr_t *h) {
  if (cap < GK_HK_ADCS_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_HK_ADCS_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_HK_ADCS_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  memcpy(buf + o, m->quat, 16); o += 16;
  memcpy(buf + o, m->rate_mdps, 6); o += 6;
  memcpy(buf + o, m->wheel_rpm, 8); o += 8;
  buf[o] = (uint8_t)m->pointing_mode; o += 1;
  gk_p16(buf + o, (uint16_t)m->sun_angle_cdeg); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_hk_adcs_unpack(const uint8_t *buf, size_t len, gk_hk_adcs_t *m, gk_hdr_t *h) {
  if (len != GK_HK_ADCS_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_HK_ADCS_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  memcpy(m->quat, buf + o, 16); o += 16;
  memcpy(m->rate_mdps, buf + o, 6); o += 6;
  memcpy(m->wheel_rpm, buf + o, 8); o += 8;
  m->pointing_mode = (uint8_t)buf[o]; o += 1;
  m->sun_angle_cdeg = (uint16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* sci_mag: Magnetometer sample block: 3 axes, 16 samples at 10 Hz, nT/1e-1 units. */
#define GK_SCI_MAG_APID 0x110
#define GK_SCI_MAG_LEN 117
typedef struct {
  uint16_t t0_fine;
  uint8_t n;
  uint8_t samples[96];
  int16_t temp_dc;
} gk_sci_mag_t;
static inline int gk_sci_mag_pack(uint8_t *buf, size_t cap, const gk_sci_mag_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_MAG_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_MAG_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_MAG_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->t0_fine); o += 2;
  buf[o] = (uint8_t)m->n; o += 1;
  memcpy(buf + o, m->samples, 96); o += 96;
  gk_p16(buf + o, (uint16_t)m->temp_dc); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_mag_unpack(const uint8_t *buf, size_t len, gk_sci_mag_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_MAG_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_MAG_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->t0_fine = (uint16_t)gk_g16(buf + o); o += 2;
  m->n = (uint8_t)buf[o]; o += 1;
  memcpy(m->samples, buf + o, 96); o += 96;
  m->temp_dc = (int16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* sci_tsi: Total solar irradiance radiometer: irradiance in mW/m2 and shutter/cavity state. */
#define GK_SCI_TSI_APID 0x111
#define GK_SCI_TSI_LEN 24
typedef struct {
  uint32_t irradiance_mw_m2;
  int16_t cavity_temp_dc;
  uint8_t shutter;
  uint8_t quality;
} gk_sci_tsi_t;
static inline int gk_sci_tsi_pack(uint8_t *buf, size_t cap, const gk_sci_tsi_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_TSI_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_TSI_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_TSI_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, (uint32_t)m->irradiance_mw_m2); o += 4;
  gk_p16(buf + o, (uint16_t)m->cavity_temp_dc); o += 2;
  buf[o] = (uint8_t)m->shutter; o += 1;
  buf[o] = (uint8_t)m->quality; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_tsi_unpack(const uint8_t *buf, size_t len, gk_sci_tsi_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_TSI_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_TSI_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->irradiance_mw_m2 = (uint32_t)gk_g32(buf + o); o += 4;
  m->cavity_temp_dc = (int16_t)gk_g16(buf + o); o += 2;
  m->shutter = (uint8_t)buf[o]; o += 1;
  m->quality = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* sci_dose: Radiation dosimeter counters and integrated dose. */
#define GK_SCI_DOSE_APID 0x112
#define GK_SCI_DOSE_LEN 30
typedef struct {
  uint32_t dose_urad;
  uint32_t counts_low;
  uint32_t counts_high;
  int16_t temp_dc;
} gk_sci_dose_t;
static inline int gk_sci_dose_pack(uint8_t *buf, size_t cap, const gk_sci_dose_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_DOSE_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_DOSE_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_DOSE_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, (uint32_t)m->dose_urad); o += 4;
  gk_p32(buf + o, (uint32_t)m->counts_low); o += 4;
  gk_p32(buf + o, (uint32_t)m->counts_high); o += 4;
  gk_p16(buf + o, (uint16_t)m->temp_dc); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_dose_unpack(const uint8_t *buf, size_t len, gk_sci_dose_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_DOSE_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_DOSE_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->dose_urad = (uint32_t)gk_g32(buf + o); o += 4;
  m->counts_low = (uint32_t)gk_g32(buf + o); o += 4;
  m->counts_high = (uint32_t)gk_g32(buf + o); o += 4;
  m->temp_dc = (int16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* sci_particle: Energetic particle spectrometer: 16 electron and 16 proton channels, 10 s integration. */
#define GK_SCI_PARTICLE_APID 0x113
#define GK_SCI_PARTICLE_LEN 82
typedef struct {
  uint16_t integ_ds;
  uint8_t electrons[32];
  uint8_t protons[32];
} gk_sci_particle_t;
static inline int gk_sci_particle_pack(uint8_t *buf, size_t cap, const gk_sci_particle_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_PARTICLE_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_PARTICLE_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_PARTICLE_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->integ_ds); o += 2;
  memcpy(buf + o, m->electrons, 32); o += 32;
  memcpy(buf + o, m->protons, 32); o += 32;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_particle_unpack(const uint8_t *buf, size_t len, gk_sci_particle_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_PARTICLE_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_PARTICLE_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->integ_ds = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(m->electrons, buf + o, 32); o += 32;
  memcpy(m->protons, buf + o, 32); o += 32;
  return 0;
}

/* sci_xray: Solar X-ray/UV monitor: band fluxes and flare flag. */
#define GK_SCI_XRAY_APID 0x114
#define GK_SCI_XRAY_LEN 35
typedef struct {
  uint16_t integ_ds;
  uint8_t bands[16];
  uint8_t flare_flag;
} gk_sci_xray_t;
static inline int gk_sci_xray_pack(uint8_t *buf, size_t cap, const gk_sci_xray_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_XRAY_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_XRAY_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_XRAY_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->integ_ds); o += 2;
  memcpy(buf + o, m->bands, 16); o += 16;
  buf[o] = (uint8_t)m->flare_flag; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_xray_unpack(const uint8_t *buf, size_t len, gk_sci_xray_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_XRAY_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_XRAY_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->integ_ds = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(m->bands, buf + o, 16); o += 16;
  m->flare_flag = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* sci_grb: GRB detector: binned counts (1 s) in 4 energy channels; trigger information. */
#define GK_SCI_GRB_APID 0x115
#define GK_SCI_GRB_LEN 83
typedef struct {
  uint16_t t0_fine;
  uint8_t counts[64];
  uint8_t trigger_flag;
} gk_sci_grb_t;
static inline int gk_sci_grb_pack(uint8_t *buf, size_t cap, const gk_sci_grb_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_GRB_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_GRB_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_GRB_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->t0_fine); o += 2;
  memcpy(buf + o, m->counts, 64); o += 64;
  buf[o] = (uint8_t)m->trigger_flag; o += 1;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_grb_unpack(const uint8_t *buf, size_t len, gk_sci_grb_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_GRB_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_GRB_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->t0_fine = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(m->counts, buf + o, 64); o += 64;
  m->trigger_flag = (uint8_t)buf[o]; o += 1;
  return 0;
}

/* sci_csac: Chip-scale atomic clock state and offset versus GNSS PPS. */
#define GK_SCI_CSAC_APID 0x116
#define GK_SCI_CSAC_LEN 23
typedef struct {
  int32_t offset_ns;
  uint8_t lock;
  int16_t temp_dc;
} gk_sci_csac_t;
static inline int gk_sci_csac_pack(uint8_t *buf, size_t cap, const gk_sci_csac_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_CSAC_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_CSAC_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_CSAC_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, (uint32_t)m->offset_ns); o += 4;
  buf[o] = (uint8_t)m->lock; o += 1;
  gk_p16(buf + o, (uint16_t)m->temp_dc); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_csac_unpack(const uint8_t *buf, size_t len, gk_sci_csac_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_CSAC_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_CSAC_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->offset_ns = (int32_t)gk_g32(buf + o); o += 4;
  m->lock = (uint8_t)buf[o]; o += 1;
  m->temp_dc = (int16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* sci_seu: Radiation experiments: bit-flip counters per memory type and per compute node (Jetson, CM5, MCU classes). */
#define GK_SCI_SEU_APID 0x117
#define GK_SCI_SEU_LEN 42
typedef struct {
  uint32_t sram_flips;
  uint32_t fram_flips;
  uint32_t nand_slc_errs;
  uint32_t nand_tlc_errs;
  uint32_t nand_qlc_errs;
  uint16_t jetson_err;
  uint16_t cm5_err;
  uint16_t mcu_err;
} gk_sci_seu_t;
static inline int gk_sci_seu_pack(uint8_t *buf, size_t cap, const gk_sci_seu_t *m, const gk_hdr_t *h) {
  if (cap < GK_SCI_SEU_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SCI_SEU_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SCI_SEU_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, (uint32_t)m->sram_flips); o += 4;
  gk_p32(buf + o, (uint32_t)m->fram_flips); o += 4;
  gk_p32(buf + o, (uint32_t)m->nand_slc_errs); o += 4;
  gk_p32(buf + o, (uint32_t)m->nand_tlc_errs); o += 4;
  gk_p32(buf + o, (uint32_t)m->nand_qlc_errs); o += 4;
  gk_p16(buf + o, (uint16_t)m->jetson_err); o += 2;
  gk_p16(buf + o, (uint16_t)m->cm5_err); o += 2;
  gk_p16(buf + o, (uint16_t)m->mcu_err); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_sci_seu_unpack(const uint8_t *buf, size_t len, gk_sci_seu_t *m, gk_hdr_t *h) {
  if (len != GK_SCI_SEU_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SCI_SEU_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->sram_flips = (uint32_t)gk_g32(buf + o); o += 4;
  m->fram_flips = (uint32_t)gk_g32(buf + o); o += 4;
  m->nand_slc_errs = (uint32_t)gk_g32(buf + o); o += 4;
  m->nand_tlc_errs = (uint32_t)gk_g32(buf + o); o += 4;
  m->nand_qlc_errs = (uint32_t)gk_g32(buf + o); o += 4;
  m->jetson_err = (uint16_t)gk_g16(buf + o); o += 2;
  m->cm5_err = (uint16_t)gk_g16(buf + o); o += 2;
  m->mcu_err = (uint16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* event: Event log record (FDIR action, mode change, fault); every FDIR action is logged at priority 1. */
#define GK_EVENT_APID 0x120
#define GK_EVENT_LEN 28
typedef struct {
  uint16_t event_id;
  uint8_t severity;
  uint8_t source_node;
  uint32_t arg0;
  uint32_t arg1;
} gk_event_t;
static inline int gk_event_pack(uint8_t *buf, size_t cap, const gk_event_t *m, const gk_hdr_t *h) {
  if (cap < GK_EVENT_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_EVENT_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_EVENT_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p16(buf + o, (uint16_t)m->event_id); o += 2;
  buf[o] = (uint8_t)m->severity; o += 1;
  buf[o] = (uint8_t)m->source_node; o += 1;
  gk_p32(buf + o, (uint32_t)m->arg0); o += 4;
  gk_p32(buf + o, (uint32_t)m->arg1); o += 4;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_event_unpack(const uint8_t *buf, size_t len, gk_event_t *m, gk_hdr_t *h) {
  if (len != GK_EVENT_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_EVENT_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->event_id = (uint16_t)gk_g16(buf + o); o += 2;
  m->severity = (uint8_t)buf[o]; o += 1;
  m->source_node = (uint8_t)buf[o]; o += 1;
  m->arg0 = (uint32_t)gk_g32(buf + o); o += 4;
  m->arg1 = (uint32_t)gk_g32(buf + o); o += 4;
  return 0;
}

/* mmu_status: Mass memory unit state: stripe width, devices alive, usage, scrub progress. */
#define GK_MMU_STATUS_APID 0x330
#define GK_MMU_STATUS_LEN 30
typedef struct {
  uint8_t devices_alive;
  uint8_t stripe_data;
  uint8_t stripe_parity;
  uint16_t used_gb;
  uint16_t free_gb;
  uint8_t scrub_pct;
  uint32_t corrected_errs;
  uint16_t uncorrectable;
} gk_mmu_status_t;
static inline int gk_mmu_status_pack(uint8_t *buf, size_t cap, const gk_mmu_status_t *m, const gk_hdr_t *h) {
  if (cap < GK_MMU_STATUS_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_MMU_STATUS_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_MMU_STATUS_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  buf[o] = (uint8_t)m->devices_alive; o += 1;
  buf[o] = (uint8_t)m->stripe_data; o += 1;
  buf[o] = (uint8_t)m->stripe_parity; o += 1;
  gk_p16(buf + o, (uint16_t)m->used_gb); o += 2;
  gk_p16(buf + o, (uint16_t)m->free_gb); o += 2;
  buf[o] = (uint8_t)m->scrub_pct; o += 1;
  gk_p32(buf + o, (uint32_t)m->corrected_errs); o += 4;
  gk_p16(buf + o, (uint16_t)m->uncorrectable); o += 2;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_mmu_status_unpack(const uint8_t *buf, size_t len, gk_mmu_status_t *m, gk_hdr_t *h) {
  if (len != GK_MMU_STATUS_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_MMU_STATUS_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  m->devices_alive = (uint8_t)buf[o]; o += 1;
  m->stripe_data = (uint8_t)buf[o]; o += 1;
  m->stripe_parity = (uint8_t)buf[o]; o += 1;
  m->used_gb = (uint16_t)gk_g16(buf + o); o += 2;
  m->free_gb = (uint16_t)gk_g16(buf + o); o += 2;
  m->scrub_pct = (uint8_t)buf[o]; o += 1;
  m->corrected_errs = (uint32_t)gk_g32(buf + o); o += 4;
  m->uncorrectable = (uint16_t)gk_g16(buf + o); o += 2;
  return 0;
}

/* obj_ack: Ground acknowledgment that an object arrived and verified; allows deletion of the onboard copy. */
#define GK_OBJ_ACK_APID 0x631
#define GK_OBJ_ACK_LEN 100
typedef struct {
  uint32_t object_id;
  uint8_t hash8[8];
} gk_obj_ack_t;
static inline int gk_obj_ack_pack(uint8_t *buf, size_t cap, const gk_obj_ack_t *m, const gk_hdr_t *h) {
  if (cap < GK_OBJ_ACK_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_OBJ_ACK_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_OBJ_ACK_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  gk_p32(buf + o, (uint32_t)m->object_id); o += 4;
  memcpy(buf + o, m->hash8, 8); o += 8;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_obj_ack_unpack(const uint8_t *buf, size_t len, gk_obj_ack_t *m, gk_hdr_t *h) {
  if (len != GK_OBJ_ACK_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_OBJ_ACK_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->object_id = (uint32_t)gk_g32(buf + o); o += 4;
  memcpy(m->hash8, buf + o, 8); o += 8;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* mode_set: Request a spacecraft mode (NOMINAL, SCIENCE, BURN, ECLIPSE, SAFE). */
#define GK_MODE_SET_APID 0x140
#define GK_MODE_SET_LEN 90
typedef struct {
  uint8_t mode;
  uint8_t reason;
} gk_mode_set_t;
static inline int gk_mode_set_pack(uint8_t *buf, size_t cap, const gk_mode_set_t *m, const gk_hdr_t *h) {
  if (cap < GK_MODE_SET_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_MODE_SET_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_MODE_SET_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->mode; o += 1;
  buf[o] = (uint8_t)m->reason; o += 1;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_mode_set_unpack(const uint8_t *buf, size_t len, gk_mode_set_t *m, gk_hdr_t *h) {
  if (len != GK_MODE_SET_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_MODE_SET_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->mode = (uint8_t)buf[o]; o += 1;
  m->reason = (uint8_t)buf[o]; o += 1;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* power_switch: Switch a latching current limiter on or off. */
#define GK_POWER_SWITCH_APID 0x141
#define GK_POWER_SWITCH_LEN 90
typedef struct {
  uint8_t lcl_id;
  uint8_t state;
} gk_power_switch_t;
static inline int gk_power_switch_pack(uint8_t *buf, size_t cap, const gk_power_switch_t *m, const gk_hdr_t *h) {
  if (cap < GK_POWER_SWITCH_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_POWER_SWITCH_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_POWER_SWITCH_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->lcl_id; o += 1;
  buf[o] = (uint8_t)m->state; o += 1;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_power_switch_unpack(const uint8_t *buf, size_t len, gk_power_switch_t *m, gk_hdr_t *h) {
  if (len != GK_POWER_SWITCH_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_POWER_SWITCH_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->lcl_id = (uint8_t)buf[o]; o += 1;
  m->state = (uint8_t)buf[o]; o += 1;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* time_set: Set or adjust the spacecraft time base. */
#define GK_TIME_SET_APID 0x142
#define GK_TIME_SET_LEN 95
typedef struct {
  uint32_t coarse;
  uint16_t fine;
  uint8_t mode;
} gk_time_set_t;
static inline int gk_time_set_pack(uint8_t *buf, size_t cap, const gk_time_set_t *m, const gk_hdr_t *h) {
  if (cap < GK_TIME_SET_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_TIME_SET_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_TIME_SET_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  gk_p32(buf + o, (uint32_t)m->coarse); o += 4;
  gk_p16(buf + o, (uint16_t)m->fine); o += 2;
  buf[o] = (uint8_t)m->mode; o += 1;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_time_set_unpack(const uint8_t *buf, size_t len, gk_time_set_t *m, gk_hdr_t *h) {
  if (len != GK_TIME_SET_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_TIME_SET_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->coarse = (uint32_t)gk_g32(buf + o); o += 4;
  m->fine = (uint16_t)gk_g16(buf + o); o += 2;
  m->mode = (uint8_t)buf[o]; o += 1;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* seq_load: Load a time-tagged command sequence entry (absolute time or orbit-position trigger). */
#define GK_SEQ_LOAD_APID 0x143
#define GK_SEQ_LOAD_LEN 113
typedef struct {
  uint16_t slot;
  uint8_t trigger_type;
  uint32_t trigger_value;
  uint16_t cmd_apid;
  uint8_t cmd_args[16];
} gk_seq_load_t;
static inline int gk_seq_load_pack(uint8_t *buf, size_t cap, const gk_seq_load_t *m, const gk_hdr_t *h) {
  if (cap < GK_SEQ_LOAD_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_SEQ_LOAD_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_SEQ_LOAD_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  gk_p16(buf + o, (uint16_t)m->slot); o += 2;
  buf[o] = (uint8_t)m->trigger_type; o += 1;
  gk_p32(buf + o, (uint32_t)m->trigger_value); o += 4;
  gk_p16(buf + o, (uint16_t)m->cmd_apid); o += 2;
  memcpy(buf + o, m->cmd_args, 16); o += 16;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_seq_load_unpack(const uint8_t *buf, size_t len, gk_seq_load_t *m, gk_hdr_t *h) {
  if (len != GK_SEQ_LOAD_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_SEQ_LOAD_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->slot = (uint16_t)gk_g16(buf + o); o += 2;
  m->trigger_type = (uint8_t)buf[o]; o += 1;
  m->trigger_value = (uint32_t)gk_g32(buf + o); o += 4;
  m->cmd_apid = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(m->cmd_args, buf + o, 16); o += 16;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* burn_schedule: Schedule an electric-thruster burn (validated on the ground for power, attitude and thermal state). */
#define GK_BURN_SCHEDULE_APID 0x144
#define GK_BURN_SCHEDULE_LEN 103
typedef struct {
  uint32_t start_coarse;
  uint32_t duration_s;
  int16_t dir_x_mm;
  int16_t dir_y_mm;
  int16_t dir_z_mm;
  uint8_t thrust_pct;
} gk_burn_schedule_t;
static inline int gk_burn_schedule_pack(uint8_t *buf, size_t cap, const gk_burn_schedule_t *m, const gk_hdr_t *h) {
  if (cap < GK_BURN_SCHEDULE_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_BURN_SCHEDULE_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_BURN_SCHEDULE_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  gk_p32(buf + o, (uint32_t)m->start_coarse); o += 4;
  gk_p32(buf + o, (uint32_t)m->duration_s); o += 4;
  gk_p16(buf + o, (uint16_t)m->dir_x_mm); o += 2;
  gk_p16(buf + o, (uint16_t)m->dir_y_mm); o += 2;
  gk_p16(buf + o, (uint16_t)m->dir_z_mm); o += 2;
  buf[o] = (uint8_t)m->thrust_pct; o += 1;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_burn_schedule_unpack(const uint8_t *buf, size_t len, gk_burn_schedule_t *m, gk_hdr_t *h) {
  if (len != GK_BURN_SCHEDULE_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_BURN_SCHEDULE_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->start_coarse = (uint32_t)gk_g32(buf + o); o += 4;
  m->duration_s = (uint32_t)gk_g32(buf + o); o += 4;
  m->dir_x_mm = (int16_t)gk_g16(buf + o); o += 2;
  m->dir_y_mm = (int16_t)gk_g16(buf + o); o += 2;
  m->dir_z_mm = (int16_t)gk_g16(buf + o); o += 2;
  m->thrust_pct = (uint8_t)buf[o]; o += 1;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* key_rotate: Install a new operational public key signed by the root key. */
#define GK_KEY_ROTATE_APID 0x045
#define GK_KEY_ROTATE_LEN 185
typedef struct {
  uint8_t key_id;
  uint8_t pubkey[32];
  uint8_t root_sig[64];
} gk_key_rotate_t;
static inline int gk_key_rotate_pack(uint8_t *buf, size_t cap, const gk_key_rotate_t *m, const gk_hdr_t *h) {
  if (cap < GK_KEY_ROTATE_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_KEY_ROTATE_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_KEY_ROTATE_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->key_id; o += 1;
  memcpy(buf + o, m->pubkey, 32); o += 32;
  memcpy(buf + o, m->root_sig, 64); o += 64;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_key_rotate_unpack(const uint8_t *buf, size_t len, gk_key_rotate_t *m, gk_hdr_t *h) {
  if (len != GK_KEY_ROTATE_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_KEY_ROTATE_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->key_id = (uint8_t)buf[o]; o += 1;
  memcpy(m->pubkey, buf + o, 32); o += 32;
  memcpy(m->root_sig, buf + o, 64); o += 64;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* ota_begin: Start an update: target node, image size, manifest hash. */
#define GK_OTA_BEGIN_APID 0x150
#define GK_OTA_BEGIN_LEN 126
typedef struct {
  uint8_t target_node;
  uint8_t slot;
  uint32_t size;
  uint8_t hash[32];
} gk_ota_begin_t;
static inline int gk_ota_begin_pack(uint8_t *buf, size_t cap, const gk_ota_begin_t *m, const gk_hdr_t *h) {
  if (cap < GK_OTA_BEGIN_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_OTA_BEGIN_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_OTA_BEGIN_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->target_node; o += 1;
  buf[o] = (uint8_t)m->slot; o += 1;
  gk_p32(buf + o, (uint32_t)m->size); o += 4;
  memcpy(buf + o, m->hash, 32); o += 32;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_ota_begin_unpack(const uint8_t *buf, size_t len, gk_ota_begin_t *m, gk_hdr_t *h) {
  if (len != GK_OTA_BEGIN_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_OTA_BEGIN_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->target_node = (uint8_t)buf[o]; o += 1;
  m->slot = (uint8_t)buf[o]; o += 1;
  m->size = (uint32_t)gk_g32(buf + o); o += 4;
  memcpy(m->hash, buf + o, 32); o += 32;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* ota_commit: Verify and switch to the new slot; the node must confirm within the timeout or roll back. */
#define GK_OTA_COMMIT_APID 0x151
#define GK_OTA_COMMIT_LEN 92
typedef struct {
  uint8_t target_node;
  uint8_t slot;
  uint16_t confirm_timeout_s;
} gk_ota_commit_t;
static inline int gk_ota_commit_pack(uint8_t *buf, size_t cap, const gk_ota_commit_t *m, const gk_hdr_t *h) {
  if (cap < GK_OTA_COMMIT_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_OTA_COMMIT_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_OTA_COMMIT_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->target_node; o += 1;
  buf[o] = (uint8_t)m->slot; o += 1;
  gk_p16(buf + o, (uint16_t)m->confirm_timeout_s); o += 2;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_ota_commit_unpack(const uint8_t *buf, size_t len, gk_ota_commit_t *m, gk_hdr_t *h) {
  if (len != GK_OTA_COMMIT_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_OTA_COMMIT_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->target_node = (uint8_t)buf[o]; o += 1;
  m->slot = (uint8_t)buf[o]; o += 1;
  m->confirm_timeout_s = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* ota_confirm: Confirm a successfully booted update. */
#define GK_OTA_CONFIRM_APID 0x052
#define GK_OTA_CONFIRM_LEN 90
typedef struct {
  uint8_t target_node;
  uint8_t slot;
} gk_ota_confirm_t;
static inline int gk_ota_confirm_pack(uint8_t *buf, size_t cap, const gk_ota_confirm_t *m, const gk_hdr_t *h) {
  if (cap < GK_OTA_CONFIRM_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_OTA_CONFIRM_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | (1u << 12) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_OTA_CONFIRM_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  gk_p32(buf + o, h->counter); gk_p32(buf + o + 4, h->valid_until); o += GK_TC_EXTRA;
  buf[o] = (uint8_t)m->target_node; o += 1;
  buf[o] = (uint8_t)m->slot; o += 1;
  memcpy(buf + o, h->sig, GK_SIG_LEN); o += GK_SIG_LEN;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_ota_confirm_unpack(const uint8_t *buf, size_t len, gk_ota_confirm_t *m, gk_hdr_t *h) {
  if (len != GK_OTA_CONFIRM_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_OTA_CONFIRM_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  h->counter = gk_g32(buf + o); h->valid_until = gk_g32(buf + o + 4); o += GK_TC_EXTRA;
  m->target_node = (uint8_t)buf[o]; o += 1;
  m->slot = (uint8_t)buf[o]; o += 1;
  memcpy(h->sig, buf + o, GK_SIG_LEN);
  return 0;
}

/* relay_msg: Public store-and-forward message (amateur band, unencrypted). */
#define GK_RELAY_MSG_APID 0x460
#define GK_RELAY_MSG_LEN 98
typedef struct {
  uint8_t from_call[8];
  uint8_t to_call[8];
  uint16_t msg_id;
  uint8_t text[64];
} gk_relay_msg_t;
static inline int gk_relay_msg_pack(uint8_t *buf, size_t cap, const gk_relay_msg_t *m, const gk_hdr_t *h) {
  if (cap < GK_RELAY_MSG_LEN) return -1;
  size_t o = 6; const uint16_t apid = GK_RELAY_MSG_APID;
  gk_p16(buf, (uint16_t)((1u << 11) | apid));
  gk_p16(buf + 2, (uint16_t)((3u << 14) | (h->seq & 0x3FFF)));
  gk_p16(buf + 4, (uint16_t)(GK_RELAY_MSG_LEN - 6 - 1));
  gk_p32(buf + o, h->coarse); gk_p16(buf + o + 4, h->fine);
  buf[o + 6] = (uint8_t)(((h->clock_quality & 3) << 6) | (((h->priority - 1) & 3) << 4)); buf[o + 7] = 1; o += GK_SEC_LEN;
  memcpy(buf + o, m->from_call, 8); o += 8;
  memcpy(buf + o, m->to_call, 8); o += 8;
  gk_p16(buf + o, (uint16_t)m->msg_id); o += 2;
  memcpy(buf + o, m->text, 64); o += 64;
  gk_p16(buf + o, gk_crc16(buf, o)); o += 2;
  return (int)o;
}
static inline int gk_relay_msg_unpack(const uint8_t *buf, size_t len, gk_relay_msg_t *m, gk_hdr_t *h) {
  if (len != GK_RELAY_MSG_LEN) return -1;
  if (gk_crc16(buf, len - 2) != gk_g16(buf + len - 2)) return -2;
  if ((gk_g16(buf) & 0x7FF) != GK_RELAY_MSG_APID) return -3;
  size_t o = 6; h->apid = gk_g16(buf) & 0x7FF; h->seq = gk_g16(buf + 2) & 0x3FFF;
  h->coarse = gk_g32(buf + o); h->fine = gk_g16(buf + o + 4); h->clock_quality = buf[o + 6] >> 6;
  h->priority = (uint8_t)(((buf[o + 6] >> 4) & 3) + 1); h->version = buf[o + 7]; o += GK_SEC_LEN;
  memcpy(m->from_call, buf + o, 8); o += 8;
  memcpy(m->to_call, buf + o, 8); o += 8;
  m->msg_id = (uint16_t)gk_g16(buf + o); o += 2;
  memcpy(m->text, buf + o, 64); o += 64;
  return 0;
}

#endif /* GINKGO_PROTO_H */
