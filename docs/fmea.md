# FMEA (generated)

Source: `mission/fmea.toml`; generated and checked by `python tools/fmea_check.py`. Severity S, likelihood L, detection difficulty D on 1-5; RPN = S x L x D.

42 failure modes over 10 subsystems; 19 with severity >= 4 (all have a detection and a response).

## Highest risk priority numbers

| RPN | ID | Item | Failure mode | S | L | D | Response (FDIR class) |
|---|---|---|---|---|---|---|---|
| 36 | PRP-03 | Iodine plume and corrosion | contamination of optics, cells or radiators | 3 | 3 | 4 | thruster placed away from optics and cells with canted exhaust; limit burn hours; plume shielding (`design`) |
| 36 | SWD-02 | Flight software defect | logic error in FDIR or mode manager | 4 | 3 | 3 | supervisor independent of flight software; safe mode; patch via OTA (`survival_mode`) |
| 36 | GND-02 | Loss of operator or organisation over decades | no one commands or receives | 3 | 4 | 3 | open protocol and tools, public archive, autonomy in the survival chain; documented operator hand-over (`design`) |
| 30 | COM-02 | UHF radio and antenna | antenna fails to deploy or radio fails | 5 | 2 | 3 | survival beacon designed as a separate low-power path; deployment retried with burn-wire on the survival supply (`retry`) |
| 27 | PWR-07 | Survival chain (pack C, survival string) | pack C dead or string open | 3 | 3 | 3 | supervisor keeps running from bus A/B; beacon designed to run direct from the solar string (sun-only) (`design`) |
| 24 | PWR-05 | Both main packs | both packs fail or fade below eclipse needs | 4 | 3 | 2 | sun-only mode (heavy loads only in sunlight), survival bus keeps supervisor and beacon (`sun_only`) |
| 24 | THM-04 | Multilayer insulation / coating degradation | gradual optical property change (UV, atomic oxygen, contamination) | 2 | 4 | 3 | heater and duty-cycle adjustment from the ground; wider margins (`ground_action`) |
| 24 | CMP-05 | Mass memory unit | one or two flash devices fail; controller hang | 3 | 4 | 2 | 6+2 erasure coding, adaptive stripe width; controller restart; data downlinked and released as soon as acknowledged (`restart`) |
| 24 | PRP-01 | Electric thruster | fails to start or loses thrust | 4 | 3 | 2 | abort burn, drag sail as passive disposal, planning without manoeuvres (`degrade`) |
| 24 | STR-02 | Launch damage (vibration, shock) | loosened fastener, cracked solder, panel damage | 4 | 2 | 3 | design margins (docs/structure.md), workmanship, environmental tests, staged commissioning (`design`) |
| 24 | SWD-03 | Key or signature failure | operational key lost or compromised | 4 | 2 | 3 | previous key still valid, key_rotate signed by the offline root key (`ground_action`) |
| 24 | GND-01 | Operator error | wrong command or wrong sequence uploaded | 4 | 3 | 2 | time-tagged sequences validated against power/attitude/thermal state on the ground; expiry windows; two-person rule for manoeuvres (`ground_action`) |
| 20 | PWR-04 | Battery pack A or B | cell short, open cell, overheating | 5 | 2 | 2 | hardware disconnect and fuse; vault contains the event; operate on the other pack and the survival pack (`hardware`) |
| 20 | PWR-08 | Charge control | charger fails to stop (overcharge) or charges below 0 C | 5 | 2 | 2 | hardware OVP/UVP and low-temperature charge inhibit (`hardware`) |
| 18 | THM-03 | Propulsion bay and tank | iodine tank overheats or freezes plumbing / cold spots | 3 | 3 | 2 | burn aborted, bay isolated, heaters thermostatic; mode manager leaves BURN (`degrade`) |

## All failure modes by subsystem

