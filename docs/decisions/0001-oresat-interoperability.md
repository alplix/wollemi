# Decision 0001: interoperability with OreSat conventions

Status: accepted (draft v0). Date: 2026-09-27.

## Context

OreSat is the closest open-source precedent (`docs/prior-art.md`). Verified from its public documentation: card/backplane
architecture, 1 Mbps CAN bus, CANopen with the OreSat Linux App Framework (OLAF), object dictionaries defined in YAML,
heartbeat with COB-ID 0x700 + node id, the C3 computer at node id 0x01 and other nodes at multiples of 0x04, file transfer over CAN,
and a 6.0 - 8.4 V two-cell Li-ion power bus. See the [OLAF documentation](https://oresat-olaf.readthedocs.io/en/stable/api/node.html),
the [CANopen primer](https://oresat-software.readthedocs.io/en/latest/primers/canopen.html) and the
[OreSat repositories](https://github.com/oresat).

## Options

| | Description | Effort | Value |
|---|---|---|---|
| A | Full compatibility: OreSat connector, pinout, voltages, protocols | high; forces dual power buses, PPS and 12U cell geometry into a 1U-3U design | reuse of every OreSat card |
| **B** | **Partial: reuse OreSat's CANopen conventions and tools; tolerate their voltage range; own connector** | low | shared tooling, easier adapters, honest credit |
| C | Independent design | none | no ecosystem |

## Decision

**Option B.**

1. **Control plane:** CAN-FD A/B carries CANopen NMT, heartbeat and SDO for discovery, supervision and configuration, following
   OreSat conventions (heartbeat COB-ID 0x700 + node id; object dictionaries described in YAML so tools such as OLAF and
   canopen-monitor can be reused where possible). CCSDS Space Packets (`docs/protocol.md`) ride inside CAN-FD frames for telemetry
   and commands.
2. **Node ids:** FC-A 0x01, FC-B 0x02, supervisor 0x03, cards at multiples of 0x04 (slot id x 4) so the numbering stays compatible
   with OreSat's scheme.
3. **Power input range:** cards accept 4.5 - 8.6 V (`docs/electrical-interface.md`), which covers Ginkgo's LiFePO4 bus (5.0 - 7.3 V) and
   the upper part of OreSat's Li-ion bus; a card meant for both declares it in its descriptor.
4. **Connector and mechanics:** Ginkgo's own (GK-P/GK-D, notched 100 x 100 card). No electrical or mechanical plug compatibility is promised;
   an adapter or a shared subset can be discussed with the OreSat team.

## Consequences

- The firmware architecture (`docs/firmware-architecture.md`) keeps CCSDS packets as the data format and CANopen as the management layer.
- The object dictionary of every card is generated from a YAML description in the same repository as its firmware (planned).
- We must credit OreSat wherever the card/backplane idea is described (`docs/prior-art.md`, `CREDITS.md` at release).
- Risk: CANopen classic frame limits (8 bytes) versus CAN-FD (64 bytes): SDO segmented transfers stay compatible, bulk data uses CAN-FD frames
  with the CCSDS packet format.

## To verify before freezing

- Read the OreSat backplane and card mechanical repositories in detail and check the exact CAN configuration (bit rate, extended IDs,
  ECSS CAN bus extended protocol use).
- Ask the OreSat maintainers whether they would accept or want a shared subset (a courtesy and a sanity check).
