# Wollemi mission requirements (v1, 12U science observatory)

Supersedes the 2U draft. Every requirement with an ID in the tables below is tracked in `mission/traceability.toml` (method, evidence, status) and covered by a planned test in `mission/tests.toml`;
`python tools/req_sync_check.py` keeps this document and the traceability file consistent. Status is in `docs/verification-matrix.md` (generated).

## 1. Mission statement and objectives

**Wollemi** is an open, modular, long-life 12U science observatory and reference platform: it produces multi-decade space-weather, radiation and Earth-observation data, demonstrates robust
electronics and software in orbit, and publishes the design, data and tools for anyone to reuse.

| ID | Objective |
|---|---|
| OBJ-1 | Long-record space-weather and geophysics data: magnetic field, energetic particles, solar X-ray/UV, total solar irradiance, radiation dose, plasma, VLF, gamma-ray bursts. |
| OBJ-2 | Earth observation: 5 m class imaging (telescope), hyperspectral scenes, thermal infrared, wide-field night imagery. |
| OBJ-3 | Technology and reliability science: radiation behaviour of three compute families and of flash memory types over years (open error data). |
| OBJ-4 | A reusable, verifiable open platform: cell grid, notched card, backplane, protocol, firmware core, analysis tools and documentation. |
| OBJ-5 | Open access: public data, public relay, open ground kit and archive; the spacecraft outlives its first operators through the tiered survival design. |

## 2. Figures of merit (`python sim/budget.py configs/12u_science.toml`)

| ID | Metric | Target | Note |
|---|---|---|---|
| FOM-1 | Orbit-average power per U (nominal scenario) | >= 3 W/U | replaced by the density goal "most energy in the least volume" |
| FOM-2 | Eclipse energy margin (usable battery energy / worst eclipse need) | >= 2 | replaces the old Wh/U, which rewarded carrying unused battery |
| FOM-3 | Science payload mass fraction | >= 25 % | mass spent on shielding, redundancy, propulsion and ballast is deliberate for longevity and safety |
| FOM-4 | Science share of module volume | >= 45 % | science-first allocation |

## 3. Requirements

### System and structure

| ID | Requirement |
|---|---|
| SYS-1 | 12U CubeSat envelope (226.3 x 226.3 x 340.5 mm) with rails; deployer-compatible. |
| SYS-2 | Total mass <= 24 kg (deployer limit); planned margin >= 20 % (<= 19 kg). |
| SYS-3 | All modules fit geometrically inside their assigned columns with no interference (exact boolean check). |
| SYS-4 | Centre of mass within 20 mm (x, y) and 70 mm (z) of the geometric centre at launch. |
| SYS-5 | Stowed wing stack thickness <= 6.5 mm protrusion allowance. |
| STR-1 | Fundamental frequencies of the frame, side walls and stowed wing panels >= 100 Hz; all structural margins >= 1 at the design load factor (hand analysis). |

### Power and thermal

| ID | Requirement |
|---|---|
| PWR-1 | Orbit-average power margin >= 20 % in every power scenario (nominal, tumbling, dawn-dusk, safe, burn). |
| PWR-2 | Eclipse energy covered by the usable battery capacity with margin >= 2x. |
| PWR-3 | An independent survival power path (pack C, own string and charger) keeps supervisor and beacon alive when packs A and B are lost. |
| PWR-4 | Solar string voltages stay inside the MPPT input window over the temperature range. |
| PWR-5 | Wing panels carry cells on both faces (needed for the dawn-dusk power scenarios). |
| THM-1 | Electronics stay within -20..+60 C in nominal and eclipse orbits; battery within 0..40 C. |
| THM-2 | Telescope column 10..30 C with swing <= 6 K while imaging. |

### Attitude, propulsion and orbit

| ID | Requirement |
|---|---|
| ADCS-1 | 90 degree slew in 120 s with torque and momentum margin >= 3x. |
| ADCS-2 | Thruster misalignment torque during a burn stays below the magnetorquer average torque (thrust line through the centre of mass +-5 mm). |
| PROP-1 | Total delta-v >= 500 m/s (station keeping to ~700 km, collision avoidance, controlled descent). |
| PROP-2 | Exhaust plume clear of the solar wings. |
| ORB-1 | At end of life the spacecraft can reach reentry within 25 years: passive with the drag sail, plus a propulsive descent option; total delta-v plan within the available budget. |

### Communications, data and software

| ID | Requirement |
|---|---|
| COM-1 | One S-band station at the reference site (Pamukkale) receives all daily science data with >= 2x margin. |
| COM-2 | S-band link margin >= 3 dB at 1 Mbps with a 1.2 m ground dish at 10 degrees elevation. |
| COM-3 | Packet encode/decode is bit-exact between flight (C) and ground (Python) and rejects every single-bit corruption. |
| COM-4 | Telecommands carry a valid Ed25519 signature, counter and validity window; the supervisor rejects others. |
| DATA-1 | On-board storage holds >= 100 days of raw data and tolerates any two device failures. |
| FW-1 | Mode manager, FDIR escalation, time-tagged command queue and A/B OTA with rollback behave as specified. |
| SIM-1 | Closed-loop simulation of the real mode manager over 60 days with injected faults shows no brownout and correct degradation and recovery. |