### ADCS

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| ADC-01 | Reaction wheel | wheel failure or bearing wear | one axis lost; slews and pointing degraded | wheel speed and current telemetry, pointing error | remaining wheels plus magnetorquers; degraded imaging; safe mode sun-pointing by torquers | `degrade` | 3 | 3 | 2 |
| ADC-02 | Magnetorquer or driver | stuck on | uncontrolled torque, magnetic disturbance to the magnetometer | torquer current telemetry, attitude drift | hardware current limit, driver disabled by supervisor, wheels take over | `kill` | 3 | 2 | 2 |
| ADC-03 | Star tracker | blinded by the Sun or Earth, or failed | no fine attitude | solution quality flags | gyro/sun-sensor propagation, coarse pointing mode, tracker exclusion angles from the wing geometry | `degrade` | 3 | 3 | 2 |
| ADC-04 | Attitude loss after separation or fault | tumbling | power falls to 28 W average with wings, 11 W on body cells; no burns or imaging | rate gyros, sun sensors | detumble with magnetorquers in safe mode; body-cell power covers the safe loads | `safe_mode` | 3 | 3 | 1 |

### Comms

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| COM-01 | S-band transmitter | power amplifier failure | no bulk downlink; UHF only (about 0.5 MB/day) | TX telemetry, ground non-reception | UHF carries priority-1 subsets; ground commands the spare or repeats | `degrade` | 3 | 3 | 2 |
| COM-02 | UHF radio and antenna | antenna fails to deploy or radio fails | loss of beacon and commanding path | no contact at expected passes | survival beacon designed as a separate low-power path; deployment retried with burn-wire on the survival supply | `retry` | 5 | 2 | 3 |
| COM-03 | Command channel | replay or forged telecommand | unauthorised spacecraft control | signature, counter and validity check (gk_auth) | command rejected and logged; key rotation available | `design` | 5 | 2 | 1 |
| COM-04 | Ground network | single station outage (weather, failure, power) | no contacts for a day or more; collision-avoidance commands delayed | planned contact log | second station, volunteer network, autonomous store-and-forward; commanding planned with 24-48 h margin | `ground_action` | 3 | 4 | 1 |

### Compute

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| CMP-01 | Flight controller | hang or single-event upset | loss of control functions | supervisor watchdog and CAN heartbeat | escalation retry, restart, power-cycle, switch to FC-B; SURVIVAL mode if all fail | `power_cycle` | 4 | 3 | 1 |
| CMP-02 | Radiation latch-up on any card | current runaway in a COTS device | card overheats, bus sag | eFuse over-current trip | eFuse latches off, retry after a delay; permanent latch-up leaves the card off | `hardware` | 3 | 4 | 1 |
| CMP-03 | Jetson Orin Nano | death by radiation or fault | no heavy processing (imaging pipeline degraded) | heartbeat and error counters | degradation level 1; SCIENCE_LITE on the CM5; science chain unaffected | `degrade` | 2 | 4 | 1 |
| CMP-04 | Pi CM5 | death | no bulk data handling or S-band engine on the Linux side | heartbeat | FC and MMU keep the long-life science chain and downlink via the S-band modem interface | `degrade` | 3 | 4 | 1 |
| CMP-05 | Mass memory unit | one or two flash devices fail; controller hang | capacity loss; risk of data loss on a third failure | scrubbing errors, device status (mmu_status) | 6+2 erasure coding, adaptive stripe width; controller restart; data downlinked and released as soon as acknowledged | `restart` | 3 | 4 | 2 |
| CMP-06 | Time base | loss of GNSS/CSAC lock or clock drift | timestamps degraded, time-tagged commands mis-timed | clock quality bits, PPS monitoring | fall back to the FC oscillator with quality flag; ground time_set command | `degrade` | 3 | 3 | 2 |
| CMP-07 | Supervisor (MSP430FR) | hang or upset | no watchdog and no beacon | its own hardware watchdog; external supervisor timer | hardware watchdog reset; FRAM state protected by checksums; stays the simplest and best-shielded device | `hardware` | 5 | 1 | 2 |

