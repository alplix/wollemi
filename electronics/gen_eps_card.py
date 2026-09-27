"""Generate EPS card floor plans (KiCad PCB) on the standard Wollemi card outline: block-level placement of the
functions specified in docs/eps-card.md, proving they physically fit the 100 x 100 mm notched card alongside the
WL-P connector, DRC clean. This is a floor plan, not a schematic: blocks are labelled placeholders (no pads, no
nets, no part numbers), exactly like the WL-P/WL-D connector placeholders already used for the generic template
and the backplane strip. Real schematic capture (verified part numbers, a routed netlist) is still open work.

Usage: python electronics/gen_eps_card.py
Writes electronics/kicad/wollemi_eps_card.kicad_pcb (EPS-A / EPS-B, identical layout) and
electronics/kicad/wollemi_survival_card.kicad_pcb, then runs kicad-cli DRC on both if it is installed.
"""
import os
import subprocess

import gen_card as gc

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD_CLI = gc.KICAD_CLI
card, W, H, NX, NY = gc.card, gc.W, gc.H, gc.NX, gc.NY


def u():
    return gc.u()


def block(ref, value, x, y, w, h, label):
    """A labelled placeholder block: courtyard outline + silkscreen reference/value + a fab-layer function label.
    No pads and no nets -- this is a floor-plan placeholder, not a verified part."""
    lines = [f'  (footprint "Wollemi:{value}_placeholder" (layer "F.Cu") (uuid "{u()}") (at {x} {y})',
             f'    (property "Reference" "{ref}" (at 0 {-h / 2 - 1.6:.2f} 0) (layer "F.SilkS") (uuid "{u()}") '
             f'(effects (font (size 1 1) (thickness 0.15))))',
             f'    (property "Value" "{value}" (at 0 {h / 2 + 1.6:.2f} 0) (layer "F.Fab") (uuid "{u()}") '
             f'(effects (font (size 0.9 0.9) (thickness 0.13))))',
             '    (attr exclude_from_pos_files exclude_from_bom)',
             f'    (fp_rect (start {-w / 2:.2f} {-h / 2:.2f}) (end {w / 2:.2f} {h / 2:.2f}) (stroke (width 0.15) (type default)) '
             f'(fill no) (layer "F.SilkS") (uuid "{u()}"))',
             f'    (fp_rect (start {-w / 2:.2f} {-h / 2:.2f}) (end {w / 2:.2f} {h / 2:.2f}) (stroke (width 0.05) (type default)) '
             f'(fill no) (layer "F.CrtYd") (uuid "{u()}"))',
             f'    (fp_text user "{label}" (at 0 0 0) (layer "F.Fab") (uuid "{u()}") '
             f'(effects (font (size 0.9 0.9) (thickness 0.15))))',
             '  )']
    return "\n".join(lines)


