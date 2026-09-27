"""Optional: run wollemi_protocol.ksy through the REAL official kaitai-struct-compiler (not the hand-parser
model check in verify_all_ksy.py) and decode a real packet per message with the generated parser. This needs
a JVM and the compiler jar/launcher, neither of which is a standing dependency of this repository, so this
script is not part of `tools/check_all.py`: it silently reports "skipped" and exits 0 if it can't find them,
rather than failing the regression for everyone who doesn't have Java installed.

Confirmed working once in this development environment: kaitai-struct-compiler 0.11, Eclipse Temurin JDK 17,
2026-09-27 -- all 27 messages compiled and round-tripped correctly (docs/ground-station-kit.md records this).
Re-run this script after any change to protocol/messages.toml or protocol/gen_kaitai.py to reconfirm.

Usage:
  python groundstation/kaitai/compile_check.py
  KAITAI_STRUCT_COMPILER=/path/to/kaitai-struct-compiler(.bat) python groundstation/kaitai/compile_check.py
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
KSY = os.path.join(ROOT, "groundstation", "kaitai", "wollemi_protocol.ksy")


def find_compiler():
    env = os.environ.get("KAITAI_STRUCT_COMPILER")
    if env and os.path.exists(env):
        return env
    for pattern in (
        os.path.expandvars(r"%TEMP%\kaitai\kaitai-struct-compiler-*\bin\kaitai-struct-compiler.bat"),
        os.path.expandvars(r"%TEMP%\kaitai\kaitai-struct-compiler-*\bin\kaitai-struct-compiler"),
        r"C:\Program Files\kaitai-struct-compiler\bin\kaitai-struct-compiler.bat",
    ):
        hits = glob.glob(pattern)
        if hits:
            return hits[0]
    return None


def find_java():
    if shutil.which("java"):
        return shutil.which("java")
    for pattern in (r"C:\Program Files\Eclipse Adoptium\jdk-*\bin\java.exe",
                    r"C:\Program Files\Eclipse Adoptium\jdk-*-jre\bin\java.exe"):
        hits = glob.glob(pattern)
        if hits:
            return hits[0]
    return None


def main():
    java = find_java()
    compiler = find_compiler()
    if not java or not compiler:
        print(f"SKIPPED: {'no java' if not java else 'java OK'}, {'no kaitai-struct-compiler' if not compiler else 'compiler OK'} "
              f"(this check needs both; it is optional and not part of the required regression)")
        return 0
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(java) + os.pathsep + env.get("PATH", "")
    with tempfile.TemporaryDirectory() as out:
        launch = ["cmd", "/c", compiler] if compiler.endswith(".bat") else ["bash", compiler]
        r = subprocess.run(launch + ["--target", "python", "--outdir", out, KSY], env=env, capture_output=True, text=True)
        if r.returncode != 0:
            print("COMPILE FAILED:", r.stdout, r.stderr)
            return 1
        try:
            import kaitaistruct  # noqa: F401
        except ImportError:
            print("SKIPPED: kaitai-struct-compiler ran, but the `kaitaistruct` runtime package is not installed (`pip install kaitaistruct`)")
            return 0
        sys.path.insert(0, out)
        sys.path.insert(0, os.path.join(ROOT, "protocol"))
        sys.path.insert(0, os.path.join(ROOT, "protocol", "generated"))
        import gen_kaitai as gk  # noqa: E402
        import wollemi_proto as wp  # noqa: E402
        from wollemi_protocol import WollemiProtocol  # noqa: E402
        sys.path.insert(0, os.path.join(ROOT, "groundstation", "kaitai"))
        from verify_all_ksy import sample_value  # noqa: E402

        cfg = gk.load()
        n_ok = 0
        for msg in cfg["message"]:
            name, kind = msg["name"], msg["kind"]
            values = {fname: sample_value(t, salt=i + 7) for i, (fname, t) in enumerate(msg["fields"])}
            kw = dict(seq=17, coarse=1_900_000_001, fine=4321, priority=1, clock_quality=2)
            if kind == "tc":
                kw.update(counter=555, valid_until=999999999)
            pkt = wp.encode(name, values, **kw)
            parsed = WollemiProtocol.from_bytes(pkt)
            b = parsed.body
            assert parsed.primary_header.apid == wp.BY_NAME[name][0], name
            assert parsed.primary_header.is_tc == (kind == "tc"), name
            if kind == "tc":
                assert b.counter == kw["counter"] and b.valid_until == kw["valid_until"], name
                assert bytes(b.signature) == bytes(64), name
            for fname, t in msg["fields"]:
                got = bytes(getattr(b, fname)) if t.startswith("bytes") else getattr(b, fname)
                assert got == values[fname], f"{name}.{fname}: got {got!r} expected {values[fname]!r}"
            assert b.crc16 == wp.crc16(pkt[:-2]), name
            n_ok += 1
        print(f"OK: {n_ok}/{len(cfg['message'])} messages compiled and round-tripped through the real kaitai-struct-compiler")
        return 0 if n_ok == len(cfg["message"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
