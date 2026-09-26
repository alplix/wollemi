"""Centre-of-mass and per-column thermal check for the 12U layout.

Usage: python sim/balance.py configs/12u_science.toml configs/12u_layout.toml
Cell centres: x,y = +-CELL_XY around the geometric centre, z = deck offset (D1 nadir = -CELL_Z).
Ring order Q1(+,+) Q2(-,+) Q3(-,-) Q4(+,-).
"""
import re
import sys
import tomllib

CELL_XY = 56.6      # mm, half of a 113.2 mm cell
CELL_Z = 113.6      # mm, deck pitch
COL_XY = {1: (CELL_XY, CELL_XY), 2: (-CELL_XY, CELL_XY), 3: (-CELL_XY, -CELL_XY), 4: (CELL_XY, -CELL_XY)}
LIMIT_XY, LIMIT_Z = 20.0, 70.0   # mm, typical deployer targets; verify against the chosen dispenser
RAD_W_M2 = 120.0                 # net radiative rejection per m2 of radiator at ~20 C (with environment)
PROP_WATER_KG = 0.5   # iodine


def parse_at(at):
    m = re.fullmatch(r"Q(\d)/(\d)(?:-(\d))?", at)
    if not m:
        return at, []
    d1 = int(m.group(2))
    return int(m.group(1)), list(range(d1, int(m.group(3) or d1) + 1))


def main(cfg_path, lay_path):
    cfg = tomllib.load(open(cfg_path, "rb"))
    lay = tomllib.load(open(lay_path, "rb"))
    geo = cfg["geometry"]
    usable = geo["envelope_cm3"] * (1 - geo["structure_fraction"]) * geo["packing_efficiency"]
    cap = usable / 12
    fill = {(q, d): 0.0 for q in range(1, 5) for d in range(1, 4)}
    parts = []   # (name, mass, x, y, z, power)
    col_power = {q: 0.0 for q in range(1, 5)}
    for m in cfg["module"]:
        hit = next(p for p in lay["place"] if m["name"].startswith(p["match"]))
        q, ds = parse_at(hit["at"])
        v = m.get("volume_cm3", 0)
        mass, pw = m["mass_kg"], m["power_w"] * m["duty"]
        if isinstance(q, str):
            x_ = -65.0 if q == "bay" else 0.0          # propulsion bay centre (mm), mid-height on the -X side
            parts.append((m["name"], mass, x_, 0.0, 0.0, pw))
            continue
        share = {}
        if hit.get("pack") == "sequential":
            rem = v
            for d in ds:
                take = min(rem, cap - fill[(q, d)])
                share[d] = take
                fill[(q, d)] += take
                rem -= take
            if rem > 0:
                share[ds[-1]] += rem
                fill[(q, ds[-1])] += rem
        else:
            for d in ds:
                share[d] = v / len(ds)
                fill[(q, d)] += v / len(ds)
        tot = sum(share.values()) or 1
        x, y = COL_XY[q]
        z = sum(share[d] / tot * (d - 2) * CELL_Z for d in ds)
        parts.append((m["name"], mass, x, y, z, pw))
        col_power[q] += pw

    def com(items):
        M = sum(p[1] for p in items)
        return M, tuple(sum(p[1] * p[i] for p in items) / M for i in (2, 3, 4))

    M, (cx, cy, cz) = com(parts)
    # end of life: water gone from the tank position
    prop = next(p for p in parts if p[0].startswith("Bus: micro-propulsion"))
    eol = [p if p is not prop else (p[0], p[1] - PROP_WATER_KG, p[2], p[3], p[4], p[5]) for p in parts]
    Me, (ex, ey, ez) = com(eol)
    ok = lambda a, b: "OK  " if a <= LIMIT_XY and b <= LIMIT_Z else "FAIL"
    print(f"== Mass balance ({M:.2f} kg BOL, {Me:.2f} kg EOL) ==")
    print(f"BOL CoM offset: x {cx:+.1f}, y {cy:+.1f}, z {cz:+.1f} mm [{ok(max(abs(cx), abs(cy)), abs(cz))}]")
    print(f"EOL CoM offset: x {ex:+.1f}, y {ey:+.1f}, z {ez:+.1f} mm [{ok(max(abs(ex), abs(ey)), abs(ez))}]")
    print(f"Targets (typical, verify with dispenser): |x|,|y| <= {LIMIT_XY:.0f} mm, |z| <= {LIMIT_Z:.0f} mm")
    print(f"Shift from propellant use: {((ex-cx)**2+(ey-cy)**2+(ez-cz)**2)**0.5:.1f} mm")
    print()
    face = geo["large_face_m2"]           # 226 x 340; a column owns half of each of two faces
    col_skin = face                        # 2 half-faces
    print("== Per-column heat (average dissipation) ==")
    print(f"{'col':4s} {'avg W':>6s} {'radiator need m2':>17s} {'available skin m2':>18s} {'% of skin':>10s}")
    for q in range(1, 5):
        need = col_power[q] / RAD_W_M2
        print(f"Q{q:<3d} {col_power[q]:6.2f} {need:17.3f} {col_skin:18.3f} {need / col_skin * 100:9.0f}%")
    tot = sum(col_power.values())
    print(f"total dissipated {tot:.1f} W; see docs for peak (Jetson burst 10 W) handling")


if __name__ == "__main__":
    main(*(sys.argv[1:3] or ["configs/12u_science.toml", "configs/12u_layout.toml"]))
