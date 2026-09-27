"""Reference decoder for Wollemi packets (ground kit).

Usage:
  python groundstation/decode.py --hex 0801...        # decode one packet given as hex
  python groundstation/decode.py --file capture.wpk   # decode a concatenated packet stream (archive .wpk format)
  python groundstation/decode.py --demo               # encode and decode a sample beacon

A .wpk file is a plain concatenation of complete CCSDS Space Packets (see docs/protocol.md, section 5).
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "protocol", "generated"))
import wollemi_proto as gp  # noqa: E402


def split_stream(data):
    """Yield complete packets from a concatenated stream; stop at the first framing error."""
    pos = 0
    while pos + 6 <= len(data):
        length = int.from_bytes(data[pos + 4:pos + 6], "big") + 1 + 6
        if pos + length > len(data):
            break
        yield data[pos:pos + length]
        pos += length


def show(pkt):
    try:
        d = gp.decode(pkt)
    except ValueError as e:
        print(f"[bad packet] {e}: {pkt[:12].hex()}...")
        return False
    tag = "TC" if d["tc"] else "TM"
    print(f"{tag} {d['name']:14s} apid 0x{d['apid']:03X} seq {d['seq']:5d} t={d['coarse']}+{d['fine'] / 65536:.3f}s "
          f"P{d['priority']} q{d['clock_quality']}")
    for k, v in d["fields"].items():
        print(f"    {k} = {v.hex() if isinstance(v, bytes) else v}")
    if d["tc"]:
        print(f"    counter {d['counter']} valid_until {d['valid_until']} signature {d['signature'][:8].hex()}... (verify with Ed25519)")
    return True


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hex")
    ap.add_argument("--file")
    ap.add_argument("--demo", action="store_true")
    a = ap.parse_args()
    if a.demo:
        pkt = gp.encode("beacon", dict(mode=2, node_health=0xA5, batt_a_mv=6400, batt_b_mv=6390, batt_c_mv=3300,
                                       bus_a_mv=6350, solar_ma=1234, temp_body_dc=-153, uptime_s=86400 * 400,
                                       reset_count=7), seq=42, coarse=800000000, fine=0x8000)
        print("demo packet:", pkt.hex())
        show(pkt)
    elif a.hex:
        show(bytes.fromhex(a.hex))
    elif a.file:
        data = open(a.file, "rb").read()
        n = ok = 0
        for pkt in split_stream(data):
            n += 1
            ok += show(pkt)
        print(f"{ok}/{n} packets decoded")
    else:
        ap.print_help()


if __name__ == "__main__":
    main()
