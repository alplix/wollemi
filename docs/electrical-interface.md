# Card and backplane electrical interface (draft v0)

The **Wollemi card** is the electrical and mechanical unit of the platform: a 100 x 100 mm board with a
20 x 20 mm corner cut-out that clears the central spine (see `mechanical/README.md`), seated in one of the four
columns of the 12U frame. This document defines what a card sees. Tools: `sim/eps_design.py` (power numbers).

## 1. Card outline and mechanics

| Item | Value |
|---|---|
| Outline | 100.0 x 100.0 mm, corner cut-out 20 x 20 mm at the spine corner (the inner corner) |
| Thickness | 1.6 mm nominal PCB |
| Retention | edge guides on the two outer edges, 3 mm keep-out; 4 x M2.5 holes for stack-and-clamp variants; **4 mm gap** between the column wall and the card edge for the backplane strip and receptacles; **8 x 8 mm relief** at the outer corner (diagonal to the notch) clears the frame rail |
| Height classes | Class S 10 mm pitch, Class M 20 mm, Class L 40 mm, Class XL multiples; component height limit = pitch - 3.2 mm |
| Thermal | copper-core edge to the column wall (conduction); heat-generating cards specify a thermal contact area |
| Larger modules | telescope tube, tank, battery packs and other non-card items occupy defined cell volumes with the same electrical interface on a card in their cell |

## 2. Two connectors per card

The exact pin-by-pin table is generated from `electronics/card_pinout.toml` (see `electronics/pinout.md`) and is the same data that
drives the KiCad card template `electronics/kicad/wollemi_card_template.kicad_pcb` (KiCad 10, DRC clean).

**WL-P (power and control), 2 x 30 pins, 1.27 mm pitch (0.8 mm was not routable on the notched card), blind-mate board-to-board.**
Connector family to be chosen after checking current rating, mating cycles and outgassing data (candidates in the Samtec ERM8/ERF8
class and similar); the pin allocation below is independent of the vendor.

| Group | Pins | Signals | Notes |
|---|---|---|---|
| Power A | 5 | `VBAT_A` (bussed; every card protects itself) | 5 pins ~ 5 A |
| Power B | 5 | `VBAT_B` (bussed) | independent bus B |
| Ground | 16 | `GND` | interleaved between the differential pairs, return current and shielding |
| CAN-FD A | 2 | `CAN_A_H/L` | 1 Mbps arbitration, up to 5 Mbps data |
| CAN-FD B | 2 | `CAN_B_H/L` | redundant bus |
| Time | 4 | `PPS_P/N`, `SYNC_P/N` | 1 pulse-per-second and frame sync, differential |
| Slot ID | 4 | `SLOT_ID[3:0]` | hard-wired on the backplane; card node id = slot id |
| Hardware kill | 6 | `SLOT_SEL[3:0]`, `KILL_N`, `FAULT_N` (open drain, bussed) | Supervisor addresses a slot and pulls `KILL_N`: the card's own comparator latches its eFuse off, no software involved. `FAULT_N` is a wired-OR fault report |
| Housekeeping | 4 | `I2C_SCL/SDA`, `UART_TX/RX` | I2C reaches the card ID EEPROM; UART is the console/bootloader |
| Debug | 4 | `SWD_CLK/IO`, `NRST_DBG`, `VREF` | ground use and integration test |
| Reset + reserve | 8 | `RESET_N` (with `SLOT_SEL` qualification), 7 x `RSV` | left free on purpose |

**WL-D (data), optional, 2 x 15 pins, only for data-plane cards** (Jetson, CM5, mass memory unit, S-band modem).

| Group | Pins | Signals |
|---|---|---|
| Ethernet | 8 | 4 differential pairs (1000BASE-T or 1000BASE-KX class, decided with the switch chip) |
| Fast lanes | 4 | 2 differential pairs reserved (future PCIe/SerDes) |
| Ground / shield | 14 | `GND` |
| Reserve | 4 | `RSV` |

RF signals never use the backplane connectors: coax (SMP/MMCX) directly from the card to its antenna or window.

## Backplane