### Longevity

| ID | Requirement |
|---|---|
| LONG-1 | Survival chain (supervisor + beacon) operates from body cells without any battery (sun-only mode). |
| LONG-2 | Long-record science instruments never depend on Linux nodes for acquisition or downlink. |
| LONG-3 | Main packs still cover eclipse after 10 years in an eclipse orbit (a dawn-dusk orbit has none); safe-mode power holds for 50 years (with the modelled degradation). |

Design life: a **tiered lifetime** (`docs/longevity.md`): survival chain 50+ years, long-life science chain 30-50 years, heavy compute about 10-15 years, main batteries about 10-28 years.

### Electronics and quality

| ID | Requirement |
|---|---|
| ELEC-1 | Card template passes KiCad DRC with the spine notch, connectors and keep-outs defined. |
| ELEC-2 | Column backplane strip (15 slots + hub, bussed CAN/PPS/SYNC/SLOT_SEL/KILL/FAULT/RESET/I2C, GND and battery planes) passes DRC with zones refilled and no unconnected items. |
| ELEC-3 | EPS cards specified (A/B chains and survival chain, hardware-only protection); schematics captured. |
| FMEA-1 | FMEA covers all subsystems; every failure mode of severity >= 4 has a detection and a response. |

### Open access, safety and regulation

| ID | Requirement |
|---|---|
| OPEN-1 | All design files, data and protocol are public under open licences (hardware CERN-OHL-S-2.0, software Apache-2.0, documents CC-BY-4.0). |
| OPEN-2 | Once launched, the spacecraft is open to everyone: anyone with a low-cost station can receive telemetry and payload data. |
| OPEN-3 | Public relay service: any licensed amateur can send and fetch short messages through the store-and-forward payload. |
| OPEN-4 | All downlinked data is unencrypted and the protocol is fully documented (amateur-band rule: no obscured meaning). |
| OPEN-5 | Only spacecraft control commands are authenticated (signed, not encrypted); public relay traffic needs no key. |
| OPEN-6 | Rate limits and message quotas protect the relay from flooding; policy documented. |
| OPEN-7 | Data published continuously in an open archive (for example SatNOGS DB). |
| COLAV-1 | Operator of record registered for conjunction data messages; collision-avoidance burns validated on the ground. |
| COLAV-2 | Avoidance burns are uploaded 24-48 h ahead (propulsion, stable attitude and about 53 W available during the burn). |
| COLAV-3 | Precise orbit knowledge: dual-frequency GNSS plus laser retroreflector; GNSS-derived ephemerides shared with tracking services. |
| COLAV-4 | At least two reliable anchor ground stations guarantee command opportunities at least daily; the volunteer network supplements them. |
| COLAV-5 | Impact detection is for science and status only; small untracked debris is countered by design margin, not avoidance. |
| COLAV-6 | Passivation and end-of-life: propulsive descent or drag sail; propellant reserve kept for disposal. |
| LONG-4 | Disposal versus 50 years: the operational life ends with a disposal manoeuvre (or a documented exception) within the 25-year guideline; the 50-year tier is a platform design life. |
| REG-1 | Frequency coordination and amateur-satellite licensing completed before launch. |

Notes on the open-access items: in-orbit open access still requires a licensed operator of record and frequency coordination; the public can use the service, the transmitter licence sits with the operator.
Onboard range sensors are not a viable collision-avoidance method in LEO (closing speeds of 10-15 km/s); avoidance is done from the ground with tracking data.

## 4. Design values that instruments must meet (targets, verified by design analysis only)

| Instrument | Design value |
|---|---|
| Telescope | ~85 mm aperture, about 5 m ground sample at 700 km, 4096-pixel class detector |
| Hyperspectral | about 50 bands 400-1000 nm, shared telescope optics |
| Magnetometer | 3 axes, 10 Hz, deployable boom |
| Particle spectrometer | 16 electron and 16 proton channels, 10 s integration |
| TSI radiometer, dosimeter, X-ray/UV, GRB counts, CSAC, GNSS/TEC | continuous records through the flight controller path (`docs/data-plan.md`) |

## 5. Communications and coverage

A single station sees a LEO spacecraft for about 2 % of the time (3.7 passes/day of 7.5 min at the reference site). Strategy: an open volunteer ground network, store-and-forward messaging, a UHF beacon for
everyone, S-band for science data, and at least two anchor stations for commanding. Relay via commercial constellations is a possible later phase.

## 6. Out of scope for now

Launch procurement, manufacturing, environmental testing (planned in `docs/test-plan.md`), and any warranty or flight-readiness certification of the design (commercial use is permitted by the open licences).