### Ground

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| GND-01 | Operator error | wrong command or wrong sequence uploaded | unintended mode, burn or data deletion | ground checks, validity windows, simulation before upload | time-tagged sequences validated against power/attitude/thermal state on the ground; expiry windows; two-person rule for manoeuvres | `ground_action` | 4 | 3 | 2 |
| GND-02 | Loss of operator or organisation over decades | no one commands or receives | open-loop spacecraft; data unrecovered | project governance review | open protocol and tools, public archive, autonomy in the survival chain; documented operator hand-over | `design` | 3 | 4 | 3 |

### Payload

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| PAY-01 | Telescope and hyperspectral optics | contamination, defocus, mechanical shift | image quality loss | calibration targets, star fields, focus telemetry | calibration campaigns, thermal control, focus adjustment from the ground | `ground_action` | 2 | 3 | 3 |
| PAY-02 | Long-life science chain sensors | individual instrument failure (magnetometer, TSI, dosimeter...) | loss of that data record | instrument health flags and data validity | other instruments continue; redundant dosimetry; ground reconfiguration | `degrade` | 2 | 3 | 2 |
| PAY-03 | Outreach LED flasher | stuck on or unintended flash during imaging | stray light, power drain, sky nuisance | LED current telemetry | hardware maximum on-time and thermal cut-off; disabled by mode manager in SCIENCE and SAFE | `hardware` | 2 | 2 | 2 |

### Power

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| PWR-01 | Solar wing string (one panel) | open circuit or short of a panel string | loss of about 1/6 of wing power; MPPT channel idles | per-channel current and voltage telemetry (hk_power), string current comparison | MPPT channel disabled, other channels continue; ground informed | `degrade` | 2 | 3 | 2 |
| PWR-02 | Wing deployment | wing fails to deploy or one panel jams | generation limited to body cells (10.9 W tumbling); imaging and burns impossible | deployment confirmation switches, generation vs sun angle | retry burn wire (independent survival supply), then safe mode on body cells; ground decides on operations without wings | `retry` | 4 | 2 | 2 |
| PWR-03 | MPPT / EPS-A card | card failure (short, no output) | wing A power lost, pack A charger lost; bus B and pack B continue | loss of EPS-A telemetry, bus A voltage, heartbeat | isolated by ideal diode; supervisor kills the slot if needed; operate on EPS-B and half the power | `switch_redundant` | 3 | 2 | 2 |
| PWR-04 | Battery pack A or B | cell short, open cell, overheating | one pack lost; risk of venting or fire in the vault | pack voltage/current/temperature, BMS flags, hardware cut-off | hardware disconnect and fuse; vault contains the event; operate on the other pack and the survival pack | `hardware` | 5 | 2 | 2 |
| PWR-05 | Both main packs | both packs fail or fade below eclipse needs | no eclipse operation; sun-only mode | state-of-charge model, eclipse voltage sag | sun-only mode (heavy loads only in sunlight), survival bus keeps supervisor and beacon | `sun_only` | 4 | 3 | 2 |
| PWR-06 | Bus short circuit or card short | short on a card input or backplane | voltage collapse on one bus | per-card eFuse trip, FAULT_N wired-OR, bus voltage monitor | the card's own eFuse latches off; supervisor kills the slot with SLOT_SEL/KILL_N if it stays faulty | `kill` | 4 | 2 | 2 |
| PWR-07 | Survival chain (pack C, survival string) | pack C dead or string open | supervisor and beacon rely on the main buses only | pack C telemetry; loss of survival-path current | supervisor keeps running from bus A/B; beacon designed to run direct from the solar string (sun-only) | `design` | 3 | 3 | 3 |
| PWR-08 | Charge control | charger fails to stop (overcharge) or charges below 0 C | cell damage, plating, vent risk | cell voltage and temperature comparators independent of software | hardware OVP/UVP and low-temperature charge inhibit | `hardware` | 5 | 2 | 2 |

