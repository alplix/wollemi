"""Generate the Ginkgo card template (KiCad PCB) and the pinout tables from card_pinout.toml.

Usage: python electronics/gen_card.py
Writes electronics/kicad/ginkgo_card_template.kicad_pcb and electronics/pinout.md, then runs
kicad-cli DRC if it is installed.
"""
import os
import subprocess
import tomllib
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD_CLI = os.path.expanduser("~/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe")
pin = tomllib.load(open(os.path.join(HERE, "card_pinout.toml"), "rb"))
card = pin["card"]
W, H = card["size"]
NX, NY = card["notch"]


def u():
    return str(uuid.uuid4())


def nets_of(*conns):
    names = []
    for c in conns:
        for a, b in pin[c]["pairs"]:
            for n in (a, b):
                if n not in names:
                    names.append(n)
    return {n: i + 1 for i, n in enumerate(names)}


NETS = nets_of("gkp", "gkd")


def pads(conn, pitch=None, row=3.0):
    pitch = pitch or card.get("connector_pitch", 0.8)
    """Pad expressions for a 2-row connector laid out along y (row A at -row/2, row B at +row/2)."""
    out = []
    n = len(pin[conn]["pairs"])
    y0 = -(n - 1) * pitch / 2
    for k, (a, b) in enumerate(pin[conn]["pairs"]):
        y = y0 + k * pitch
        for j, (name, x) in enumerate(((a, -row / 2), (b, row / 2))):
            num = 2 * k + 1 + j
            net = NETS[name]
            out.append(f'    (pad "{num}" smd rect (at {x:.3f} {y:.3f}) (size 1.4 0.5) '
                       f'(layers "F.Cu" "F.Mask" "F.Paste") (net {net} "{name}") (uuid "{u()}"))')
    return out, (n * pitch + 2.0)


def footprint(ref, value, x, y, conn, label):
    pd, length = pads(conn)
    lines = [f'  (footprint "Ginkgo:{value}_placeholder" (layer "F.Cu") (uuid "{u()}") (at {x} {y})',
             f'    (property "Reference" "{ref}" (at 0 {-length / 2 - 2:.2f} 0) (layer "F.SilkS") (uuid "{u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))',
             f'    (property "Value" "{value}" (at 0 {length / 2 + 2:.2f} 0) (layer "F.Fab") (uuid "{u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))',
             '    (attr smd)',
             f'    (fp_rect (start -3.2 {-length / 2:.2f}) (end 3.2 {length / 2:.2f}) (stroke (width 0.05) (type default)) '
             f'(fill no) (layer "F.CrtYd") (uuid "{u()}"))',
             f'    (fp_text user "{label}" (at 0 0 90) (layer "F.Fab") (uuid "{u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))']
    lines += pd
    lines.append("  )")
    return "\n".join(lines)


def hole(x, y, d):
    return (f'  (footprint "MountingHole:MountingHole_2.7mm_M2.5" (layer "F.Cu") (uuid "{u()}") (at {x} {y})\n'
            f'    (property "Reference" "H" (at 0 -3 0) (layer "F.SilkS") (hide yes) (uuid "{u()}") '
            f'(effects (font (size 1 1) (thickness 0.15))))\n'
            f'    (property "Value" "M2.5" (at 0 3 0) (layer "F.Fab") (hide yes) (uuid "{u()}") '
            f'(effects (font (size 1 1) (thickness 0.15))))\n'
            f'    (attr exclude_from_pos_files exclude_from_bom)\n'
            f'    (pad "" np_thru_hole circle (at 0 0) (size {d} {d}) (drill {d}) (layers "*.Cu" "*.Mask") (uuid "{u()}"))\n  )')


def line(x1, y1, x2, y2, layer="Edge.Cuts", w=0.1):
    return (f'  (gr_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width {w}) (type default)) '
            f'(layer "{layer}") (uuid "{u()}"))')


def text(s, x, y, layer="F.SilkS", size=1.2):
    return (f'  (gr_text "{s}" (at {x} {y} 0) (layer "{layer}") (uuid "{u()}") '
            f'(effects (font (size {size} {size}) (thickness 0.18)) (justify left)))')


