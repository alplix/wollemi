# Closed-loop mission simulation (draft v0)

Tool: `python sim/mission_sim.py [days]`. The **real firmware mode manager** (`firmware/common/gk_modes.c`, compiled to a shared library and called through ctypes) is driven by an
orbit, power and fault model for 60 days, at 30 s steps, for two orbits. Power numbers come from the design budgets (`sim/budget.py`): sun-biased generation 94 W (eclipse orbit) or
125 W (dawn-dusk), tumbling 45 W; loads NOMINAL 20.4 W, SCIENCE 27.9 W, ECLIPSE 17.9 W, BURN 53.1 W, SAFE 3.1 W, SURVIVAL 0.7 W. Battery 84 Wh, charge limit 42 W.

## Scenario

- Requests: three 42-minute science campaigns per day; electric-thruster burn windows on days 20 and 35.
- Faults: day 10 Jetson dies (permanent); day 25 battery pack A fails (capacity halves); day 40 flight controller hangs for 2 hours; day 50 a 30-minute temperature excursion.

## Results

| | Eclipse orbit (beta 0) | Dawn-dusk orbit (beta 80) |
|---|---|---|
| Time in NOMINAL / ECLIPSE | 60 % / 34 % | 93 % / 0 % |
| Mode transitions per day | 28 (one eclipse entry and exit per orbit) | 0.9 |
| Minimum state of charge | 75 % | 90 % |
| Brownout | none | none |
| Thruster burn delivered | 7.7 h of 7.7 h requested | 12.0 h of 12.0 h |
| Flight controller hang (day 40) | NOMINAL -> SURVIVAL -> SAFE -> NOMINAL, recovered in ~2 h | same |
| Temperature excursion (day 50) | NOMINAL -> SAFE -> NOMINAL in ~30 min | same |
| Science time before the Jetson failure | 9 h | 15 h |

Verdict: no brownout and correct degradation and recovery in both orbits.

## Findings

- The mode ladder behaves as designed with hysteresis (safe mode entered below 20 % charge, left above 45 %), and the thruster runs only in sunlight and only with a sun-biased attitude.
- **After the Jetson failure the spacecraft never returns to SCIENCE mode**, because that mode requires heavy compute. The long-life instruments keep running in NOMINAL, but imaging campaigns stop entirely.
  Improvement to make: a **SCIENCE-LITE** mode where the Pi CM5 does compression and selection so imaging continues at reduced rate (level 1 of the ladder).
- In an eclipse orbit the mode changes every half orbit (about 28 per day); harmless but the telemetry and event log must not flood: log mode changes only when the cause is not a routine eclipse.
- Energy is plentiful: the batteries are full most of the time and much sunlight is shed, so more power-hungry instruments or a bigger heater budget fit if the volume and thermal design allow.

## Limits

- Thermal, attitude and communications are not simulated; only a temperature-fault flag exists. The power model uses budget averages, not string-level MPPT behaviour.
- One simulation per orbit with a fixed fault schedule; random faults, sensor noise and command latency are not modelled.
- The single-point mode manager is exercised, not the whole flight software; a hardware-in-the-loop run with real timing is a later step.

## Next

- Add SCIENCE-LITE to `gk_modes` with unit tests and re-run the simulation.
- Extend the simulation with the thermal model and with an eclipse-entry cold-soak case for the optics heater.
