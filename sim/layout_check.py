"""Layout checker: cell fill and separation rules.

Usage: python sim/layout_check.py configs/12u_science.toml configs/12u_layout.toml
"""
import re
import sys
import tomllib


def parse_at(at):
    """'Q3/1-3' -> (3, [1,2,3]); 'skin' -> ('skin', [])."""
    m = re.fullmatch(r"Q(\d)/(\d)(?:-(\d))?", at)
    if not m:
        return at, []
    q, d1, d2 = int(m.group(1)), int(m.group(2)), m.group(3)
    return q, list(range(d1, int(d2) + 1)) if d2 else [d1]


def main(cfg_path, lay_path):
    cfg = tomllib.load(open(cfg_path, "rb"))
    lay = tomllib.load(open(lay_path, "rb"))
    geo = cfg["geometry"]
    cols, decks = lay["grid"]["columns"], lay["grid"]["decks"]
    usable = geo["envelope_cm3"] * (1 - geo["structure_fraction"]) * geo["packing_efficiency"]
    cell_cap = usable / (cols * decks)

    where = {}       # module name -> (q, decks)
    unassigned = []
    fill = {(q, d): 0.0 for q in range(1, cols + 1) for d in range(1, decks + 1)}
    other = {"skin": 0.0, "spine": 0.0, "structure": 0.0, "bay": 0.0}
    for m in cfg["module"]:
        hit = next((p for p in lay["place"] if m["name"].startswith(p["match"])), None)
        if not hit:
            unassigned.append(m["name"])
            continue
        q, ds = parse_at(hit["at"])
        where[m["name"]] = (0, [2]) if q == "bay" else (q, ds)
        v = m.get("volume_cm3", 0)
        if isinstance(q, int) and hit.get("pack") == "sequential":
            rem = v
            for d in ds:
                take = min(rem, cell_cap - fill[(q, d)])
                fill[(q, d)] += take
                rem -= take
            if rem > 0:
                fill[(q, ds[-1])] += rem
        elif isinstance(q, int):
            for d in ds:
                fill[(q, d)] += v / len(ds)
        else:
            other[q] += v

    print(f"== Layout: {cfg['platform']['name']} ==")
    print(f"Cell capacity {cell_cap:.0f} cm3 x {cols * decks} cells = {usable:.0f} cm3 usable")
    print("Fill (% of cell capacity), rows = decks D1 nadir .. D3 zenith, columns Q1..Q4")
    for d in range(1, decks + 1):
        row = "  ".join(f"{fill[(q, d)] / cell_cap * 100:5.0f}%" for q in range(1, cols + 1))
        print(f"  D{d}:  {row}")
    print("Column totals: " + ", ".join(
        f"Q{q} {sum(fill[(q, d)] for d in range(1, decks + 1)) / (cell_cap * decks) * 100:.0f}%"
        for q in range(1, cols + 1)))
    over = [(q, d) for (q, d), v in fill.items() if v > cell_cap]
    for q in range(1, cols + 1):
        tot = sum(fill[(q, d)] for d in range(1, decks + 1))
        if tot > cell_cap * decks:
            print(f"[OVER] column Q{q}: {tot:.0f} cm3 > {cell_cap * decks:.0f} cm3")
    for q, d in over:
        print(f"[warn] cell Q{q}/D{d} over capacity: {fill[(q, d)]:.0f} > {cell_cap:.0f} cm3")
    print(f"Outside cells: skin {other['skin']:.0f} cm3, spine {other['spine']:.0f} cm3, propulsion bay {other['bay']:.0f} cm3")
    if unassigned:
        print("[FAIL] unassigned modules:", unassigned)

    print("-- Separation rules --")
    def find(prefix):
        for n, loc in where.items():
            if n.startswith(prefix):
                return loc
        return None
    for r in lay["rule"]:
        a, b = find(r["a"]), find(r["b"])
        if not a or not b or not isinstance(a[0], int) or not isinstance(b[0], int):
            print(f"[FAIL] {r['why']}: module not placed in a cell")
            continue
        qa, qb = a[0], b[0]
        ring = min((qa - qb) % cols, (qb - qa) % cols)
        k = r["kind"]
        if k == "different_column":
            ok = qa != qb
        elif k == "different_deck":
            ok = not (set(a[1]) & set(b[1]))
        elif k == "opposite_column":
            ok = ring == 2
        elif k == "not_adjacent":
            ok = ring != 1
        else:
            ok = False
        print(f"[{'OK  ' if ok else 'FAIL'}] {r['why']}")


if __name__ == "__main__":
    main(*(sys.argv[1:3] or ["configs/12u_science.toml", "configs/12u_layout.toml"]))