### Propulsion

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| PRP-01 | Electric thruster | fails to start or loses thrust | no station keeping or collision avoidance; no controlled descent | thruster telemetry, no delta-v measured from GNSS | abort burn, drag sail as passive disposal, planning without manoeuvres | `degrade` | 4 | 3 | 2 |
| PRP-02 | Thruster stuck on / valve or heater failure | uncommanded thrust | orbit change and torque, propellant loss | acceleration from GNSS/gyros, thruster telemetry | hardware cut through the supervisor kill path and the three-inhibit chain; power removed | `kill` | 4 | 1 | 2 |
| PRP-03 | Iodine plume and corrosion | contamination of optics, cells or radiators | gradual loss of optical performance and power | image degradation, generation trend | thruster placed away from optics and cells with canted exhaust; limit burn hours; plume shielding | `design` | 3 | 3 | 4 |
| PRP-04 | Thrust line off the centre of mass | CoM shift beyond +-5 mm (ballast, propellant use) | torque during burns exceeds the magnetorquer capacity; wheel saturation | wheel momentum during burns | shorter burns with dumping; ground updates the cant/CoM model; burn aborted on saturation | `safe_mode` | 3 | 3 | 2 |

### Software

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| SWD-01 | Over-the-air update | corrupt or interrupted update | node fails to boot the new image | hash check before commit, confirm timeout | A/B slots, confirm-or-rollback (gk_ota); never overwrite the running slot | `design` | 4 | 3 | 1 |
| SWD-02 | Flight software defect | logic error in FDIR or mode manager | wrong mode or missed recovery | unit tests, closed-loop simulation, hardware-in-the-loop, telemetry review | supervisor independent of flight software; safe mode; patch via OTA | `survival_mode` | 4 | 3 | 3 |
| SWD-03 | Key or signature failure | operational key lost or compromised | cannot command, or unauthorised command risk | rejected commands, ground audit | previous key still valid, key_rotate signed by the offline root key | `ground_action` | 4 | 2 | 3 |

### Structure

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| STR-01 | Burn-wire / hold-down release | release does not occur | wing or antenna stays stowed | deployment switches | retry, second wire, independent supply; see PWR-02 and COM-02 | `retry` | 4 | 2 | 2 |
| STR-02 | Launch damage (vibration, shock) | loosened fastener, cracked solder, panel damage | any function may fail at first contact | post-launch checkout of every subsystem | design margins (docs/structure.md), workmanship, environmental tests, staged commissioning | `design` | 4 | 2 | 3 |
| STR-03 | Debris or micrometeoroid impact | penetration of tank, vault or electronics; solar panel damage | random failures up to loss of mission | impact sensor, sudden telemetry change | Whipple protection on tank and batteries, redundancy (A/B/C), collision avoidance for tracked objects | `design` | 5 | 1 | 3 |

### Thermal

| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |
|---|---|---|---|---|---|---|---|---|---|
| THM-01 | Battery heater or thermostat | stuck off or stuck on | cold battery (no charging) or overheating | vault temperature, heater current telemetry | hardware over-temperature cut-off; charge inhibit below 0 C; second heater element | `hardware` | 4 | 2 | 2 |
| THM-02 | Telescope column heater | fails off in eclipse orbits | optics cold, swing beyond 6 K; imaging degraded, possible focus shift | column temperature sensors | imaging inhibited outside the temperature window; ground reconfigures the orbit plan | `degrade` | 2 | 3 | 2 |
| THM-03 | Propulsion bay and tank | iodine tank overheats or freezes plumbing / cold spots | thruster cannot start or wrong pressure; heat into neighbours | tank and bay temperature sensors, thruster telemetry | burn aborted, bay isolated, heaters thermostatic; mode manager leaves BURN | `degrade` | 3 | 3 | 2 |
| THM-04 | Multilayer insulation / coating degradation | gradual optical property change (UV, atomic oxygen, contamination) | temperatures drift over the years | long-term temperature trend vs the model | heater and duty-cycle adjustment from the ground; wider margins | `ground_action` | 2 | 4 | 3 |

## Limits

Qualitative and estimated by the design team, not derived from part-level failure-rate data. It should be reviewed independently, extended to part level (each card and connector), and turned into a fault-injection test list (`docs/test-plan.md`).
