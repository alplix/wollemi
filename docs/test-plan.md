# Verification and test plan (generated)

Source: `mission/tests.toml` against `mission/traceability.toml`; generated and checked by `python tools/test_plan_check.py`. Effort figures are estimates in engineer-days for one campaign.

29 planned activities, 47 requirements covered by tests, 3 waived (analysis only, with a reason); 0 uncovered. Total effort about 780 engineer-days (about 3.5 person-years), of which 315 days involve medium/high-cost external facilities.

## Approach

1. Verify by analysis first (the automatic checks of `sim/trace_check.py`), then confirm with test at the lowest level where the risk can be retired.
2. Build the integrated **FlatSat** early: it exercises the electronics, firmware, protocol and mission simulation on real hardware long before flight hardware exists.
3. A **high-altitude balloon** precursor flies the computers, cameras, LoRa/GNSS and the ground chain (`PRE-01`), retiring software and link risk cheaply.
4. Environmental tests (vibration, shock, thermal vacuum, EMC, battery safety) use the launch provider's levels; qualification level and acceptance level are decided with the provider.
5. Every severity >= 4 failure mode of the FMEA is injected on the FlatSat (`SYS-03`).

## Test list

### Component

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| CMP-01 | Battery pack cell and pack tests (capacity, DoD cycling at the LEO profile, vent and short tests in the vault) | PWR-2, PWR-3, LONG-3 | T | 40 | low |
| CMP-02 | Solar cell and double-sided panel coupon tests (I-V at temperature, thermal cycling, bending and vibration of a 2.1 mm panel) | PWR-4, PWR-5, STR-1, SYS-5 | T | 30 | medium |
| CMP-03 | Radiation screening of COTS parts: total dose (control electronics, radios, flash) and single-event/latch-up (Jetson, CM5, MCUs) | LONG-1, LONG-2, LONG-3 | T | 25 | high |

### Board

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| BRD-01 | Card template and backplane bring-up: fit check of notched cards in a 3D-printed column, continuity of every backplane net, DRC-to-fab check | ELEC-1, ELEC-2, SYS-3 | T | 15 | low |
| BRD-02 | EPS card engineering models: MPPT efficiency, cold start from a dead pack, charge control limits, OVP/UVP, eFuse trips, survival path with pack C removed | ELEC-3, PWR-3, PWR-4, PWR-1 | T | 45 | none |
| BRD-03 | Supervisor and hardware kill: SLOT_SEL/KILL_N latch-off of a card, watchdog and beacon on the survival string alone | PWR-3, LONG-1, ELEC-1 | T | 20 | none |

### Subsystem

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| SUB-01 | Telecommand authentication on the target processors: signature, replay, expiry, key rotation, timing of Ed25519 verify | COM-4 | T | 10 | none |
| SUB-02 | Packet and CFDP stack on target hardware with the ground decoder: bit-exactness, corruption, loss and resume across passes | COM-3, DATA-1 | T | 20 | none |
| SUB-03 | Mass memory unit: erasure-coding stress, device failure injection (two devices), scrubbing, power-loss safety, data volume for 100 days of raw data | DATA-1 | T | 25 | none |
| SUB-04 | ADCS bench: wheels, torquers, sensors on an air-bearing or torsion table; slew and momentum dumping; magnetic moment measurement | ADCS-1, ADCS-2 | T | 40 | medium |
| SUB-05 | Iodine thruster with the spacecraft bay: thrust and plume measurement, thermal behaviour, contamination witness plates, canted mount alignment | PROP-1, PROP-2, ADCS-2, THM-1 | T | 40 | high |
| SUB-06 | Telescope and hyperspectral optics: focus, MTF, thermal focus shift, ground sample distance on a collimator or a distant target | THM-2 | T | 35 | medium |
| SUB-07 | Wing deployment and hold-down: burn-wire release repeatability, deployment shock, hinge torque, stowed frequency of the stack | SYS-5, STR-1, PWR-5 | T | 30 | low |

### System

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| SYS-01 | FlatSat integration: all cards, computers, sensors and radios on a bench with a simulated power and orbit environment; mission simulation replayed on hardware | SYS-3, PWR-1, PWR-2, COM-3 | T | 90 | none |
| SYS-02 | Hardware-in-the-loop mission run (60 days compressed): mode manager, FDIR, command queue, OTA with real processors and timing | SIM-1, FW-1 | T | 30 | none |
| SYS-03 | Fault injection campaign from the FMEA: each severity >= 4 failure mode injected and the response verified | FMEA-1, PWR-3, LONG-2 | T | 30 | none |
| SYS-04 | Mass properties on the flight model: mass, centre of mass and moments of inertia measured against the CAD values | SYS-2, SYS-4, ADCS-2 | T | 5 | low |
| SYS-05 | Magnetic cleanliness survey: residual dipole of the flight model with the boom stowed and deployed | ADCS-2 | T | 10 | medium |
| SYS-09 | Precise orbit knowledge: GNSS receiver accuracy on a hardware simulator or balloon flight, retroreflector ranging campaign plan with a laser station | COLAV-3 | T | 20 | medium |

