# Open ground-station kit (draft v0)

Goal: anyone can receive Ginkgo's science data and telemetry cheaply. SatNOGS provides the network and
database ([SatNOGS](https://satnogs.org/)) and is primarily VHF/UHF today, with S-band named as a goal, so the
S-band part is where Ginkgo adds value. Ginkgo's high-rate data (about 136 MB per mid-latitude station per day, see
`docs/data-plan.md`) needs S-band; UHF LoRa only carries about 0.5 MB/day.

## Two station classes

| | **Listener** (UHF/LoRa) | **Science station** (S-band) |
|---|---|---|
| Purpose | Beacon, telemetry, relay messages | Full science data, imaging, CFDP |
| Frequency | 433 MHz amateur band (LoRa) | 2.4 GHz amateur S-band |
| Antenna | Omnidirectional or small Yagi | 0.9-1.2 m dish on an az/el rotator |
| Rate | ~1-5 kbps | 0.25-2 Mbps |
| Hardware | LoRa board (TinyGS-class) + small computer | LNA + filter, down-converter or wideband SDR, rotator, Pi-class computer |
| Rough cost | tens of dollars | on the order of one to a few thousand dollars (estimate, unpriced) |

## S-band link margin (`sim/link_budget.py`, 700 km, 10 degrees elevation, 2 W, 6 dBi patch)

| Dish | 250 kbps | 500 kbps | 1 Mbps | 2 Mbps |
|---|---|---|---|---|
| 0.6 m | +6.6 dB | +3.6 | +0.6 | -2.4 |
| 0.9 m | +10.1 | +7.1 | +4.1 | +1.1 |
| **1.2 m** | +12.6 | +9.6 | **+6.6** | +3.6 |
| 1.8 m | +16.2 | +13.2 | +10.1 | +7.1 |

Reading: a 0.9 m dish supports 500 kbps comfortably, 1.2 m supports the 1 Mbps design rate with margin.
The spacecraft should support **adaptive rate** (250 kbps to 2 Mbps) so smaller stations still get data.
Assumptions: 150 K system temperature, 6.5 dB required Eb/N0, 3 dB miscellaneous losses; full budget still open.

## Kit components (to design)

- Mechanical: 1.2 m offset mesh dish, az/el rotator with enough torque, printable mounts.
- RF: 2.4 GHz feed, low-noise amplifier, band-pass filter, bias tee, coax; SDR (for example an AD9363-based
  or similar wideband device) or a down-converter feeding a low-cost SDR.
- Compute: Raspberry Pi class, running the receiver, tracking, Doppler correction and upload to the open archive.
- Software: SatNOGS-compatible client plugin (decoder for the Ginkgo protocol, CFDP receiver, CCSDS frame
  decoding), open data upload, tracking from orbit elements.
- Documentation: build guide, BOM with sourcing notes, alignment and calibration procedure.
- Reference decoder in Python shared with the flight protocol description (`docs/protocol.md`, planned).

## Pass statistics and Doppler (`groundstation/predict.py`)

Synthetic 700 km sun-synchronous orbit, 10 degrees minimum elevation, 7 days: Ankara 3.9 passes/day (mean 434 s, ~28 min/day contact), Istanbul 3.7,
Singapore 2.7, Tromso 9.7 (~76 min/day). Doppler at 2.4 GHz reaches about +-54 kHz with a rate of only ~0.6 kHz/s (433 MHz: about +-10 kHz),
so tracking with an ordinary SDR is straightforward. Use real orbit elements once the spacecraft exists.

## Software already in the repository

- `groundstation/predict.py`: pass prediction, Doppler and pass statistics (needs `pip install sgp4`).
- `groundstation/decode.py`: reference decoder for hex packets and `.gpk` archive streams, built on the generated protocol module.

## Anchor station

Collision-avoidance commanding needs at least one reliable station with transmit capability (COLAV-4). The kit
therefore also needs a **transmit variant** (licensed operator) and a documented process for the operator of record.

## Open items

- Choose the RF front end and SDR with actual pricing and availability.
- Rotator design or selection for a 1.2 m dish; wind loading.
- Frequency coordination, licensing and the operator-of-record process (amateur satellite service, IARU).
- Prototype with a spare dish and verify against a known S-band source before finalising the BOM.
