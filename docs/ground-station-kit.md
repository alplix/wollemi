# Open ground-station kit (draft v0)

Goal: anyone can receive Ginkgo's science data and telemetry cheaply. SatNOGS provides the network and
database ([SatNOGS](https://satnogs.org/)) and is primarily VHF/UHF today, with S-band named as a goal, so the
S-band part is where Ginkgo adds value. Ginkgo's high-rate data (about 134 MB per day at the Pamukkale reference station, see
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

## Kit components and rough BOM (science station, 1.2 m; unpriced hardware not yet chosen, order-of-magnitude only)

| Item | Class | Rough cost (USD) | Notes |
|---|---|---|---|
| 1.2 m offset mesh dish | Ku/C-band satellite-TV mesh dish, repurposed | 150-400 | widely available secondhand; needs a 2.4 GHz feed |
| 2.4 GHz helical or patch feed | custom or amateur-radio surplus | 50-150 | feed illumination must match the dish f/D |
| Low-noise amplifier (2.4 GHz) | amateur/Wi-Fi-band LNA | 30-100 | noise figure drives the system temperature assumed in the link budget |
| Band-pass filter + bias tee + coax/connectors | | 50-150 | keeps Wi-Fi/ISM interference out |
| Az/el rotator with controller | amateur-radio class (Yaesu/SPID-class or open-source) | 300-1200 | must handle the wind load of a 1.2 m dish; open-source rotator designs exist |
| Wideband SDR (or down-converter + narrowband SDR) | AD9363-class (e.g. PlutoSDR/LimeSDR family) or a 2.4 GHz down-converter feeding an RTL-SDR-class device | 150-500 | adaptive-rate receiver, Doppler tracking in software |
| Compute (tracking, decode, upload) | Raspberry Pi class | 50-100 | runs `groundstation/predict.py`-derived tracking, the decoder, and upload to the archive |
| Mounts, enclosure, cabling, misc | | 100-300 | weatherproofing for an unattended station |
| **Total, science station** | | **roughly 900 - 2900** | consistent with the "on the order of one to a few thousand dollars" estimate above and with `configs/12u_cost.toml` (ground segment, two sites: 6-40 k likely 15 k total) |
| Listener station (UHF/LoRa) | LoRa board + small computer | 30-80 | no dish or rotator |

- Mechanical: 1.2 m offset mesh dish, az/el rotator with enough torque, printable mounts.
- RF: 2.4 GHz feed, low-noise amplifier, band-pass filter, bias tee, coax; SDR (for example an AD9363-based
  or similar wideband device) or a down-converter feeding a low-cost SDR.
- Compute: Raspberry Pi class, running the receiver, tracking, Doppler correction and upload to the open archive.
- Software: SatNOGS-compatible client plugin (decoder for the Ginkgo protocol, CFDP receiver, CCSDS frame
  decoding), open data upload, tracking from orbit elements.
- Documentation: build guide, BOM with sourcing notes, alignment and calibration procedure.
- Reference decoder in Python shared with the flight protocol description (`groundstation/decode.py`, `docs/protocol.md`).

## Pass statistics and Doppler (`groundstation/predict.py`)

Synthetic 700 km dawn-dusk sun-synchronous orbit (RAAN = Sun RA - 90 deg), 10 degrees minimum elevation, 7-30 days. **Reference site: Pamukkale (37.9 N, 29.1 E), the operator's home: 3.7 passes/day, mean 447 s, ~28 min/day contact, about 1.3 high passes (> 40 deg) per day.** Others: Ankara 3.9 passes/day (mean 446 s, ~29 min/day contact), Istanbul 4.0,
Singapore 2.9, Tromso 9.7 (~76 min/day). Doppler at 2.4 GHz reaches about +-54 kHz with a rate of only ~0.6 kHz/s (433 MHz: about +-10 kHz),
so tracking with an ordinary SDR is straightforward. Use real orbit elements once the spacecraft exists.

## Software already in the repository

- `groundstation/predict.py`: pass prediction, Doppler and pass statistics (needs `pip install sgp4`).
- `groundstation/decode.py`: reference decoder for hex packets and `.gpk` archive streams, built on the generated protocol module.

## Anchor stations (COLAV-4: at least two)

- **Primary anchor:** the operator's home in Pamukkale (Denizli), which doubles as the reference for all budgets.
- **Second anchor (proposed, not yet arranged):** a station about 8-11 hours ahead in longitude gives command opportunities spread through the day rather than clustered in the same local hours as
  Pamukkale. Candidates in decreasing order of ease (existing amateur-satellite or university ground-station communities to approach first): a partner station in **East Asia or Australia/New
  Zealand** (for maximum longitude spread), or, as an easier first step while the mission is small, a second **Turkish or nearby-country** amateur radio club station (faster to arrange, smaller
  longitude spread, still removes the single-point-of-failure risk). This is a partnership to arrange, not a design decision; `mission/traceability.toml` (COLAV-4) marks it open until a real
  second site is named.
- Collision-avoidance commanding needs at least one reliable station with transmit capability (COLAV-1, COLAV-4). The kit therefore also needs a **transmit variant** (licensed operator) and a
  documented process for the operator of record; both anchors should eventually have it so a single station outage does not stop commanding.

## Open items

- Choose the RF front end and SDR with actual pricing and availability.
- Rotator design or selection for a 1.2 m dish; wind loading.
- Frequency coordination, licensing and the operator-of-record process (amateur satellite service, IARU).
- Prototype with a spare dish and verify against a known S-band source before finalising the BOM.
