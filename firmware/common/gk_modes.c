#include "gk_modes.h"
#include <string.h>

#define SOC_SAFE_ENTER 20u   /* below this: safe mode */
#define SOC_SAFE_EXIT 45u    /* hysteresis: leave safe mode above this */
#define SOC_SCIENCE_MIN 50u
#define SOC_BURN_MIN 40u
#define SOC_ECLIPSE_MIN 35u

void gk_modes_init(gk_state_t *s) {
  memset(s, 0, sizeof *s);
  s->mode = GK_MODE_LAUNCH;
  s->level = 0;
}

const char *gk_mode_name(gk_mode_t m) {
  static const char *const names[] = {"LAUNCH", "DEPLOY", "COMMISSION", "NOMINAL", "SCIENCE",
                                      "BURN",   "ECLIPSE", "SAFE",       "SURVIVAL", "SCIENCE_LITE"};
  return names[m];
}

static void outputs(gk_state_t *s, const gk_inputs_t *in) {
  /* level from health, permissions from mode and level */
  if (!in->fc_ok)
    s->level = 3;
  else if (!in->packs_ok)
    s->level = 2;
  else if (!in->heavy_compute_ok)
    s->level = 1;
  else
    s->level = 0;
  s->allow_payloads = 0;
  s->allow_heavy_compute = 0;
  s->allow_light_compute = 0;
  s->allow_thruster = 0;
  switch (s->mode) {
    case GK_MODE_NOMINAL:
    case GK_MODE_SCIENCE:
      s->allow_payloads = s->level <= 2;
      s->allow_heavy_compute = s->level == 0 && s->mode == GK_MODE_SCIENCE;
      s->allow_light_compute = in->light_compute_ok && s->mode == GK_MODE_SCIENCE;
      break;
    case GK_MODE_SCIENCE_LITE:
      s->allow_payloads = 1;
      s->allow_light_compute = 1;
      break;
    case GK_MODE_BURN:
      s->allow_thruster = 1; /* every other load is cut in burn mode */
      break;
    case GK_MODE_ECLIPSE:
      s->allow_payloads = s->level <= 1;
      break;
    case GK_MODE_COMMISSION:
      s->allow_payloads = 1;
      break;
    default:
      break; /* LAUNCH, DEPLOY, SAFE, SURVIVAL: essential loads only */
  }
}

int gk_modes_step(gk_state_t *s, const gk_inputs_t *in) {
  const gk_mode_t old = s->mode;
  gk_mode_t m = old;

  /* Overrides in strict priority order: the supervisor's view wins over everything. */
  if (!in->fc_ok) {
    m = GK_MODE_SURVIVAL;
  } else if (old == GK_MODE_SURVIVAL) {
    m = GK_MODE_SAFE; /* flight controller is back: recover through safe mode */
  } else if (old == GK_MODE_LAUNCH) {
    if (in->sep_timer_done) m = GK_MODE_DEPLOY;
  } else if (old == GK_MODE_DEPLOY) {
    if (in->deploy_done) m = GK_MODE_COMMISSION;
  } else {
    const int critical = !in->packs_ok || !in->temp_ok || in->soc_pct < SOC_SAFE_ENTER;
    if (critical) {
      m = GK_MODE_SAFE;
    } else if (old == GK_MODE_SAFE) {
      if (in->soc_pct >= SOC_SAFE_EXIT && in->packs_ok && in->temp_ok) m = GK_MODE_NOMINAL;
    } else if (old == GK_MODE_COMMISSION) {
      if (in->commissioning_ok) m = GK_MODE_NOMINAL;
    } else if (!in->sunlit) {
      if (old == GK_MODE_BURN)
        m = GK_MODE_ECLIPSE; /* the thruster runs only in sunlight */
      else if (in->soc_pct >= SOC_ECLIPSE_MIN)
        m = GK_MODE_ECLIPSE;
      else
        m = GK_MODE_SAFE;
    } else {
      /* sunlit and healthy: choose the most useful permitted mode */
      if (in->burn_requested && in->thruster_ok && in->sun_biased && in->wings_deployed && in->soc_pct >= SOC_BURN_MIN)
        m = GK_MODE_BURN;
      else if (in->science_requested && in->soc_pct >= SOC_SCIENCE_MIN && (old != GK_MODE_BURN || !in->burn_requested) &&
               (in->heavy_compute_ok || in->light_compute_ok))
        m = in->heavy_compute_ok ? GK_MODE_SCIENCE : GK_MODE_SCIENCE_LITE; /* keep imaging alive on the light computer */
      else
        m = GK_MODE_NOMINAL;
    }
  }
  s->mode = m;
  outputs(s, in);
  return m != old;
}
