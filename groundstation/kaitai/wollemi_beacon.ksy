meta:
  id: wollemi_beacon
  title: Wollemi survival beacon (CCSDS Space Packet + Wollemi secondary header)
  application: Wollemi 12U science observatory, survival chain beacon (APID = SUP node << 8 | 1)
  license: Apache-2.0
  endian: be
  bit-endian: be
doc: |
  Decodes the Wollemi spacecraft's survival beacon (`protocol/messages.toml`, message "beacon", id 1, node SUP, kind tm):
  "minimal state, decodable by any listener; sent by the supervisor even in sun-only mode."
  This is the one message meant to be received and understood by anyone, including a station that has never seen
  the mission before, so it is the first candidate submitted to SatNOGS Decoders (docs/ground-station-kit.md, OPEN-7)
  so any SatNOGS station worldwide decodes it automatically, not only the project's own stations.
  Wire format: unauthenticated CCSDS Space Packet (kind = tm, no signature, no counter/valid_until), Wollemi secondary
  header, payload, CRC-16 (not verified by this struct; a station should still check it against `crc16` in
  `protocol/generated/wollemi_proto.py` before trusting the fields).
seq:
  - id: primary_header
    type: primary_header
  - id: coarse_time
    type: u4
    doc: TAI seconds (secondary header)
  - id: fine_time
    type: u2
    doc: sub-second ticks (secondary header)
  - id: flags
    type: flags_byte
  - id: format_version
    type: u1
    doc: per-message format version; the field layout below is version 0
  - id: mode
    type: u1
    doc: spacecraft mode (gk_modes.h / wl_modes.h mode enum)
  - id: node_health
    type: u1
    doc: bitfield, one bit per monitored node (see docs/protocol.md)
  - id: batt_a_mv
    type: u2
    doc: pack A bus voltage, millivolts
  - id: batt_b_mv
    type: u2
    doc: pack B bus voltage, millivolts
  - id: batt_c_mv
    type: u2
    doc: survival pack C bus voltage, millivolts
  - id: bus_a_mv
    type: u2
    doc: chain A regulated bus voltage, millivolts
  - id: solar_ma
    type: u2
    doc: total solar current, milliamps
  - id: temp_body_dc
    type: s2
    doc: body temperature, deci-degrees Celsius (value / 10.0 = degrees C)
  - id: uptime_s
    type: u4
    doc: seconds since last supervisor reset
  - id: reset_count
    type: u2
    doc: lifetime supervisor reset counter
  - id: crc16
    type: u2
    doc: CRC-16/CCITT-FALSE over every preceding byte of the packet (verify separately; not checked by this struct)
types:
  primary_header:
    doc: CCSDS Space Packet primary header (6 bytes)
    seq:
      - id: version
        type: b3
        doc: always 0 for this mission
      - id: is_tc
        type: b1
        doc: 0 = telemetry (this message is always tm)
      - id: has_secondary_header
        type: b1
        doc: always 1 for this mission
      - id: apid
        type: b11
        doc: (node << 8) | message id; this decoder is for APID = (SUP node id << 8) | 1
      - id: sequence_flags
        type: b2
        doc: always 3 (unsegmented) for this mission
      - id: sequence_count
        type: b14
      - id: packet_data_length
        type: u2
        doc: CCSDS convention -- total packet length in octets is this value + 7
  flags_byte:
    doc: secondary header flags byte
    seq:
      - id: clock_quality
        type: b2
        doc: 0-3, higher is better (see docs/protocol.md)
      - id: priority_minus_1
        type: b2
        doc: message priority - 1 (P1..P4)
      - id: reserved
        type: b4