### Environmental

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| ENV-01 | Vibration: sine sweep for modes, random at the launch provider's levels, quasi-static; before and after signatures | STR-1, SYS-1, SYS-5 | T | 10 | medium |
| ENV-02 | Shock: separation and deployment shock levels on the flight model | STR-1 | T | 5 | medium |
| ENV-03 | Thermal vacuum and thermal cycling with heaters, eclipse profile and survival mode; correlate the thermal model | THM-1, THM-2, LONG-1, PWR-2 | T | 20 | high |
| ENV-04 | EMC and RF: emissions, susceptibility, antenna patterns and link test in an anechoic setting; frequency compliance | COM-2, REG-1 | T | 10 | medium |
| ENV-05 | Battery safety tests required by the launch provider (vent, short, overcharge protection) and outgassing/bake-out | PWR-3, SYS-1 | T | 10 | medium |

### Precursor

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| PRE-01 | High-altitude balloon flight (about 30 km): Jetson, CM5, cameras, LoRa link, GNSS, magnetometer, dosimeter and the packet/ground chain | COM-2, COM-3, LONG-2 | D | 60 | medium |

### Ground

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| GND-01 | End-to-end ground chain: station at the reference site tracks a real satellite of opportunity, decodes and uploads to the archive; unattended operation for two weeks | COM-1, COM-2, OPEN-1, OPEN-2, OPEN-7, COLAV-4 | D | 30 | none |
| GND-02 | Open relay and protocol review: fuzz and interoperability test of the public message set with an independent decoder, quota and abuse drills, verification that no downlink content is obscured | OPEN-3, OPEN-4, OPEN-5, OPEN-6 | T | 15 | none |

### Review

| ID | Activity | Covers | Method | Days | External |
|---|---|---|---|---|---|
| REV-01 | Design reviews: preliminary and critical design review, safety review with the launch provider, licensing and coordination review | SYS-1, REG-1, COLAV-1, ORB-1, OPEN-1, LONG-4, COLAV-5, COLAV-6 | I | 40 | low |
| REV-02 | Operations readiness review: procedures, contact plan, collision-avoidance drill with a conjunction message, anomaly drills | COLAV-1, COLAV-2, COM-4, SIM-1 | D | 20 | none |

## Requirement coverage

| Requirement | Planned tests | Note |
|---|---|---|
| SYS-1 | ENV-01, ENV-05, REV-01 |  |
| SYS-2 | SYS-04 |  |
| SYS-3 | BRD-01, SYS-01 |  |
| SYS-4 | SYS-04 |  |
| SYS-5 | CMP-02, SUB-07, ENV-01 |  |
| STR-1 | CMP-02, SUB-07, ENV-01, ENV-02 |  |
| PWR-1 | BRD-02, SYS-01 |  |
| PWR-2 | CMP-01, SYS-01, ENV-03 |  |
| PWR-3 | CMP-01, BRD-02, BRD-03, SYS-03, ENV-05 |  |
| PWR-4 | CMP-02, BRD-02 |  |
| PWR-5 | CMP-02, SUB-07 |  |
| THM-1 | SUB-05, ENV-03 |  |
| THM-2 | SUB-06, ENV-03 |  |
| ADCS-1 | SUB-04 |  |
| ADCS-2 | SUB-04, SUB-05, SYS-04, SYS-05 |  |
| PROP-1 | SUB-05 |  |
| PROP-2 | SUB-05 |  |
| ORB-1 | REV-01 |  |
| COM-1 | GND-01 |  |
| COM-2 | ENV-04, PRE-01, GND-01 |  |
| COM-3 | SUB-02, SYS-01, PRE-01 |  |
| COM-4 | SUB-01, REV-02 |  |
| FW-1 | SYS-02 | waived: unit tests already run automatically on every check; hardware runs are covered by SYS-02 |
| DATA-1 | SUB-02, SUB-03 |  |
| LONG-1 | CMP-03, BRD-03, ENV-03 |  |
| LONG-2 | CMP-03, SYS-03, PRE-01 |  |
| LONG-3 | CMP-01, CMP-03 |  |
| SIM-1 | SYS-02, REV-02 | waived: software simulation result; the hardware-in-the-loop test HW-01 repeats it on real timing |
| FMEA-1 | SYS-03 | waived: document quality gate; its fault-injection consequences are covered by SYS-03 and SYS-05 |
| ELEC-1 | BRD-01, BRD-03 |  |
| ELEC-2 | BRD-01 |  |
| ELEC-3 | BRD-02 |  |
| OPEN-1 | GND-01, REV-01 |  |
| COLAV-1 | REV-01, REV-02 |  |
| REG-1 | ENV-04, REV-01 |  |
| COLAV-2 | REV-02 |  |
| COLAV-3 | SYS-09 |  |
| COLAV-4 | GND-01 |  |
| COLAV-5 | REV-01 |  |
| COLAV-6 | REV-01 |  |
| LONG-4 | REV-01 |  |
| OPEN-2 | GND-01 |  |
| OPEN-3 | GND-02 |  |
| OPEN-4 | GND-02 |  |
| OPEN-5 | GND-02 |  |
| OPEN-6 | GND-02 |  |
| OPEN-7 | GND-01 |  |

## Facilities and external cost drivers

- No external facility: 335 engineer-days (FlatSat, board work, software, ground).
- Low: 130 days; medium: 230 days; high: 85 days (radiation screening, thermal vacuum, thruster tests are the cost drivers).

## Open items

- Choose facilities and quotes; align test levels with the launch provider's requirements; decide flight-model versus proto-flight approach (one flight model reduces cost, raises risk).
- Write detailed procedures per test with pass/fail criteria linked to the requirement text; keep the results in the repository next to the requirement that they verify.
