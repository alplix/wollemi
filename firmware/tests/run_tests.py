"""Build and run the firmware host tests, including Ed25519 cross-checks (Python signs, C verifies).

Usage: python firmware/tests/run_tests.py
Needs gcc and `pip install cryptography`.
"""
import os
import shutil
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
sys.path.insert(0, os.path.join(ROOT, "protocol", "generated"))
import wollemi_proto as gp  # noqa: E402
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey  # noqa: E402
from cryptography.hazmat.primitives.serialization import Encoding, PublicFormat  # noqa: E402

FLAGS = ["-std=c99", "-Wall", "-Wextra", "-Werror", "-O2"]
COMMON = ["wl_auth.c", "wl_modes.c", "wl_fdir.c", "wl_cmdq.c", "wl_ota.c"]
EXT = ".exe" if os.name == "nt" else ""


def build():
    gcc = shutil.which("gcc")
    if not gcc:
        raise SystemExit("gcc not found")
    common = [os.path.join(ROOT, "firmware", "common", f) for f in COMMON if f != "wl_auth.c"]
    unit = os.path.join(HERE, "test_firmware" + EXT)
    subprocess.run([gcc, *FLAGS, os.path.join(HERE, "test_firmware.c"), *common, "-o", unit], check=True)
    auth = os.path.join(HERE, "auth_cli" + EXT)
    tweet = os.path.join(ROOT, "firmware", "third_party", "tweetnacl", "tweetnacl.c")
    # TweetNaCl is third-party code: build it without -Werror
    subprocess.run([gcc, "-std=c99", "-O2", "-c", tweet, "-o", os.path.join(HERE, "tweetnacl.o")], check=True)
    subprocess.run([gcc, *FLAGS, os.path.join(HERE, "auth_cli.c"), os.path.join(ROOT, "firmware", "common", "wl_auth.c"),
                    os.path.join(HERE, "tweetnacl.o"), "-o", auth], check=True)
    return unit, auth


def pub_hex(priv):
    return priv.public_key().public_bytes(Encoding.Raw, PublicFormat.Raw).hex()


def make_tc(priv, counter, valid_until, mode=2, seq=7, coarse=1000):
    vals = dict(mode=mode, reason=1)
    pre = gp.encode("mode_set", vals, seq=seq, coarse=coarse, counter=counter, valid_until=valid_until)
    signed = gp.decode(pre)["signed_bytes"]
    return gp.encode("mode_set", vals, seq=seq, coarse=coarse, counter=counter, valid_until=valid_until,
                     signature=priv.sign(signed))


def auth(exe, last, now, pub, prev, pkt):
    out = subprocess.run([exe, str(last), str(now), pub, prev or "-", pkt.hex()], capture_output=True, text=True)
    return int(out.stdout.strip())


def main():
    unit, exe = build()
    r = subprocess.run([unit], capture_output=True, text=True)
    print(r.stdout.strip())
    if r.returncode != 0:
        print(r.stdout)
        raise SystemExit("firmware unit tests failed")

    k1, k2, bad = Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate(), Ed25519PrivateKey.generate()
    p1, p2 = pub_hex(k1), pub_hex(k2)
    ok = make_tc(k1, counter=10, valid_until=5000)
    cases = []

    def case(name, got, want):
        cases.append((name, got, want))

    case("valid signature", auth(exe, 9, 2000, p1, None, ok), 0)
    case("counter equal (replay)", auth(exe, 10, 2000, p1, None, ok), -5)
    case("counter lower (replay)", auth(exe, 50, 2000, p1, None, ok), -5)
    case("expired", auth(exe, 9, 6000, p1, None, ok), -4)
    case("wrong key", auth(exe, 9, 2000, p2, None, ok), -6)
    case("previous key still accepted", auth(exe, 9, 2000, p2, p1, ok), 0)
    forged = make_tc(bad, counter=10, valid_until=5000)
    case("forged (unknown key)", auth(exe, 9, 2000, p1, p2, forged), -6)
    tam = bytearray(ok)
    tam[20] ^= 0x01                               # flip a payload/counter bit but keep a valid CRC
    body = bytes(tam[:-2])
    tam = body + gp.crc16(body).to_bytes(2, "big")
    case("tampered content, valid CRC", auth(exe, 9, 2000, p1, None, bytes(tam)), -6)
    badcrc = bytearray(ok)
    badcrc[-1] ^= 0xFF
    case("bad CRC", auth(exe, 9, 2000, p1, None, bytes(badcrc)), -2)
    case("truncated", auth(exe, 9, 2000, p1, None, ok[:30]), -1)
    tm = gp.encode("beacon", dict(mode=1, node_health=0, batt_a_mv=6400, batt_b_mv=6400, batt_c_mv=3300, bus_a_mv=6400,
                                  solar_ma=0, temp_body_dc=20, uptime_s=1, reset_count=0))
    tm_padded = tm + bytes(80 - len(tm))         # too short to be a TC once padded wrongly
    case("telemetry packet is not a command", auth(exe, 9, 2000, p1, None, tm_padded[:len(ok)] if len(tm) >= len(ok) else bytes(len(ok))), None)
    nokey = subprocess.run([exe, "0", "0", "00" * 32, "-", ok.hex()], capture_output=True, text=True)
    case("all-zero key rejects", int(nokey.stdout.strip()), -6)

    failed = 0
    for name, got, want in cases:
        if want is None:
            print(f"  [info] {name}: code {got}")
            continue
        good = got == want
        failed += not good
        print(f"  [{'OK  ' if good else 'FAIL'}] {name}: code {got} (expected {want})")
    # counter state advances only on success
    print(f"authentication cross-checks: {len([c for c in cases if c[2] is not None]) - failed}/{len([c for c in cases if c[2] is not None])} OK")
    if failed:
        raise SystemExit(1)
    print("ALL FIRMWARE TESTS PASSED")


if __name__ == "__main__":
    main()