def outline_and_frame(title):
    rr = card["rail_relief"]
    pts = [(0, 0), (W - rr, 0), (W - rr, rr), (W, rr), (W, H), (NX, H), (NX, H - NY), (0, H - NY)]
    L = ['(kicad_pcb', '  (version 20241229)', '  (generator "wollemi_gen_eps_card")', '  (generator_version "1.0")',
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
    for n, i in gc.NETS.items():
        L.append(f'  (net {i} "{n}")')
    for (x1, y1), (x2, y2) in zip(pts, pts[1:] + pts[:1]):
        L.append(gc.line(x1, y1, x2, y2))
    for x, y in ((4, 4), (W - 4, 4), (W - 4, H - 4), (NX + 4, H - 4)):
        L.append(gc.hole(x, y, card["hole_d"]))
    g = card["guide_keepout"]
    for name, poly in (("guide keepout top", [(0, 0), (W, 0), (W, g), (0, g)]),
                       ("guide keepout right", [(W - g, g), (W, g), (W, H), (W - g, H)])):
        pts_s = " ".join(f"(xy {x} {y})" for x, y in poly)
        L.append(f'  (zone (net 0) (net_name "") (layers "F.Cu" "In1.Cu" "In2.Cu" "B.Cu") (uuid "{u()}") (name "{name}") '
                 f'(hatch edge 0.5) (connect_pads (clearance 0)) (min_thickness 0.25) '
                 f'(keepout (tracks not_allowed) (vias not_allowed) (pads allowed) (copperpour not_allowed) (footprints allowed)) '
                 f'(polygon (pts {pts_s})))')
    L.append(gc.text(title, 30, 4.5, size=1.0))
    L.append(gc.text("100x100mm, notch 20x20; floor plan, no schematic yet", 30, 7.5, size=0.8))
    L.append(gc.text("SPINE SIDE", 1.5, H - NY - 4, size=0.9))
    return L


def build_eps():
    L = outline_and_frame("WOLLEMI EPS-A / EPS-B CARD v0 (floor plan)")
    L.append(gc.footprint("J1", "WL-P", 8.0, 30.0, "gkp", "WL-P 2x30 (control + CAN-FD)"))
    # three MPPT buck channels (10s2p panel string each, 8-40V in, ~24W)
    for i, y in enumerate((22, 46, 70)):
        L.append(block(f"U{i + 1}", "MPPT_BUCK", 40, y, 26, 18, f"MPPT ch{i + 1}: 8-40V->6.4V, ~24W"))
    L.append(block("U4", "CHG_BAL", 68, 22, 28, 20, "Pack charger + balancer: CC-CV 7.3V, 3.3A"))
    L.append(block("U5", "IDEAL_DIODE", 68, 48, 20, 14, "Ideal diode OR-ing to bus"))
    L.append(block("U6", "EFUSE_OVPUVP", 68, 66, 24, 16, "eFuse + OVP/UVP, hardware only"))
    L.append(block("U7", "TELEM_MCU", 40, 92, 22, 14, "Telemetry MCU: V/I/T, CAN-FD"))
    L.append(")")
    return "\n".join(L) + "\n"


def build_survival():
    L = outline_and_frame("WOLLEMI SURVIVAL CARD v0 (floor plan)")
    L.append(gc.footprint("J1", "WL-P", 8.0, 30.0, "gkp", "WL-P 2x30 (control + CAN-FD)"))
    L.append(block("U1", "CHG_C", 45, 22, 26, 18, "Pack C charger: 4s2p ~9.6V, 1A"))
    L.append(block("U2", "DIRECT_PATH", 45, 46, 22, 16, "Direct string path -> supervisor (sun-only)"))
    L.append(block("U3", "IDEAL_DIODE", 75, 22, 18, 14, "Ideal diode"))
    L.append(block("U4", "BURNWIRE1", 45, 68, 24, 16, "Burn-wire driver 1: 3 inhibits (timer, supervisor, sep-sw)"))
    L.append(block("U5", "BURNWIRE2", 45, 90, 24, 16, "Burn-wire driver 2: 3 inhibits (same)"))
    L.append(block("U6", "TELEM_MCU", 78, 46, 20, 14, "Telemetry MCU"))
    L.append(")")
    return "\n".join(L) + "\n"


def main():
    outdir = os.path.join(HERE, "kicad")
    os.makedirs(outdir, exist_ok=True)
    for name, builder in (("wollemi_eps_card", build_eps), ("wollemi_survival_card", build_survival)):
        path = os.path.join(outdir, f"{name}.kicad_pcb")
        open(path, "w", encoding="utf-8").write(builder())
        open(os.path.join(outdir, f"{name}.kicad_pro"), "w", encoding="utf-8").write(
            gc.PRO.replace("wollemi_card_template", name))
        print(f"Wrote {path}")
        if os.path.exists(KICAD_CLI):
            rep = os.path.join(outdir, f"{name}_drc_report.txt")
            r = subprocess.run([KICAD_CLI, "pcb", "drc", "--output", rep, "--severity-all", path], capture_output=True, text=True)
            print("kicad-cli DRC exit code:", r.returncode)
            print((r.stdout + r.stderr).strip()[:400])
            if os.path.exists(rep):
                txt = open(rep, encoding="utf-8").read()
                found = next((l for l in txt.splitlines() if "Found" in l and "violations" in l), "")
                print(found)


if __name__ == "__main__":
    main()