Each column has a passive **backplane strip** (90 x 330 mm, 6 layers) on its inner wall carrying one WL-P receptacle per slot at a 20 mm pitch (up to 15 slots plus a hub receptacle). Bussed signals
run as daisy chains between identical pins; GND and the two battery rails are planes reached through vias; `SLOT_ID[3:0]` is strapped to ground per slot. Generated from
`electronics/card_pinout.toml` by `electronics/gen_backplane.py` (KiCad, DRC checked). The data connector WL-D is cabled to a switch card, not routed on the strip.

## 3. Power rules for cards

- Input range **4.5 - 8.6 V** on `VBAT_A` and `VBAT_B` (2S LiFePO4 pack 5.0 - 7.3 V, most of the time ~6.4 V; the wide range also
  tolerates 2-cell Li-ion buses of other open platforms, 6.0 - 8.4 V).
- Card must **OR the two inputs** (ideal diode or cross-strap) unless it declares single-bus use in its descriptor.
- **Every card carries its own hardware eFuse / latching current limiter** at each input (trip at 1.5x its declared maximum, soft start, latch-off, retry policy set
  by the card). The backplane is a passive bus with no per-slot power switches, so a card fault cannot take down the bus.
- No card connects `GND` to chassis; single-point ground on the EPS (avoid ground loops that corrupt magnetometer data).
- Hardware protection (over-current, over-voltage, under-voltage) never relies on software.
- Sensitive analog/magnetic cards (magnetometer, VLF) declare a maximum allowed DC current in their neighbourhood so layout can keep
  battery and wheel currents away (see the layout rules).

## 4. Card identity and self-description

Every card carries an I2C EEPROM (identity descriptor, versioned, CRC protected): name, revision, class, max current on each rail, mass,
node id mapping, protocol version and thermal contact area. The flight controller reads it at boot to populate the power table,
thermal model and health monitoring; it also feeds the geometry BOM used by the CAD scripts.

## 5. Control-plane behaviour

- CAN-FD A and B are both active; a card listens on both and transmits on both (or uses A and fails over to B).
- CANopen-style NMT and heartbeat (node id = slot id) for discovery and supervision; CCSDS Space Packets travel inside CAN-FD
  frames for telemetry and commands (`docs/protocol.md`).
- Supervisor (MSP430) watches the CAN heartbeats and can shut down any card in hardware: it places the slot number on `SLOT_SEL[3:0]` and pulls `KILL_N`;
  the card's comparator latches its eFuse off (radiation-tolerant, no firmware). A card is re-enabled by a power-good handshake over CAN or by a reset strobe.

## 6. EPS numbers behind the interface (`sim/eps_design.py`)

- Wing panels: 20 cells (5 x 4) per panel, 10s2p strings, Vmp ~24 V, cold open-circuit voltage ~35 V (< 40 V MPPT input limit), ~24 W per
  panel, 145 W peak for the six wing panels.
- One buck MPPT channel per panel; EPS-A takes wing A, EPS-B wing B; survival pack C has its own charger on a dedicated body string.
- Battery pack: 2S2P 26650 LiFePO4, 42 Wh, ~440 g each; charge limit C/2 = 3.3 A (~21 W) per pack.
- The chargers back off when packs are full: peak power tracking is only needed when loads plus charge exceed generation.

## 7. Interoperability note (OreSat)

OreSat uses a 1 Mbps CAN bus with CANopen and a 6.0 - 8.4 V power bus on its backplane. Wollemi keeps CANopen NMT/heartbeat/SDO conventions
so open tooling can be reused, and requires a wide input voltage range on cards so they can be adapted; the **connector and pinout are
not electrically compatible** with OreSat cards and a compatibility adapter or a shared subset would need to be agreed with that
project. This is a decision item, not a promise.

## 8. Open items

- Choose the board-to-board connector family (current per pin, outgassing, vibration) and verify with datasheets.
- Decide 1000BASE-T vs 1000BASE-KX on the backplane and the switch chip.
- Define the descriptor EEPROM format and the CANopen object dictionary.
- Detailed EPS/backplane schematics and PCBs (KiCad), then a first card template and a power card.
- Shielding and EMC budget for the magnetometer and VLF receiver.
