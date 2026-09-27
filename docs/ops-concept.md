# Operations concept and commissioning plan (draft v0)

Companion documents: `docs/mission-simulation.md` (mode behaviour), `docs/firmware-architecture.md`, `docs/fmea.md` (anomaly responses), `docs/data-plan.md`, `mission/requirements.md`.
Tool: `python groundstation/contact_plan.py` (passes and roles for the reference station).

## 1. Phases

| Phase | Duration | Goal | Mode |
|---|---|---|---|
| Pre-launch | months | integration, functional and environmental tests, remove-before-flight, launch approval | powered off (RBF) |
| Separation and deployment | first 1-2 h | timer (no RF, no deployment until >= 30 min), antenna and wing deployment from the survival supply | LAUNCH, DEPLOY |
| LEOP | days 0-3 | first contact, beacon decode by any listener, detumble, sun acquisition, time set | COMMISSION / SAFE |
| Commissioning | days 3-30 | checkout of every subsystem, calibration, first burn, first images | COMMISSION -> NOMINAL |
| Routine science | years | long-life record plus imaging campaigns; station keeping and collision avoidance | NOMINAL, SCIENCE, SCIENCE_LITE, ECLIPSE, BURN |
| Extended life | decades | degraded operation along the tiers (`docs/longevity.md`) | SAFE / sun-only / survival |
| End of life | months | disposal manoeuvre, passivation | BURN then survival beacon |

## 2. Ground segment and contact plan

- Reference station: Pamukkale (37.9 N, 29.1 E): about 3.7 passes/day of ~7.5 min. In the dawn-dusk orbit the passes fall in **two clusters per day**: around 05-08 h local (dawn side) and around 18-20 h local (dusk side)
  (a dawn-dusk orbit crosses every latitude at about 06:00 and 18:00 local time). **The station must run unattended**: scheduled tracking, automatic decode and upload of the received data to the open archive, alarms on missed passes.
- Pass roles each day: first pass = command upload and time synchronisation; highest-elevation pass = bulk S-band downlink; low passes = UHF housekeeping. About 23 min/day of usable S-band contact
  (`groundstation/contact_plan.py`), enough for the ~44 MB/day of science data plus imaging (`docs/data-plan.md`).
- Redundancy: a second station (or the volunteer network) is needed for commanding continuity; a single outage removes a day of contacts (FMEA COM-04).
- Commanding: all commands are time-tagged sequences loaded 24-48 h ahead (COLAV-2), validated on the ground against the power, attitude and thermal state (`wl_cmdq`, `wl_auth`), signed with the operational key.

## 3. Launch and early operations (LEOP)

1. Separation detected; timer of 30 minutes (no RF, no deployments); the survival supply deploys the UHF antenna, then the wings; the supervisor confirms with the deployment switches.
2. First beacon (`beacon` packet, decodable by anyone) at the first pass; contact confirmed by the operator or by volunteer stations.
3. Detumble with magnetorquers, sun acquisition; verify generation against the model (>= 28 W tumbling, ~58 W sun-biased); battery state.
4. Time set (`time_set`), key check (a signed no-op telecommand), housekeeping stream review (`hk_power`, `hk_thermal`, `hk_adcs`).
5. Go/no-go for commissioning: power positive, thermal inside limits, attitude controlled, both CAN buses healthy.

## 4. Commissioning checklist (pass criteria link to requirements)

| Step | Check | Pass criterion | Requirement |
|---|---|---|---|
| 1 | Power: pack A/B/C voltages, charge and discharge, string currents | generation within 20 % of the model; all packs balanced | PWR-1, PWR-2 |
| 2 | Thermal: all columns and battery inside limits over two orbits | electronics -20..60 C, battery 0..40 C; heaters cycle as predicted | THM-1, THM-2 |
| 3 | Comms: UHF and S-band links, Doppler tracking, rate adaptation | link margin >= 3 dB at 1 Mbps with a 1.2 m dish | COM-2 |
| 4 | ADCS: wheels, torquers, star tracker, slew and nadir tracking | pointing error within budget, slew 90 deg in 120 s | ADCS-1 |
| 5 | Compute: FC-A/FC-B failover, Jetson and CM5 boot, MMU scrub | heartbeat monitoring, redundancy switching and storage self-test OK | FMEA CMP rows |
| 6 | Time and navigation: GNSS lock, CSAC discipline | time quality bits at maximum | CMP-06 |
| 7 | Payload checkout: magnetometer boom, TSI, dosimeter, particle, X-ray, VLF, GRB, SEU experiments | each instrument health and baseline data valid | FMEA PAY rows |
| 8 | Imaging: dark frames, star fields, first Earth images (telescope, wide-field, thermal IR, hyperspectral) | focus and calibration within spec; data reaches the ground | THM-2, PAY-01 |
| 9 | Propulsion: heater check, low-power test burn, thrust and centre-of-mass torque | measured thrust and wheel momentum consistent with the canted-nozzle model | ADCS-2, PROP-1, PROP-2 |
| 10 | Open access: LoRa relay and public data path | a volunteer station receives and decodes | OPEN-1 to OPEN-7 |