def build():
    # KiCad y grows downward; origin at the card's top-left corner; notch at the bottom-left (spine corner).
    rr = card["rail_relief"]
    pts = [(0, 0), (W - rr, 0), (W - rr, rr), (W, rr), (W, H), (NX, H), (NX, H - NY), (0, H - NY)]
    L = ['(kicad_pcb', '  (version 20241229)', '  (generator "ginkgo_gen_card")', '  (generator_version "1.0")',
         f'  (general (thickness {card["thickness"]}) (legacy_teardrops no))', '  (paper "A4")',
         '  (layers',
         '    (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (2 "B.Cu" signal)',
         '    (9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive") (13 "F.Paste" user) (15 "B.Paste" user)',
         '    (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen") (1 "F.Mask" user) (3 "B.Mask" user)',
         '    (17 "Dwgs.User" user "User.Drawings") (19 "Cmts.User" user "User.Comments")',
         '    (21 "Eco1.User" user "User.Eco1") (23 "Eco2.User" user "User.Eco2") (25 "Edge.Cuts" user) (27 "Margin" user)',
         '    (31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard") (35 "F.Fab" user) (33 "B.Fab" user)',
         '  )',
         '  (setup', '    (pad_to_mask_clearance 0)', '  )', '  (net 0 "")']
    for n, i in NETS.items():
        L.append(f'  (net {i} "{n}")')
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        L.append(line(x1, y1, x2, y2))
    for x, y in ((4, 4), (W - 4, 4), (W - 4, H - 4), (NX + 4, H - 4)):
        L.append(hole(x, y, card["hole_d"]))
    L.append(footprint("J1", "GK-P", 8.0, 28.0, "gkp", "GK-P 2x30"))
    L.append(footprint("J2", "GK-D", 8.0, 62.0, "gkd", "GK-D 2x15"))
    g = card["guide_keepout"]
    for name, poly in (("guide keepout top", [(0, 0), (W, 0), (W, g), (0, g)]),
                       ("guide keepout right", [(W - g, g), (W, g), (W, H), (W - g, H)])):
        pts_s = " ".join(f"(xy {x} {y})" for x, y in poly)
        L.append(f'  (zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (uuid "{u()}") (name "{name}") '
                 f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
                 f'(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) '
                 f'(polygon (pts {pts_s})))')
    L.append(text("GINKGO CARD v0", 26, 14))
    L.append(text("100 x 100, spine notch 20 x 20 (bottom-left)", 26, 18.5, size=0.9))
    L.append(text("SPINE SIDE", 1.5, H - NY - 4, size=0.9))
    L.append(text("OUTER: guides 3 mm, rail relief 8x8", 50, 14, size=0.9))
    L.append(")")
    return "\n".join(L) + "\n"


def write_pinout_md():
    out = ["# Card connector pinouts (generated)", "",
           "Generated from `electronics/card_pinout.toml` by `electronics/gen_card.py`; do not edit by hand.", ""]
    for c in ("gkp", "gkd"):
        d = pin[c]
        out += [f"## {d['title']}", "", "| Pin pair | Row A (odd) | Row B (even) |", "|---|---|---|"]
        for k, (a, b) in enumerate(d["pairs"], 1):
            out.append(f"| {k} (pins {2 * k - 1}, {2 * k}) | {a} | {b} |")
        cnt = {}
        for a, b in d["pairs"]:
            for n in (a, b):
                key = "VBAT" if n.startswith("VBAT") else n
                cnt[key] = cnt.get(key, 0) + 1
        out += ["", "Pin counts: " + ", ".join(f"{k} x{v}" for k, v in sorted(cnt.items())), ""]
    open(os.path.join(HERE, "pinout.md"), "w", encoding="utf-8").write("\n".join(out) + "\n")


PRO = """{
  "board": {
    "design_settings": {
      "rule_severities": {
        "lib_footprint_issues": "ignore",
        "lib_footprint_mismatch": "ignore",
        "unconnected_items": "ignore"
      }
    }
  },
  "meta": { "filename": "ginkgo_card_template.kicad_pro", "version": 3 }
}
"""


def main():
    path = os.path.join(HERE, "kicad", "ginkgo_card_template.kicad_pcb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(build())
    write_pinout_md()
    # template: no routing yet, so unconnected items and generated-library warnings are silenced on purpose;
    # cards derived from the template must re-enable them.
    open(os.path.join(os.path.dirname(path), "ginkgo_card_template.kicad_pro"), "w", encoding="utf-8").write(PRO)
    print(f"Wrote {path} and pinout.md; nets: {len(NETS)}")
    if os.path.exists(KICAD_CLI):
        rep = os.path.join(HERE, "kicad", "drc_report.txt")
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--output", rep, "--severity-all", path], capture_output=True, text=True)
        print("kicad-cli DRC exit code:", r.returncode)
        print((r.stdout + r.stderr).strip()[:600])
        if os.path.exists(rep):
            print(open(rep, encoding="utf-8").read()[:1800])


if __name__ == "__main__":
    main()
