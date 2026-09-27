"""Generate a Kaitai Struct decoder covering every message in protocol/messages.toml, for eventual submission
to https://github.com/librespacefoundation/satnogs-decoders (see docs/ground-station-kit.md, OPEN-7).

Single source of truth: this reads the same protocol/messages.toml that protocol/gen.py uses for the C and
Python implementations, so the three can never drift apart the way a hand-written decoder could.

Usage: python protocol/gen_kaitai.py
Writes groundstation/kaitai/wollemi_protocol.ksy (replaces the earlier hand-written wollemi_beacon.ksy, which
covered only the beacon message; this file covers all 27).

Important limits, stated here so they are not lost on the way to a real submission:
- The .ksy syntax has not been run through the official `kaitai-struct-compiler` (no Java toolchain in this
  environment). `groundstation/kaitai/verify_all_ksy.py` instead hand-parses real encoder output for every
  message and checks every field, which proves the byte/bit *model* this generator emits is correct -- it does
  not prove the emitted YAML is syntactically valid Kaitai Struct. Run the real compiler before submitting.
- Telecommand messages ("kind = tc") are unsigned/zero-signature in ground test fixtures; a real capture would
  carry a real Ed25519 signature in that same 64-byte field, which this decoder does not attempt to verify
  (`firmware/common/wl_auth.c` is the verifier; a passive ground decoder has no reason to hold the private key).
"""
import os
import re
import tomllib

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(os.path.dirname(HERE), "groundstation", "kaitai")
OUT_PATH = os.path.join(OUT_DIR, "wollemi_protocol.ksy")

SEC_LEN = 8
TC_EXTRA = 8
SIG_LEN = 64
KAITAI_TYPE = {"u8": "u1", "u16": "u2", "u32": "u4", "i8": "s1", "i16": "s2", "i32": "s4", "f32": "f4"}


def load():
    return tomllib.load(open(os.path.join(HERE, "messages.toml"), "rb"))


def field_size(t):
    m = re.fullmatch(r"bytes\[(\d+)\]", t)
    return int(m.group(1)) if m else {"u8": 1, "u16": 2, "u32": 4, "i8": 1, "i16": 2, "i32": 4, "f32": 4}[t]


def field_lines(name, t, indent="      "):
    m = re.fullmatch(r"bytes\[(\d+)\]", t)
    if m:
        return f"{indent}- id: {name}\n{indent}  size: {m.group(1)}\n"
    return f"{indent}- id: {name}\n{indent}  type: {KAITAI_TYPE[t]}\n"


HEADER_TYPES = '''types:
  primary_header:
    doc: CCSDS Space Packet primary header (6 bytes), common to every Wollemi message.
    seq:
      - id: version
        type: b3
        doc: always 0 for this mission
      - id: is_tc
        type: b1
        doc: 1 = telecommand (authenticated, kind "tc"); 0 = telemetry or the public relay message
      - id: has_secondary_header
        type: b1
        doc: always 1 for this mission
      - id: apid
        type: b11
        doc: (node id << 8) | message id; selects the body type below
      - id: sequence_flags
        type: b2
        doc: always 3 (unsegmented) for this mission
      - id: sequence_count
        type: b14
      - id: packet_data_length
        type: u2
        doc: CCSDS convention -- total packet length in octets is this value + 7
  secondary_header:
    doc: Wollemi secondary header (8 bytes), common to every message.
    seq:
      - id: coarse_time
        type: u4
        doc: TAI seconds
      - id: fine_time
        type: u2
        doc: sub-second ticks, 1/65536 s
      - id: flags
        type: flags_byte
      - id: format_version
        type: u1
        doc: per-message field-layout version (increments if fields ever change)
  flags_byte:
    seq:
      - id: clock_quality
        type: b2
      - id: priority_minus_1
        type: b2
        doc: message priority - 1 (P1..P4)
      - id: reserved
        type: b4
'''


def body_type(m, nodes):
    name, kind = m["name"], m["kind"]
    lines = [f"  {name}_body:", "    seq:",
             "      - id: secondary_header", "        type: secondary_header"]
    if kind == "tc":
        lines += ["      - id: counter", "        type: u4",
                   "      - id: valid_until", "        type: u4"]
    for fname, ftype in m["fields"]:
        lines.append(field_lines(fname, ftype).rstrip("\n"))
    if kind == "tc":
        lines += [f"      - id: signature", f"        size: {SIG_LEN}",
                   "        doc: Ed25519 signature over everything from the primary header through the payload (verified by firmware/common/wl_auth.c, not by this decoder)"]
    lines += ["      - id: crc16", "        type: u2",
              "        doc: CRC-16/CCITT-FALSE over every preceding byte (verify separately; not checked by this struct)"]
    return "\n".join(lines) + "\n"


def main():
    cfg = load()
    nodes = cfg["nodes"]
    messages = cfg["message"]
    L = ["meta:", "  id: wollemi_protocol",
         "  title: Wollemi 12U science observatory -- full protocol (all messages, CCSDS Space Packet + Wollemi secondary header)",
         "  application: Wollemi (github.com/alplix/wollemi, private until the design is complete)",
         "  license: Apache-2.0", "  endian: be", "  bit-endian: be",
         "doc: |", "  Generated by protocol/gen_kaitai.py from protocol/messages.toml (the same source protocol/gen.py uses",
         "  for the C and Python implementations); do not edit by hand. Covers all 27 messages by switching on the CCSDS",
         "  APID in the primary header. See protocol/gen_kaitai.py's own docstring for what is and is not verified.",
         "seq:", "  - id: primary_header", "    type: primary_header",
         "  - id: body", "    type:", "      switch-on: primary_header.apid", "      cases:"]
    for m in messages:
        apid = (nodes[m["node"]] << 8) | m["id"]
        L.append(f'        {apid}: {m["name"]}_body  # {m["name"]} ({m["node"]}, {m["kind"]})')
    L.append(HEADER_TYPES.rstrip("\n"))
    for m in messages:
        L.append(body_type(m, nodes).rstrip("\n"))
    os.makedirs(OUT_DIR, exist_ok=True)
    open(OUT_PATH, "w", encoding="utf-8").write("\n".join(L) + "\n")
    print(f"Wrote {OUT_PATH}: {len(messages)} message bodies")


if __name__ == "__main__":
    main()
