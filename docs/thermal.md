# Thermal design (draft v0)

Tool: `python sim/thermal.py` (lumped-node orbital model; inputs in `configs/12u_thermal.toml`; heat and masses per column come from the CAD packing).
Nodes: four columns Q1-Q4, an isolated battery vault and the propulsion-bay tank; environment: sun, Earth infrared, albedo; nadir-pointing orbit frame.
All coatings and conductances are estimates: replace them with test data (thermal balance and thermal-vacuum tests).

## Finding: the spacecraft tends to run **cold**, not hot

With every face fully emissive (radiator-like) the electronics in an eclipse orbit fell to -27 C and safe mode to -40 C. A sweep of effective face emissivity
showed that **about 0.5** keeps every case inside limits (solar cells are 0.85, so roughly 40 % of each face must be MLI or low-emissivity area). This is a
requirement on the panel and skin layout, not only a coating choice.

## Design decisions

| Item | Decision |
|---|---|
| Body faces | effective emissivity ~0.5: cells plus MLI patches (`configs/12u_thermal.toml`) |
| Telescope column (Q1) | its two side faces get a low-absorptivity, low-emissivity coating (alpha 0.2, eps 0.3) instead of cells; MLI-wrapped optical tube, low-conductance mounts (conductance x0.15); 8 W thermostatic heater (setpoint 14-17 C), used mainly in eclipse orbits |
| Battery vault | isolated (0.1 W/K), 6 W thermostatic heater with 4/9 C thresholds keeps 4-9 C (limits 0..40 C) |
| Survival heaters | 2 W thermostatic heater set in safe mode keeps electronics above -20 C |
| Propulsion bay | the tank/thruster region is the hottest spot in burn mode; it must be isolated from Q2 and Q3 and carry its own radiator |

## Results (steady orbit, last five orbits)

| Case | Electronics | Telescope column | Battery |
|---|---|---|---|
| Nominal, dawn-dusk (beta 80 deg, no eclipse) | 15-32 C | 24-25 C, swing 0.6 K | 15.5 C, heater off |
| Nominal, eclipse orbit (beta 0 deg, 35 min eclipse) | 6-15 C | 12.6-17.2 C, swing 4.5 K, heater 70 % | 9 C |
| Science burst (Jetson +10 W), dawn-dusk | 25-41 C | 30.7-31.3 C (about 1 K above the 30 C limit) | 25 C |
| Safe mode, eclipse orbit (optics heater off) | -16..-8 C | -17..-12 C (optics window not applicable) | 4-9 C |
| Burn mode, dawn-dusk | 32-55 C (Q2 next to the bay) | 36 C (no imaging during a burn) | 32 C |

The optics limit (10-30 C, swing <= 6 K) only has to hold while imaging, so the science-burst overshoot is managed by not imaging during long Jetson bursts.

## What this means for power and orbit

- The telescope heater costs up to 8 W in eclipse-heavy orbits (budgeted as 30 % duty, 2.4 W average) and the survival heaters 2 W in safe mode; safe-mode load is
  3.1 W against 10.9 W of body-cell power. Everything else is unchanged.
- A **dawn-dusk orbit is thermally far better**: no eclipse, temperature swings of about 1 K, no heater use. It is now favoured for thermal reasons as well.
- The temperature swing in the electronics columns (5-8 K per orbit in eclipse orbits) contributes to solder-joint fatigue (see `docs/longevity.md`).

## Open items

- Physics review: safe mode needs the optics heater off (8 W would exceed the 10.9 W body-cell power); `sim/thermal.py` now checks the modelled heater power against the budgeted 2.2 W, uses the analytic side view factor (0.23 instead of 0.17) and adds cold and hot environment extremes. Not yet modelled: wing panels, the cell operating point (cells that do not extract power run hotter, up to ~20 W extra on a lit face in the worst case), a tank temperature limit.

- Propulsion bay: tank and thruster reach ~100 C in burn mode in this model; real thermal isolation, radiator and the vendor's heat rejection must be designed.
- Wing-back radiators are not needed for the nominal case but remain an option for high-power burst operation.
- Internal radiation and conduction between modules (finite-element or detailed nodal model), contact resistances, cable conduction and heaters' real power.
- Transient cases: deployment, detumble, commissioning, eclipse entry with cold soak, and the 7 s Jetson start-up peak.
