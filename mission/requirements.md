# Mission requirements (draft v0)

## Figures of merit

Every design revision reports these via `sim/budget.py`.

| ID | Metric | Baseline target | Stretch |
|---|---|---|---|
| FOM-1 | Orbit-average power per U (W/U) | >= 3 | >= 4 (needs sun pointing) |
| FOM-2 | Stored energy per U (Wh/U) | >= 15 | >= 20 |
| FOM-3 | Payload mass fraction | >= 35 % | >= 40 % |
| FOM-4 | Energy per unit of work (J per measurement / MB) | tracked | minimised |
| FOM-5 | Downlink bits per pass | tracked | maximised |

## Reference mission (baseline config)

2U, science multi-payload, open ground network.

| ID | Requirement |
|---|---|
| REQ-1 | Form factor: 2U CubeSat, mass <= 2.66 kg, deployer-compatible (CDS Rev. 14 style rails). |
| REQ-2 | Payload A: SEU / bit-flip experiment (COTS MCU, SRAM, FRAM; with and without ECC). |
| REQ-3 | Payload B: 3-axis magnetometer + sun sensors. |
| REQ-4 | Payload C: temperature and power telemetry. |
| REQ-5 | Payload D: LoRa store-and-forward relay (amateur UHF band). |
| REQ-6 | Optional: low-resolution camera, GNSS receiver. |
| REQ-7 | All telemetry formats and data are public. |
| REQ-8 | Power positive over the orbit with >= 20 % margin, survive eclipse without brownout. |

## Open access (design and in orbit)

| ID | Requirement |
|---|---|
| OPEN-1 | Design, data and software are public from day one (repo). |
| OPEN-2 | Once launched, the satellite is open to everyone: anyone can receive telemetry and payload data with a low-cost station. |
| OPEN-3 | Public relay service: any licensed amateur can send and fetch short messages through the store-and-forward payload. |
| OPEN-4 | All downlinked data is unencrypted and the protocol is fully documented (amateur-band rule: no obscured meaning). |
| OPEN-5 | Only spacecraft *control* commands are authenticated (signed, not encrypted) so that open access cannot be abused to disable the satellite. Public relay traffic needs no key. |
| OPEN-6 | Rate limits and message quotas protect the relay from flooding; policy documented in `docs/`. |
| OPEN-7 | Data published continuously in an open archive (e.g. SatNOGS DB). |

Note: open access in orbit still requires a licensed operator of record and frequency
coordination; the public can use the service, but the transmitter licence sits with the operator.

## Collision avoidance and space safety

Onboard range sensors are not a viable collision-avoidance method in LEO (closing speeds of
10-15 km/s leave seconds of warning). Avoidance is done from the ground, using tracking data.

| ID | Requirement |
|---|---|
| COLAV-1 | An operator of record registered with a conjunction-assessment service (e.g. Space-Track, EU SST) receives conjunction data messages (CDM). |
| COLAV-2 | The spacecraft can execute a time-tagged avoidance manoeuvre uploaded >= 24-48 h ahead (propulsion, stable attitude and >= 20 W available during the burn). |
| COLAV-3 | Precise orbit knowledge: dual-frequency GNSS plus laser retroreflector; GNSS-derived ephemerides are shared with tracking services. |
| COLAV-4 | At least one reliable ground station guarantees command opportunities at least daily; volunteer network supplements it. |
| COLAV-5 | Impact detection (micrometeoroid sensor, wide-field camera) is for science and status only; small untracked debris is countered by design margin, not avoidance. |
| COLAV-6 | Passivation and end-of-life: deorbit or drag sail, propulsion reserve kept for disposal. |

## Communications and coverage

LEO gives a single station ~2-3 % coverage. Strategy: open volunteer ground network
(SatNOGS/TinyGS-style), store-and-forward messaging, optional polar station.
Relay via commercial constellations is a possible phase 2 item.

## Out of scope for now

Launch, licensing (frequency coordination), manufacturing and environmental testing.
