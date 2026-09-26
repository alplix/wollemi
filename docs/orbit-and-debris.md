# Orbit lifetime and debris compliance (draft v0)

Tool: `python sim/orbit_life.py`. Atmosphere: two exponential tables (solar minimum and maximum, log interpolation) with an 11-year cycle; accuracy a factor 2-3.
For licensing use NRLMSISE-00 or JB2008 with a solar-flux forecast, or ESA DRAMA / NASA DAS. The spacecraft mass is 15.1 kg, Cd 2.2, tumbling projected area body 0.10 m2 plus wings 0.23 m2 (double-sided
plates average half their area), plus 0.5 m2 for a 1 m2 flat sail.

## Natural decay to 200 km (years; best and worst starting phase of the solar cycle)

| Altitude | Body only | Wings deployed | Wings + 1 m2 sail |
|---|---|---|---|
| 500 km | 3 - 8 | 2 - 6 | 1 - 3 |
| 600 km | 26 - 31 | 4 - 10 | 2 - 8 |
| 700 km | 131 - 134 | **37 - 42** | **14 - 19** |
| 800 km | > 300 | 146 - 151 | 58 - 63 |

## Drag make-up delta-v (wings deployed, averaged over the solar cycle)

| Altitude | m/s per year | 50 years |
|---|---|---|
| 500 km | 17 | 870 m/s (not possible) |
| 600 km | 3.9 | 194 m/s |
| **700 km** | **0.9** | **44 m/s** |
| 800 km | 0.3 | 15 m/s |

This replaces the earlier rough estimate of 22 m/s for 700 km (the solar-maximum years dominate; a constant mean density underestimates the drag).

## Disposal from 700 km (IADC guideline: 25 years)

- Passive with wings only: 37-42 years: **fails**.
- Passive with a 1 m2 sail: 14-19 years: **meets 25 years on this model**, but the uncertainty (factor 2-3) could push it above 25; treat the sail as the passive backup, not the plan.
- **Propulsive descent** with the electric thruster: 700 -> 600 km costs 54 m/s (~8 days of thrusting at 1.1 mN, then 2-8 years of drag with the sail); 700 -> 500 km costs 108 m/s (~17 days, then 1-3 years).
  A perigee-lowering burn to 300 km costs 110 m/s (~17 days).
- Delta-v plan at 700 km: 44 m/s station keeping x1.5 margin (66) + 108 m/s descent + 20 m/s collision avoidance = **194 m/s of about 630 m/s available** (`docs/propulsion.md`).
- 800 km and above would need propulsion for disposal (passive 58-150 years) and are not recommended without a disposal plan.

## Consequences for the design

- The drag sail is required, not optional (also as the passive backup if propulsion fails at end of life); the propulsion bay keeps propellant reserved for the descent (about 108 m/s, ~110 g of iodine at Isp 2000 s).
- 600 km is technically possible for 50 years (194 m/s) but leaves a smaller margin against collision-avoidance needs; 700 km balances lifetime and disposal.
- Collision risk with catalogued and uncatalogued debris is **not evaluated**: run ESA MASTER / NASA ORDEM for the chosen orbit and use the conjunction data messages (`mission/requirements.md`, COLAV).

## Open items

- Replace the atmosphere model with NRLMSISE-00 / JB2008 and a solar-flux forecast; include attitude-dependent area (a stable attitude changes the area by a factor of 2-4).
- Debris flux and probability of collision for a 50-year mission at 700 km; end-of-life passivation (deplete propellant, discharge batteries) and its effect on the survival chain that is meant to outlive the mission.
- Conflict to resolve: a 50-year science mission conflicts with a 25-year disposal guideline; the operational life must end with a disposal manoeuvre no later than the guideline allows, or the mission must accept a documented exception.
