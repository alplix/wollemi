"""Reconcile configs/12u_layout.toml with the real geometric packing.

Usage: python mechanical/reconcile.py
Runs pack.py; every module the packer had to move to another deck gets its layout entry updated to the actual decks, and the loop repeats
until nothing moves. Modules that fail to fit at all are listed (they need a human decision: shrink, swap column, or drop).
"""
import json
import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
LAYOUT = os.path.join(ROOT, "configs", "12u_layout.toml")


def main():
    for it in range(6):
        subprocess.run([sys.executable, os.path.join(HERE, "pack.py")], capture_output=True, cwd=ROOT)
        d = json.load(open(os.path.join(HERE, "out", "placement.json")))
        if d["failed"]:
            print("FAILED to fit:", d["failed"])
            return 1
        rel = [p for p in d["placed"] if p["name"] in d["relocated"]]
        if not rel:
            print(f"iteration {it}: everything placed inside its planned decks")
            return 0
        deck_h = d["inner_z"] / 3
        text = open(LAYOUT, encoding="utf-8").read()
        for r in rel:
            z0, z1 = r["min"][2] - 3.0, r["max"][2] - 3.0
            d1, d2 = int(z0 // deck_h) + 1, int((z1 - 0.01) // deck_h) + 1
            at = f"Q{r['col']}/{d1}" if d1 == d2 else f"Q{r['col']}/{d1}-{d2}"
            entries = re.findall(r'match = "([^"]+)"\nat = "([^"]+)"', text)
            best = max((e for e in entries if r["name"].startswith(e[0])), key=lambda e: len(e[0]))
            text = text.replace(f'match = "{best[0]}"\nat = "{best[1]}"', f'match = "{best[0]}"\nat = "{at}"')
            print(f"  {best[0][:48]}: {best[1]} -> {at}")
        open(LAYOUT, "w", encoding="utf-8").write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
