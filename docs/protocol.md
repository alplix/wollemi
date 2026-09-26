# Ginkgo protocol specification (draft v0)

Single source of truth: `protocol/messages.toml`. `python protocol/gen.py` generates the flight C header
(`protocol/generated/ginkgo_proto.h`), the ground Python module (`ginkgo_proto.py`) and the message
reference (`docs/protocol-messages.md`). `python protocol/tests/test_protocol.py` checks round trips,
corruption detection and byte-exact agreement between C and Python.

Goals: readable in 50 years (self-describing, versioned, documented, no secrets on the air except signatures),
identical on every link, and usable by any volunteer station with the open reference decoder.

## 1. Packet format

Every message is a CCSDS Space Packet (CCSDS 133.0-B) with a Ginkgo secondary header; all fields big-endian.

| Bytes | Field | Notes |
|---|---|---|
| 6 | Primary header | version 0, type (0 TM, 1 TC), secondary-header flag = 1, APID (11 bits), sequence flags = 3, sequence count (14 bits), data length - 1 |
| 8 | Secondary header | coarse time u32 (s since 2000-01-01 TAI), fine u16 (1/65536 s), flags u8 (bits 7-6 clock quality, 5-4 priority P1..P3), format version u8 |
| 8 | TC only: counter u32, valid_until u32 | monotonically increasing counter and TAI expiry |
| N | Payload | fixed layout per message, see `docs/protocol-messages.md` |
| 64 | TC only: Ed25519 signature | over every byte from the primary header up to the signature |
| 2 | CRC-16/CCITT-FALSE | over everything before it |

- **APID** = node (3 bits) << 8 | message id (8 bits). Nodes: SUP 0, FCA 1, FCB 2, MMU 3, PAYL 4, PAYH 5, GND 6, ALL 7.
- **Versioning:** the format-version byte of a message is incremented on any field change; old versions stay
  decodable forever (the generated tables keep every version once we start flying).
- **Time:** TAI, disciplined by the CSAC + GNSS PPS; clock-quality bits say whether it is trusted.
- **Priority:** P1 must reach the ground, P2 normal science, P3 best effort (public relay).

## 2. Security (open but protected)

- Nothing on the air is encrypted (amateur-band rule); telecommands are **signed** so open receivers can still
  verify them but nobody can forge them.
- Signature: Ed25519 over the packet; verified by the supervisor (keys in its FRAM). The counter must be strictly
  greater than the last accepted counter and `valid_until` must not have passed (replay protection).
- Key hierarchy: offline root key signs operational keys (`key_rotate`); operational keys rotate on a schedule;
  the supervisor keeps the current and previous key id.
- Public relay traffic (`relay_msg`, kind `public`) is unsigned, quota limited and lives on an isolated path that
  cannot reach control functions.
- Reference note: the current tools pack and check the structure and CRC; signature creation and verification
  are to be added with a vetted Ed25519 library (not hand-written) in the flight and ground code.

## 3. Links

| Link | Framing (proposed) | Rate |
|---|---|---|
| UHF beacon (CW + AX.25 UI) | Callsign header, then a `beacon` packet as payload; a plain CW/ASCII fallback line so any listener can decode without our software | ~1-5 kbps |
| UHF LoRa (433 MHz) | LoRa frame = one packet (max ~250 bytes), no encryption | ~1-5 kbps |
| S-band (2.4 GHz) | CCSDS TM synchronisation and channel coding style frames (attached sync marker, Reed-Solomon, randomiser) carrying packets and CFDP PDUs; adaptive rate 250 kbps to 2 Mbps | see `docs/data-plan.md` |
| Uplink | UHF for commands (short, signed); S-band uplink optional for OTA | low |

The survival beacon is emitted directly by the supervisor even in sun-only mode; it must fit in one small frame
(the `beacon` message is 40 bytes on the wire).

## 4. File transfer

CFDP (CCSDS 727.0-B) class 2 (acknowledged) between spacecraft and ground, resumable across passes. Large data
products are stored as objects in the mass memory unit and transferred as files. Ground acknowledgment
(`obj_ack`) lets the spacecraft delete its copy; P1 objects are never evicted before acknowledgment.

## 5. Object and archive format

**On-board object** (in the MMU): header = magic `GKOB`, version u8, APID u16, priority u8, t_start u32+u16,
t_end u32+u16, payload length u32, CRC-32C u32, BLAKE2s-128 hash; then the payload (a stream of complete Space
Packets or a data product).

**Open archive** (published continuously):

- `*.gpk`: the exact wire packets, concatenated (lossless raw record), one file per APID group per day;
- `*.json`: index (time span, APID, counts, hashes) and instrument metadata (units, calibration version);
- `MANIFEST` with SHA-256 of every file, plus a copy of the protocol version (`messages.toml`, `docs/protocol.md`) used
  to produce them, so a future user can decode without our tools;
- derived, human-readable products (CSV/NetCDF) with units and calibration provenance.

## 6. Extending the protocol

Add a `[[message]]` to `messages.toml`, run `gen.py` and the tests, update the message reference, and bump the
format version when changing an existing layout. Never reuse an APID for a different meaning.

## 7. Open items

- Integrate a vetted Ed25519 implementation and add signature tests.
- Full AX.25 and LoRa framing definitions and the S-band coding parameters (with the SDR chosen for the ground kit).
- CFDP profile (class, segment size, timers) and store-and-forward handling on the relay path.
- Variable-length messages (image tiles, spectra) and a compressed-data container.
- Fuzzing of the decoders and a formal review of the security model.
