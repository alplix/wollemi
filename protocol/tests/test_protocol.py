"""Protocol tests: round trips, corruption detection and C <-> Python cross-checks.

Usage: python protocol/tests/test_protocol.py
"""
import os
import random
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "generated"))
import wollemi_proto as gp  # noqa: E402

RNG = random.Random(1234)
ranges = {"u8": (0, 255), "u16": (0, 65535), "u32": (0, 2 ** 32 - 1), "i8": (-128, 127), "i16": (-32768, 32767),
          "i32": (-2 ** 31, 2 ** 31 - 1)}


def random_values(msg):
    vals = {}
    for name, t, off, size in msg["fields"]:
        vals[name] = bytes(RNG.randrange(256) for _ in range(size)) if t.startswith("bytes") else RNG.randint(*ranges[t])
    return vals


def test_roundtrip_all():
    n = 0
    for apid, msg in gp.MESSAGES.items():
        vals = random_values(msg)
        kw = dict(seq=RNG.randrange(16384), coarse=RNG.randrange(2 ** 32), fine=RNG.randrange(65536))
        if msg["kind"] == "tc":
            kw.update(counter=RNG.randrange(2 ** 32), valid_until=RNG.randrange(2 ** 32),
                      signature=bytes(RNG.randrange(256) for _ in range(64)))
        pkt = gp.encode(msg["name"], vals, **kw)
        out = gp.decode(pkt)
        assert out["fields"] == vals, msg["name"]
        assert out["apid"] == apid and out["seq"] == kw["seq"] and out["coarse"] == kw["coarse"]
        assert out["tc"] == (msg["kind"] == "tc")
        if msg["kind"] == "tc":
            assert out["counter"] == kw["counter"] and out["signature"] == kw["signature"]
            assert out["signed_bytes"] == pkt[: len(out["signed_bytes"])]
        n += 1
    return n


def test_corruption():
    pkt = bytearray(gp.encode("beacon", random_values(gp.BY_NAME["beacon"][1])))
    bad = 0
    for i in range(len(pkt) * 8):
        p = bytearray(pkt)
        p[i // 8] ^= 1 << (i % 8)
        try:
            gp.decode(bytes(p))
        except ValueError:
            bad += 1
    assert bad == len(pkt) * 8, "every single-bit corruption must be rejected"
    return bad


def test_c_crosscheck():
    gcc = shutil.which("gcc")
    if not gcc:
        return "skipped (no gcc)"
    exe = os.path.join(HERE, "c_crosscheck.exe" if os.name == "nt" else "c_crosscheck")
    subprocess.run([gcc, "-std=c99", "-Wall", "-Wextra", "-Werror", "-O2", os.path.join(HERE, "c_crosscheck.c"), "-o", exe], check=True)
    lines = subprocess.run([exe, "pack"], capture_output=True, text=True, check=True).stdout.split()
    beacon_c, burn_c = lines[0], lines[1]
    beacon_vals = dict(mode=2, node_health=0xA5, batt_a_mv=7400, batt_b_mv=7390, batt_c_mv=3300, bus_a_mv=7350,
                       solar_ma=1234, temp_body_dc=-153, uptime_s=86400 * 400, reset_count=7)
    py_b = gp.encode("beacon", beacon_vals, seq=42, coarse=0x11223344, fine=0x5566, clock_quality=3, priority=1)
    assert py_b.hex() == beacon_c, "beacon bytes differ between C and Python"
    burn_vals = dict(start_coarse=123456, duration_s=7200, dir_x_mm=-1000, dir_y_mm=5, dir_z_mm=32767, thrust_pct=80)
    py_t = gp.encode("burn_schedule", burn_vals, seq=9, coarse=1000, fine=2, clock_quality=2, priority=1,
                     counter=77, valid_until=5000, signature=bytes(range(64)))
    assert py_t.hex() == burn_c, "telecommand bytes differ between C and Python"
    out = subprocess.run([exe, "unpack", py_b.hex()], capture_output=True, text=True, check=True).stdout.split()
    assert out[0] == "0" and int(out[1]) == 2 and int(out[3]) == 7400 and int(out[9]) == -153 and int(out[10]) == 86400 * 400
    assert int(out[12]) == 42 and int(out[13]) == 0x11223344
    bad = bytearray(py_b)
    bad[10] ^= 1
    out = subprocess.run([exe, "unpack", bad.hex()], capture_output=True, text=True, check=True).stdout.split()
    assert out[0] == "-2", "C unpack must reject a corrupted packet with a CRC error"
    return "C pack == Python encode (TM and TC), C unpack of Python packet OK, C rejects corruption"


if __name__ == "__main__":
    print(f"round trip: {test_roundtrip_all()} messages OK")
    print(f"corruption: {test_corruption()} single-bit flips rejected")
    print(f"C cross-check: {test_c_crosscheck()}")
    print("ALL PASSED")