## 5. Routine operations

- **Daily**: ingest the archive, review health, plan the next 48 h of sequences; imaging campaigns (three per day when heavy or light compute is available); science data priority as in `docs/data-plan.md`.
- **Weekly**: check the FDIR event log, scrubbing statistics (`mmu_status`), battery and panel trends, temperatures vs the model; update the atmosphere and orbit forecast.
- **Station keeping**: about 0.8 m/s per year at 700 km on average (`docs/orbit-and-debris.md`), roughly 4 h of thrusting per 1 m/s at 1.1 mN; burn mode only in sunlight with a sun-biased attitude.
- **Collision avoidance**: receive a conjunction data message, assess probability, plan a burn (0.1-0.5 m/s, 1-2.5 h), validate, upload 24-48 h ahead, verify afterwards with GNSS (COLAV-1 to COLAV-4).
- **Updates**: OTA sequence PAY-H, PAY-L, MMU, FC-B, then FC-A (`docs/firmware-architecture.md`); every update is signed, staged, verified and confirmed or rolled back.
- **Data policy**: all data published in the open archive with metadata; nothing encrypted; public relay quotas.

## 6. Anomaly response (summary; details in `docs/fmea.md`)

| Symptom | First response | Follow-up |
|---|---|---|
| No contact at a planned pass | check the station, retry the next pass; second station | after 24 h assume UHF/antenna or attitude problem, use the volunteer network |
| Safe mode entered | read the event log (`event`), confirm the power or thermal cause | recover through NOMINAL after fixing the cause; hysteresis prevents chatter |
| Survival mode | only the beacon is heard | diagnose from beacon data; recovery goes SURVIVAL -> SAFE -> NOMINAL |
| Heavy compute lost | SCIENCE_LITE keeps imaging on the CM5 | reboot or leave off; long-life science unaffected |
| Battery degradation | switch to sun-only operation for heavy loads | eclipse operations reduced; a dawn-dusk orbit avoids the problem |
| Thruster fault | abort burn; log; retry once at low power | plan without manoeuvres; the drag sail is the passive fallback |
| Suspected command compromise | rotate the key with a signed `key_rotate` (root key) | audit log, keep the previous key valid for a fixed period |

## 7. End of life

- Plan the disposal manoeuvre while at least 200 m/s of delta-v remains: propulsive descent to 500-600 km (54-108 m/s, 8-17 days of thrusting), then drag with the sail (`docs/orbit-and-debris.md`).
- Passivation: deplete or vent the propellant heaters and discharge the main batteries. The survival chain that could outlive the mission conflicts with the disposal guideline and must be handled deliberately
  (either accept a documented exception or end it during passivation).
- Hand over the archive, tools and keys according to the governance plan; publish the final data set.

## 8. Staffing and tools (a one-person project needs automation)

- Automated pass scheduling and recording, alarms, an automatic archive uploader, and a web status page.
- Dry runs: mission simulation (`sim/mission_sim.py`), digital twin from the same configuration, replay of recorded telemetry.
- A written on-call and hand-over procedure; two-person rule for manoeuvres and key operations (FMEA GND-01).

## 9. Open items

- A real orbit (launch provider) replaces the synthetic one; regenerate the contact plan; check eclipse seasons for the chosen local time of the node.
- Decide the second station and the operator organisation (licensing).
- Detailed procedures (one page per step), operator training, mission control software selection.
