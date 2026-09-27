"""Verify wollemi_beacon.ksy against the real protocol implementation, without a Kaitai Struct compiler
(no Java toolchain in this environment; the .ksy syntax itself still needs a real `kaitai-struct-compiler`
run before it is submitted to satnogs-decoders -- this script only proves the *byte-level model* the .ksy
describes is correct, by hand-parsing a real encoded packet the same way the .ksy claims to and comparing
every field against the values that were encoded).

Usage: python groundstation/kaitai/verify_beacon_ksy.py
"""
import os
import struct
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "protocol", "generated"))
import wollemi_proto as wp  # noqa: E402


def parse_like_ksy(pkt):
    """Hand-parse exactly what wollemi_beacon.ksy declares, field by field."""
    word0, word1, length = struct.unpack(">HHH", pkt[:6])
    out = {
        "version": (word0 >> 13) & 0b111,
        "is_tc": (word0 >> 12) & 1,
        "has_secondary_header": (word0 >> 11) & 1,
        "apid": word0 & 0x7FF,
        "sequence_flags": (word1 >> 14) & 0b11,
        "sequence_count": word1 & 0x3FFF,
        "packet_data_length": length,
    }
    coarse, fine, flags, ver = struct.unpack(">IHBB", pkt[6:14])
    out["coarse_time"] = coarse
    out["fine_time"] = fine
    out["clock_quality"] = (flags >> 6) & 0b11
    out["priority_minus_1"] = (flags >> 4) & 0b11
    out["reserved"] = flags & 0b1111
    out["format_version"] = ver
    (mode, node_health, batt_a_mv, batt_b_mv, batt_c_mv, bus_a_mv, solar_ma, temp_body_dc,
     uptime_s, reset_count) = struct.unpack(">BBHHHHHhIH", pkt[14:34])
    out.update(mode=mode, node_health=node_health, batt_a_mv=batt_a_mv, batt_b_mv=batt_b_mv,
               batt_c_mv=batt_c_mv, bus_a_mv=bus_a_mv, solar_ma=solar_ma, temp_body_dc=temp_body_dc,
               uptime_s=uptime_s, reset_count=reset_count)
    out["crc16"] = struct.unpack(">H", pkt[34:36])[0]
    assert len(pkt) == 36, f"unexpected beacon length {len(pkt)} (fields or SEC_LEN drifted from the .ksy)"
    return out


def main():
    values = dict(mode=4, node_health=0b00000101, batt_a_mv=6350, batt_b_mv=6280, batt_c_mv=6100,
                  bus_a_mv=5100, solar_ma=1850, temp_body_dc=-235, uptime_s=1234567, reset_count=3)
    pkt = wp.encode("beacon", values, seq=42, coarse=1_800_000_000, fine=1234, priority=1, clock_quality=3)
    got = parse_like_ksy(pkt)

    checks = [
        ("version", 0), ("is_tc", 0), ("has_secondary_header", 1),
        ("apid", wp.BY_NAME["beacon"][0]), ("sequence_flags", 3), ("sequence_count", 42),
        ("packet_data_length", len(pkt) - 7),
        ("coarse_time", 1_800_000_000), ("fine_time", 1234),
        ("clock_quality", 3), ("priority_minus_1", 0), ("format_version", wp.MESSAGES[wp.BY_NAME["beacon"][0]]["version"]),
    ]
    for name, expect in checks:
        got_v = got[name]
        status = "OK" if got_v == expect else "MISMATCH"
        print(f"[{status}] {name}: got {got_v}, expected {expect}")
        assert got_v == expect, f"{name}: got {got_v}, expected {expect}"
    for name, expect in values.items():
        got_v = got[name]
        status = "OK" if got_v == expect else "MISMATCH"
        print(f"[{status}] {name}: got {got_v}, expected {expect}")
        assert got_v == expect, f"{name}: got {got_v}, expected {expect}"
    assert got["crc16"] == wp.crc16(pkt[:-2]), "CRC field position or algorithm does not match"
    print("[OK] crc16 field is at the byte position the .ksy claims and matches wp.crc16()")
    print()
    print("All fields in wollemi_beacon.ksy's declared byte/bit layout match the real encoder output.")
    print("This proves the WIRE-FORMAT MODEL is correct; it does not prove the .ksy file's Kaitai Struct")
    print("syntax compiles (no Java / kaitai-struct-compiler is available in this environment) -- run")
    print("`kaitai-struct-compiler --target python wollemi_beacon.ksy` and parse a real capture before")
    print("submitting it to https://github.com/librespacefoundation/satnogs-decoders.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
