# Attitude determination and control (draft v0)

Tool: `python sim/adcs.py` (first-order sizing, inertias from the CAD model); geometry checks from `mechanical/wollemi_cad.py`.

## Sizing results (700 km, deployed inertia about 0.18 / 0.34 / 0.27 kg m2)

| Item | Result |
|---|---|
| Gravity gradient | 2.5e-7 N m |
| Aerodynamic (mean / solar max) | 5.6e-8 / 2.8e-7 N m |
| Solar radiation pressure | 5.3e-7 N m |
| **Residual magnetic dipole 0.1 A m2** | **3.0e-6 N m (dominant)**: magnetometer cleanliness and dipole compensation matter |
| Slew 90 deg in 120 s | 0.15 mN m, 8.9 mN m s |
| Candidate wheels (3 x 30 mN m s, 3 mN m) | torque margin x20, momentum margin x3.4 |
| Magnetorquers 1 A m2 | up to 30 uN m, about 18 uN m average (perpendicular to B only) |
| Telescope IFOV / smear budget | 7.7 urad (5.4 m pixel at 700 km); rate error <= 2.3 mrad/s over 1 ms; jitter <= 2.3 urad |
| Rigid-body wheel jitter | negligible (0.002-0.007 urad); the real risk is structural modes and sensor noise |
| Star tracker 5 arcsec | 17 m on the ground; image registration removes it |

## The thruster line must pass through the centre of mass (design change)

With the nozzle in a column (y = +55 mm) and the centre of mass near y = -16 mm the lever arm was ~70 mm: about **70 uN m of torque at 1.1 mN**, four times
the magnetorquer average, and a wheel saturates in about 7 minutes. Resolution adopted:

1. The propulsion module became a **propulsion bay on the -X face centre line** (y = 0, mid-height; a cylinder along X), reserved as a keep-out in
   columns Q2 and Q3 (`configs/12u_geometry.toml`, `mechanical/pack.py`).
2. The nozzle is **canted** so the thrust line passes through the centre of mass: about -3.9 deg (y) and +5.8 deg (z) with the trimmed centre of mass (it was -8.6 / -2.9 deg before the ballast), thrust loss below 1 %.
3. The same cant tilts the exhaust away from wing B: with a 12 deg plume half-angle the cone no longer reaches wing B (uncanted it would).
4. Requirement: centre of mass known and controlled to +-5 mm. A **1.7 kg tungsten ballast** in the Q2 strip trims the centre of mass from y = -18.7 mm (too close to the +-20 mm dispenser limit) to y = -7.3 mm; the remaining offset is absorbed by the fixed cant; residual torque then ~5 uN m, below the magnetorquer average.
5. Continuous magnetorquer desaturation during burns, and a burn-mode attitude controller (`docs/propulsion.md`).

Deorbit or retrograde burns use a 180 degree yaw flip so the exhaust always leaves through the trailing face.

## Panels must be double-sided (power model assumption made explicit)

In a dawn-dusk orbit the sun sits on the orbit-normal (+Y or -Y) side. The wings stow on the +Y and -Y faces and unfold in opposite directions,
so with cells on one face only, one wing would face away from the sun. The power budgets (`configs/12u_science.toml`, scenarios) count both wings as
lit, which is only true with **cells on both faces of each panel** (2.1 mm total thickness required; stiffness, mass and cost are open issues).
The tumbling case is then even better (a double-sided plate averages twice the projected area).

## Open items

- Full simulation: detumble after separation, sun acquisition, nadir tracking, slews, burn mode with flexible modes.
- Wheel micro-vibration and telescope-tube structural modes (modal analysis).
- Sensor suite trade (star tracker, sun sensors, gyro, magnetometer boom effects on control) and star tracker keep-out angles vs the wings.
- Residual magnetic moment budget (0.1 A m2 is a requirement, not yet a measurement).
