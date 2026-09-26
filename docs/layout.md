# 12U internal layout (draft v0)

Envelope 226.3 x 226.3 x 340.5 mm = 2 x 2 x 3 cells. Ring order Q1-Q2-Q3-Q4; D1 nadir end,
D3 zenith end. Machine-readable version: `configs/12u_layout.toml`, verified by
`python sim/layout_check.py`.

| Column | Contents |
|---|---|
| **Q1** telescope column | Telescope (D1-D3, tube filling D1, D2 and the tip of D3) + hyperspectral spectrometer at the focal plane end |
| **Q2** attitude + propulsion | Wide-field camera, thermal IR, lightning detector (D1, nadir); reaction wheels (D1-D2); propulsion tank and thruster (D2-D3); dedicated star tracker (D3) |
| **Q3** compute + quiet science | Jetson, Pi, dosimeter (D1, hot, opposite the telescope); flight controller, comms, SEU, telemetry, relay, atomic clock (D2); antenna deployer, VLF, Langmuir, magnetometer and boom, GNSS, TSI radiometer (D3, zenith, far from noise) |
| **Q4** energy vault + hard science | Pack A + EPS A (D1), pack B + EPS B + particle spectrometer (D2), survival pack C + GRB + X-ray/UV (D3), each pack in its own deck with containment |
| Skin | Solar cells, retroreflector, memory plate, material plate |
| Spine | Harness and backplane |

Rules enforced automatically: batteries away from the magnetometer, wheels and telescope column;
telescope opposite the Jetson; VLF receiver in a different deck from compute; packs A, B, C in
separate decks; propellant away from batteries.

Open items: mass balance / centre of mass (propellant depletion), thermal paths per column,
radiator face assignment, cable routing through the spine, and validation of the volume
estimates (currently +-30 %).

## Balance and thermal (from `sim/balance.py`)

- Centre of mass: offset (-0.7, -0.7, +14 mm) at launch, shifts by ~7 mm as propellant is used.
  Inside typical dispenser limits (about +-20 mm x/y, +-70 mm z; verify with the chosen deployer).
- Average heat per column: Q1 0.3 W, Q2 6.0 W, Q3 5.7 W, Q4 3.0 W (total ~15 W). Q2 and Q3 need
  ~60 % of their outer skin as radiator if nothing else helps.
- Mitigation options: heat straps between columns; use the **back faces of the solar wings** as
  radiators (~0.4 m2 facing cold space, ~50 W capacity) via flexible copper straps through the
  hinges (adds mechanical risk); Jetson burst (10 W) needs thermal mass (several kg of Al or a
  phase-change material) or limited burst duration.
