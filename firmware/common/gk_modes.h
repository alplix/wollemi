/* Spacecraft mode manager and degradation ladder (pure logic, host-testable). */
#ifndef GK_MODES_H
#define GK_MODES_H
#include <stdint.h>

typedef enum {
  GK_MODE_LAUNCH = 0,
  GK_MODE_DEPLOY,
  GK_MODE_COMMISSION,
  GK_MODE_NOMINAL,
  GK_MODE_SCIENCE,
  GK_MODE_BURN,
  GK_MODE_ECLIPSE,
  GK_MODE_SAFE,
  GK_MODE_SURVIVAL,
  GK_MODE_SCIENCE_LITE /* imaging with the light computer only (heavy compute lost); appended to keep earlier values stable */
} gk_mode_t;

/* degradation level: 0 full, 1 no heavy compute, 2 sun-only, 3 survival (supervisor + beacon) */
typedef struct {
  uint8_t fc_ok;             /* flight controller alive and healthy */
  uint8_t packs_ok;          /* at least one main pack usable */
  uint8_t heavy_compute_ok;  /* Jetson healthy */
  uint8_t light_compute_ok;  /* Pi CM5 healthy */
  uint8_t thruster_ok;
  uint8_t temp_ok;           /* all monitored temperatures inside limits */
  uint8_t sunlit;
  uint8_t sun_biased;        /* attitude allows wings toward the sun (needed for burns) */
  uint8_t wings_deployed;
  uint8_t sep_timer_done;    /* post-separation timer elapsed */
  uint8_t deploy_done;       /* antenna and wings confirmed (or deploy timeout) */
  uint8_t commissioning_ok;  /* checkout finished */
  uint8_t science_requested;
  uint8_t burn_requested;
  uint8_t soc_pct;           /* lowest usable pack state of charge */
  uint8_t optics_ok;         /* telescope/detector temperatures inside the imaging window; science modes are refused otherwise */
} gk_inputs_t;

typedef struct {
  gk_mode_t mode;
  uint8_t level;
  uint8_t allow_payloads;
  uint8_t allow_heavy_compute;
  uint8_t allow_light_compute;
  uint8_t allow_thruster;
  gk_mode_t resume_mode; /* early-phase mode to return to after SURVIVAL (LAUNCH/DEPLOY), else SAFE */
} gk_state_t;

void gk_modes_init(gk_state_t *s);
/* Evaluate one step; returns 1 if the mode changed. */
int gk_modes_step(gk_state_t *s, const gk_inputs_t *in);
const char *gk_mode_name(gk_mode_t m);

#endif
