"""LONG-2 check: every long-life science stream is acquired and stored without the Linux computers.

Usage: python sim/chain_check.py
Reads `chain`, `acquire` and `path` of each [[stream]] in configs/12u_data.toml. A stream marked chain = "long" must be acquired by the flight controller
or the supervisor and its path to the radio may contain only those nodes, the mass memory unit and the radio. Also checks that the marked streams
cover the instruments the longevity document calls the long-life chain (magnetometer, TSI, dosimeter, particle spectrometer, atomic clock).
"""
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALLOWED_LONG = {"fc", "supervisor", "mmu", "radio"}
REQUIRED_LONG = ("magnetometer", "total solar irradiance", "radiation dosimeter", "energetic particle", "atomic clock")


def main():
    data = tomllib.load(open(os.path.join(ROOT, "configs", "12u_data.toml"), "rb"))
    errors, n_long = [], 0
    for s in data["stream"]:
        for f in ("chain", "acquire", "path"):
            if f not in s:
                errors.append(f"stream '{s['name']}' has no '{f}' field")
        if s.get("chain") != "long":
            continue
        n_long += 1
        if s["acquire"] not in ("fc", "supervisor"):
            errors.append(f"long-life stream '{s['name']}' is acquired by '{s['acquire']}'")
        bad = [n for n in s["path"] if n not in ALLOWED_LONG]
        if bad:
            errors.append(f"long-life stream '{s['name']}' depends on {bad}")
    names = {s["name"].lower(): s for s in data["stream"]}
    for key in REQUIRED_LONG:
        hit = [s for n, s in names.items() if key in n]
        if not hit or hit[0].get("chain") != "long":
            errors.append(f"required long-life instrument '{key}' is not in the long chain")
    for e in errors:
        print("CHAIN error:", e)
    if errors:
        print(f"CHAIN CHECK FAILED ({len(errors)} errors)")
        return 1
    print(f"CHAIN CHECK OK: {n_long} long-life streams acquired by the flight controller and stored via the mass memory unit; "
          f"{len(data['stream']) - n_long} streams may use the Linux computers")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
