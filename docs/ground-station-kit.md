# Open ground-station kit (draft v0)

Goal: anyone can receive Wollemi's science data and telemetry cheaply. SatNOGS provides the network and
database ([SatNOGS](https://satnogs.org/)) and is primarily VHF/UHF today, with S-band named as a goal, so the
S-band part is where Wollemi adds value. Wollemi's high-rate data (about 134 MB per day at the Pamukkale reference station, see
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

Reading: a 0.9 m dish supports 500 kbps comfortably, 1.2 m supports the 1 Mbps design rate with margin. (A 0.9 m dish is light enough for a SatNOGS/SATRAN-class open-hardware rotator; the 1.2 m dish that reaches the full 1 Mbps design rate needs the heavier rotator below.)
The spacecraft should support **adaptive rate** (250 kbps to 2 Mbps) so smaller stations still get data.
Assumptions: 150 K system temperature, 6.5 dB required Eb/N0, 3 dB miscellaneous losses; full budget still open.

## Kit components and rough BOM (science station, 1.2 m; unpriced hardware not yet chosen, order-of-magnitude only)

| Item | Class | Rough cost (USD) | Notes |
|---|---|---|---|
| 1.2 m offset mesh dish | Ku/C-band satellite-TV mesh dish, repurposed | 150-400 | widely available secondhand; needs a 2.4 GHz feed |
| 2.4 GHz helical or patch feed | custom or amateur-radio surplus | 50-150 | feed illumination must match the dish f/D |
| Low-noise amplifier (2.4 GHz) | amateur/Wi-Fi-band LNA | 30-100 | noise figure drives the system temperature assumed in the link budget |
| Band-pass filter + bias tee + coax/connectors | | 50-150 | keeps Wi-Fi/ISM interference out |
| Az/el rotator with controller | **SPID BIG-RAS class** (see below; open-source SatNOGS/SATRAN rotators do not hold a 1.2 m dish) | 1500-1700 | 1300 Nm torque, 318 kg load rating, hamlib-compatible |
| Wideband SDR (or down-converter + narrowband SDR) | AD9363-class (e.g. PlutoSDR/LimeSDR family) or a 2.4 GHz down-converter feeding an RTL-SDR-class device | 150-500 | adaptive-rate receiver, Doppler tracking in software |
| Compute (tracking, decode, upload) | Raspberry Pi class | 50-100 | runs `groundstation/predict.py`-derived tracking, the decoder, and upload to the archive |
| Mounts, enclosure, cabling, misc | | 100-300 | weatherproofing for an unattended station |
| **Total, science station** | | **roughly 2200 - 4500** (RF chain ~900-2900 + rotator ~1500-1700) | within `configs/12u_cost.toml` (ground segment, two sites: 6-40 k likely 15 k total) |
| Listener station (UHF/LoRa) | LoRa board + small computer | 30-80 | no dish or rotator |

### Rotator: SatNOGS/SATRAN is the wrong choice here, a heavier commercial unit is needed

The project's own preference (open, reusable, community hardware) points at the SatNOGS rotator or the lighter SATRAN kit (< 200 USD) first, but both are sized for Yagis and light parabolic-grid antennas:
SatNOGS builders report the standard rotator handling a 24 dB parabolic grid antenna without a counterweight, but **failing under the weight and wind load of a 1.2 m dish** (community reports; see
[SatNOGS Rotator v3](https://wiki.satnogs.org/SatNOGS_Rotator_v3)). A dish-class science station therefore needs a heavier-duty unit:

- **Selected reference: SPID BIG-RAS az/el rotator** -- 1300 Nm turning torque, 2712 Nm brake torque, 318 kg vertical load rating, 0.5 deg resolution, about 1250 GBP (~1550 USD) as of March 2026 ([The DX Shop](https://thedxshop.com/product/spid-big-ras-heavy-duty-azimuth-elevation-rotator/)). This is well above the BOM range for the RF chain alone, so the total science-station cost should be read as **roughly 2200-4500 USD** once the rotator is priced in, not 900-2900; `configs/12u_cost.toml`'s 6-40 k (likely 15 k) range for two complete ground sites already covers this.
- **Wind-load sanity check:** a 1.2 m dish has a frontal area of about 1.13 m^2. At a 30 m/s design gust (108 km/h), broadside-on (worst case; Cd ~1.2 for a dish-like flat disc), the wind force is about
  0.5 x 1.225 kg/m^3 x 30^2 x 1.2 x 1.13 m^2 ~ 750 N. For a plausible mount standoff of 0.15-0.3 m, that is a wind torque of roughly 110-225 N m about the elevation axis -- 6-12x below the BIG-RAS's
  1300 Nm rating, so the unit has a large margin even in strong wind; a lighter (and cheaper) SPID RAS or BIG-RAK could also be checked against the same 750 N figure once a real mount geometry exists.
- **Software integration**: the SatNOGS client talks to rotators through `hamlib`, which already supports the SPID protocol and most commercial az/el rotators, so choosing a heavier commercial unit does
  not require new client software -- only a `hamlib` rotctld configuration for the SPID protocol.
- The **listener station** (UHF/LoRa, a small Yagi) stays on the SatNOGS or SATRAN open-hardware rotator; only the S-band science station needs the commercial unit.

- Mechanical: 1.2 m offset mesh dish, az/el rotator with enough torque, printable mounts.
- RF: 2.4 GHz feed, low-noise amplifier, band-pass filter, bias tee, coax; SDR (for example an AD9363-based
  or similar wideband device) or a down-converter feeding a low-cost SDR.
- Compute: Raspberry Pi class, running the receiver, tracking, Doppler correction and upload to the open archive.
- Software: SatNOGS-compatible client plugin (decoder for the Wollemi protocol, CFDP receiver, CCSDS frame
  decoding), open data upload, tracking from orbit elements.
- Documentation: build guide, BOM with sourcing notes, alignment and calibration procedure.
- Reference decoder in Python shared with the flight protocol description (`groundstation/decode.py`, `docs/protocol.md`).

## Pass statistics and Doppler (`groundstation/predict.py`)

Synthetic 700 km dawn-dusk sun-synchronous orbit (RAAN = Sun RA - 90 deg), 10 degrees minimum elevation, 7-30 days. **Reference site: Pamukkale (37.9 N, 29.1 E), the operator's home: 3.7 passes/day, mean 447 s, ~28 min/day contact, about 1.3 high passes (> 40 deg) per day.** Others: Ankara 3.9 passes/day (mean 446 s, ~29 min/day contact), Istanbul 4.0,
Singapore 2.9, Tromso 9.7 (~76 min/day). Doppler at 2.4 GHz reaches about +-54 kHz with a rate of only ~0.6 kHz/s (433 MHz: about +-10 kHz),
so tracking with an ordinary SDR is straightforward. Use real orbit elements once the spacecraft exists.

## Software already in the repository

- `groundstation/predict.py`: pass prediction, Doppler and pass statistics (needs `pip install sgp4`).
- `groundstation/decode.py`: reference decoder for hex packets and `.wpk` archive streams, built on the generated protocol module.

## Anchor stations (COLAV-4: at least two)

- **Primary anchor:** the operator's home in Pamukkale (Denizli), which doubles as the reference for all budgets.
- **Second anchor (proposed, not yet arranged):** a station about 8-11 hours ahead in longitude gives command opportunities spread through the day rather than clustered in the same local hours as
  Pamukkale. Candidates in decreasing order of ease (existing amateur-satellite or university ground-station communities to approach first): a partner station in **East Asia or Australia/New
  Zealand** (for maximum longitude spread), or, as an easier first step while the mission is small, a second **Turkish or nearby-country** amateur radio club station (faster to arrange, smaller
  longitude spread, still removes the single-point-of-failure risk). This is a partnership to arrange, not a design decision; `mission/traceability.toml` (COLAV-4) marks it open until a real
  second site is named.
- Collision-avoidance commanding needs at least one reliable station with transmit capability (COLAV-1, COLAV-4). The kit therefore also needs a **transmit variant** (licensed operator) and a
  documented process for the operator of record; both anchors should eventually have it so a single station outage does not stop commanding.

## Frequency coordination and licensing: where to start (Turkey, reference site)

- **National society:** Turkiye Radyo Amatorleri Cemiyeti (TRAC) is Turkey's IARU member society and the entry point for amateur-satellite frequency coordination questions and for the operator's own
  amateur radio licence.
- **National regulator:** BTK (Bilgi Teknolojileri ve Iletisim Kurumu) administers spectrum and station licensing in Turkey; an amateur satellite still needs the standard IARU international
  coordination (below) plus whatever domestic filing BTK requires for a transmitting ground station and, separately, for the spacecraft's amateur-satellite service use.
- **International coordination:** the actual satellite frequency assignment is coordinated globally through the **IARU Satellite Adviser** and regional advisory panel (not a national body alone,
  since a satellite's footprint is global); the request process and forms are published at [iaru.org/reference/satellites](https://www.iaru.org/reference/satellites/). This should start as soon as
  the link budget and orbit are stable, well before any hardware is built (`mission/requirements.md`, REG-1).
- None of this has been started; it is a real open item (`REG-1`, `COLAV-1`), not a design task, and is why `docs/risks.md` (R2) rates it high.

## Open items

- RF front end and SDR are chosen at reference-design level (this document); actual purchase needs current availability and a supplier that ships to Turkey.
- Rotator selection is closed at reference-design level for the science station (SPID BIG-RAS class); the listener station keeps the SatNOGS/SATRAN open-hardware rotator. A real mount design (standoff,
  mast, guying) is still needed to replace the order-of-magnitude wind-torque check above.
- Frequency coordination, licensing and the operator-of-record process: entry points identified above (TRAC, BTK, IARU); the actual coordination has not been started.
- Prototype with a spare dish and verify against a known S-band source before finalising the BOM (`GND-01`, `mission/tests.toml`).
