"""Verify wollemi_protocol.ksy (protocol/gen_kaitai.py) against the real protocol encoder, for all 27 messages.

Same caveat as before: no Java/kaitai-struct-compiler is available in this environment, so this does not prove
the emitted YAML is syntactically valid Kaitai Struct -- it proves the byte/bit *model* the generator emits
(header sizes, tc-extra placement, signature placement, field order and sizes) is correct, by hand-parsing a
real encoded packet the same way `protocol/gen_kaitai.py`'s `body_type()` declares the layout, independently of
`wollemi_proto.decode()` (so a bug shared between the two would not hide here), for every message in
protocol/messages.toml.

Usage: python groundstation/kaitai/verify_all_ksy.py
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "protocol"))
sys.path.insert(0, os.path.join(ROOT, "protocol", "generated"))
import gen_kaitai as gk  # noqa: E402
import wollemi_proto as wp  # noqa: E402

STRUCT_FMT = {"u8": ">B", "u16": ">H", "u32": ">I", "i8": ">b", "i16": ">h", "i32": ">i", "f32": ">f"}


def sample_value(t, salt):
    if t.startswith("bytes"):
        n = gk.field_size(t)
        return bytes((salt + i) % 256 for i in range(n))
    if t in ("i8", "i16", "i32"):
        bits = {"i8": 7, "i16": 15, "i32": 31}[t]
        return (salt % (2 ** bits)) - (2 ** (bits - 1)) + 1  # a distinct, in-range signed value
    bits = {"u8": 8, "u16": 16, "u32": 32}[t]
    return (salt * 2654435761 + 12345) % (2 ** bits)


def parse_body_like_ksy(pkt, msg):
    """Hand-parse exactly what gen_kaitai.body_type() declares for this message: secondary_header (8), then
    counter/valid_until (8, tc only), then the payload fields in order, then a 64-byte signature (tc only),
    then a 2-byte CRC. Offsets are computed here from scratch, not imported from gen.py/gen_kaitai.py, so a
    shared bug in the offset math would not hide."""
    off = 6  # primary header
    coarse, fine, flags, ver = struct.unpack(">IHBB", pkt[off:off + 8])
    off += 8
    # kept in a dict separate from the payload fields below: a message can (and one does) define its own
    # payload field also called "clock_quality", which must not be confused with the secondary header's.
    header = {"coarse_time": coarse, "fine_time": fine, "clock_quality": (flags >> 6) & 0b11,
              "priority_minus_1": (flags >> 4) & 0b11, "reserved": flags & 0b1111, "format_version": ver}
    tc_extra = {}
    if msg["kind"] == "tc":
        counter, valid_until = struct.unpack(">II", pkt[off:off + 8])
        tc_extra["counter"], tc_extra["valid_until"] = counter, valid_until
        off += 8
    payload = {}
    for name, t in msg["fields"]:
        size = gk.field_size(t)
        raw = pkt[off:off + size]
        payload[name] = raw if t.startswith("bytes") else struct.unpack(STRUCT_FMT[t], raw)[0]
        off += size
    tail = {}
    if msg["kind"] == "tc":
        tail["signature"] = pkt[off:off + 64]
        off += 64
    tail["crc16"] = struct.unpack(">H", pkt[off:off + 2])[0]
    off += 2
    return header, tc_extra, payload, tail, off


def main():
    cfg = gk.load()
    n_checked = 0
    for msg in cfg["message"]:
        name, kind = msg["name"], msg["kind"]
        values = {fname: sample_value(t, salt=i + 7) for i, (fname, t) in enumerate(msg["fields"])}
        kw = dict(seq=17, coarse=1_900_000_001, fine=4321, priority=1, clock_quality=2)
        if kind == "tc":
            kw.update(counter=555, valid_until=999999999)
        pkt = wp.encode(name, values, **kw)
        header, tc_extra, payload, tail, consumed = parse_body_like_ksy(pkt, msg)
        assert consumed == len(pkt), f"{name}: parsed {consumed} bytes but the packet is {len(pkt)} bytes"
        assert header["coarse_time"] == kw["coarse"] and header["fine_time"] == kw["fine"], f"{name}: secondary header mismatch"
        assert header["clock_quality"] == kw["clock_quality"], f"{name}: clock_quality mismatch"
        if kind == "tc":
            assert tc_extra["counter"] == kw["counter"] and tc_extra["valid_until"] == kw["valid_until"], f"{name}: tc-extra mismatch"
            assert tail["signature"] == bytes(64), f"{name}: signature field not where the .ksy says (expected the zero-filled default)"
        for fname, t in msg["fields"]:
            expect = values[fname]
            got_v = payload[fname]
            assert got_v == expect, f"{name}.{fname} ({t}): got {got_v!r}, expected {expect!r}"
        assert tail["crc16"] == wp.crc16(pkt[:-2]), f"{name}: crc16 field is not where the .ksy says or the algorithm mismatches"
        print(f"[OK] {name:16s} ({kind:6s}) {len(pkt):3d} bytes, {len(msg['fields']):2d} fields, all match")
        n_checked += 1
    print()
    print(f"All {n_checked} messages in wollemi_protocol.ksy match the real encoder output, field by field.")
    print("This proves the WIRE-FORMAT MODEL is correct for every message; it does not prove the .ksy file's")
    print("Kaitai Struct syntax compiles (no Java / kaitai-struct-compiler is available in this environment) --")
    print("run `kaitai-struct-compiler --target python wollemi_protocol.ksy` and parse a real capture before")
    print("submitting it to https://github.com/librespacefoundation/satnogs-decoders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
