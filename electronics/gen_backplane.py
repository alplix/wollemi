"""Generate the Ginkgo column backplane strip (KiCad) from card_pinout.toml.

Usage: python electronics/gen_backplane.py
Writes electronics/kicad/ginkgo_backplane_strip.kicad_pcb (+ project file) and runs kicad-cli DRC with zone refill.

Strip: 90 x 330 mm, 6 layers (F.Cu pads, In1 GND plane, In2 signal chains, In3 VBAT_A plane, In4 VBAT_B plane, B.Cu GND).
15 GK-P receptacle placeholders at a 20 mm pitch plus one hub receptacle. Bussed signals are daisy-chained between the
same pins of consecutive slots on In2 (row A and row B vias are offset by 0.7 mm so the chains never touch other vias).
GND and the battery rails reach planes through vias; SLOT_ID[3:0] is strapped to GND per slot; GK-D pads are left for a cable header.
"""
import os
import subprocess
import tomllib
import uuid

HERE = os.path.dirname(os.path.abspath(__file__))
KICAD_CLI = os.path.expanduser("~/AppData/Local/Programs/KiCad/10.0/bin/kicad-cli.exe")
pin = tomllib.load(open(os.path.join(HERE, "card_pinout.toml"), "rb"))
PITCH = pin["card"].get("connector_pitch", 1.27)

BOARD_W, BOARD_L = 90.0, 330.0     # 330 mm fits the 334.5 mm interior height of the 12U
SLOTS = 15
SLOT_PITCH = 20.0
Y0 = 30.0
HUB_Y = 10.0
ROW = 3.0                      # distance between the two contact rows
VIA_OFF_Y = 3.3               # via distance from the connector centre line (beyond the pads)
STAGGER = 0.32                # x offset of row A / row B vias (window 0.275..0.36 for 0.5 mm vias at 1.27 pitch)
J1_X, J2_X = 28.0, 62.0       # connector centres along the strip (card y coordinates)

CHAIN = {"CAN_A_H", "CAN_A_L", "CAN_B_H", "CAN_B_L", "PPS_P", "PPS_N", "SYNC_P", "SYNC_N",
         "SLOT_SEL0", "SLOT_SEL1", "SLOT_SEL2", "SLOT_SEL3", "KILL_N", "FAULT_N", "RESET_N", "I2C_SCL", "I2C_SDA"}
PLANE_NETS = {"GND", "VBAT_A", "VBAT_B"}


def u():
    return str(uuid.uuid4())


class Nets:
    def __init__(self):
        self.ids = {"": 0}

    def get(self, name):
        if name not in self.ids:
            self.ids[name] = len(self.ids)
        return self.ids[name]


nets = Nets()


def pad_positions(conn, cx):
    """Yield (pair index, row, x offset) for a connector of the pinout, rows 0 = A and 1 = B."""
    n = len(pin[conn]["pairs"])
    for j in range(n):
        x = cx + (j - (n - 1) / 2) * PITCH
        yield j, x


def build():
    out, tracks = [], []
    slots = [("HUB", HUB_Y)] + [(f"S{k:02d}", Y0 + SLOT_PITCH * k) for k in range(SLOTS)]
    # per-net chain memory: net -> list of (y, x, row) via positions in slot order
    chains = {}
    fp = []
    vias = []
    used_vias = set()

    def add_via(x, y, net):
        key = (round(x, 3), round(y, 3))
        if key in used_vias:
            return
        used_vias.add(key)
        vias.append(f'  (via (at {x:.3f} {y:.3f}) (size 0.5) (drill 0.25) (layers "F.Cu" "B.Cu") (net {nets.get(net)}) (uuid "{u()}"))')

    def add_track(x1, y1, x2, y2, layer, net, w=0.2):
        tracks.append(f'  (segment (start {x1:.3f} {y1:.3f}) (end {x2:.3f} {y2:.3f}) (width {w}) (layer "{layer}") '
                      f'(net {nets.get(net)}) (uuid "{u()}"))')

    for sname, sy in slots:
        for conn, cx, tag in (("gkp", J1_X, "P"), ("gkd", J2_X, "D")):
            padlines = []
            k = int(sname[1:]) if sname != "HUB" else -1
            for j, x in pad_positions(conn, cx):
                for row, (rname_sel) in enumerate(("A", "B")):
                    signal = pin[conn]["pairs"][j][row]
                    num = 2 * j + 1 + row
                    ypad = sy - ROW / 2 if row == 0 else sy + ROW / 2
                    # decide the net name for this pad
                    if tag == "D" or signal in ("RSV", "SWD_CLK", "SWD_IO", "NRST_DBG", "VREF", "UART_TX", "UART_RX"):
                        net = f"{signal}_{sname}_{tag}{num}"           # not bussed: unique single-pad net (cable, debug, reserve)
                    elif signal.startswith("SLOT_ID"):
                        bit = int(signal[-1])
                        net = "GND" if (k >= 0 and not (k >> bit) & 1) else f"{signal}_{sname}"
                    else:
                        net = signal
                    padlines.append(f'    (pad "{num}" smd rect (at {x - cx:.3f} {ypad - sy:.3f}) (size 0.5 1.4) '
                                    f'(layers "F.Cu" "F.Mask" "F.Paste") (net {nets.get(net)} "{net}") (uuid "{u()}"))')
                    # via, stub and chain bookkeeping
                    if net in PLANE_NETS or net in CHAIN:
                        vx = x - STAGGER if row == 0 else x + STAGGER
                        vy = sy - VIA_OFF_Y if row == 0 else sy + VIA_OFF_Y
                        add_via(vx, vy, net)
                        add_track(x, ypad, vx, vy, "F.Cu", net, 0.2)
                        if net in CHAIN:
                            chains.setdefault((net, row, j), []).append((sy, vx, vy))
            length = len(pin[conn]["pairs"]) * PITCH + 2.0
            fp.append(f'  (footprint "Ginkgo:GK-{tag}_backplane_placeholder" (layer "F.Cu") (uuid "{u()}") (at {cx} {sy})\n'
                      f'    (property "Reference" "J_{sname}_{tag}" (at 0 {-ROW / 2 - 2.6:.1f} 0) (layer "F.SilkS") (uuid "{u()}") '
                      f'(effects (font (size 0.8 0.8) (thickness 0.12))))\n'
                      f'    (property "Value" "GK-{tag}" (at 0 {ROW / 2 + 2.6:.1f} 0) (layer "F.Fab") (uuid "{u()}") '
                      f'(effects (font (size 0.8 0.8) (thickness 0.12))))\n'
                      f'    (attr smd)\n'
                      f'    (fp_rect (start {-length / 2:.2f} -2.6) (end {length / 2:.2f} 2.6) (stroke (width 0.05) (type default)) '
                      f'(fill no) (layer "F.CrtYd") (uuid "{u()}"))\n' + "\n".join(padlines) + "\n  )")

    # chain tracks between consecutive slots on In2.Cu
    for (net, row, j), pts in chains.items():
        pts.sort()
        for (y1, x1, vy1), (y2, x2, vy2) in zip(pts, pts[1:]):
            add_track(x1, vy1, x2, vy2, "In2.Cu", net, 0.2)

    # zones (planes)
    def zone(layer, net, name):
        pts = [(0.5, 0.5), (BOARD_W - 0.5, 0.5), (BOARD_W - 0.5, BOARD_L - 0.5), (0.5, BOARD_L - 0.5)]
        ps = " ".join(f"(xy {x} {y})" for x, y in pts)
        return (f'  (zone (net {nets.get(net)}) (net_name "{net}") (layer "{layer}") (uuid "{u()}") (name "{name}") '
                f'(hatch edge 0.5) (connect_pads (clearance 0.25)) (min_thickness 0.2) (filled_areas_thickness no) '
                f'(fill yes (thermal_gap 0.25) (thermal_bridge_width 0.3)) (polygon (pts {ps})))')

    zones = [zone("In1.Cu", "GND", "GND plane"), zone("In3.Cu", "VBAT_A", "VBAT_A plane"),
             zone("In4.Cu", "VBAT_B", "VBAT_B plane"), zone("B.Cu", "GND", "GND back")]

    holes = []
    for x, y in ((5, 5), (BOARD_W - 5, 5), (5, BOARD_L - 5), (BOARD_W - 5, BOARD_L - 5),
                 (5, BOARD_L / 2), (BOARD_W - 5, BOARD_L / 2)):
        holes.append(f'  (footprint "MountingHole:MountingHole_2.7mm_M2.5" (layer "F.Cu") (uuid "{u()}") (at {x} {y})\n'
                     f'    (property "Reference" "H" (at 0 -3 0) (layer "F.SilkS") (hide yes) (uuid "{u()}") '
                     f'(effects (font (size 1 1) (thickness 0.15))))\n'
                     f'    (property "Value" "M2.5" (at 0 3 0) (layer "F.Fab") (hide yes) (uuid "{u()}") '
                     f'(effects (font (size 1 1) (thickness 0.15))))\n'
                     f'    (attr exclude_from_pos_files exclude_from_bom)\n'
                     f'    (pad "" np_thru_hole circle (at 0 0) (size 2.7 2.7) (drill 2.7) (layers "*.Cu" "*.Mask") (uuid "{u()}"))\n  )')

    edge = []
    corners = [(0, 0), (BOARD_W, 0), (BOARD_W, BOARD_L), (0, BOARD_L)]
    for (x1, y1), (x2, y2) in zip(corners, corners[1:] + corners[:1]):
        edge.append(f'  (gr_line (start {x1} {y1}) (end {x2} {y2}) (stroke (width 0.1) (type default)) (layer "Edge.Cuts") (uuid "{u()}"))')
    label = (f'  (gr_text "GINKGO BACKPLANE STRIP v0 - 15 slots, 20 mm pitch" (at 6 {BOARD_L - 12} 90) (layer "F.SilkS") '
             f'(uuid "{u()}") (effects (font (size 1.2 1.2) (thickness 0.18)) (justify left)))')

    head = ['(kicad_pcb', '  (version 20241229)', '  (generator "ginkgo_gen_backplane")', '  (generator_version "1.0")',
            '  (general (thickness 1.6) (legacy_teardrops no))', '  (paper "A3")',
            '  (layers',
            '    (0 "F.Cu" signal) (4 "In1.Cu" signal) (6 "In2.Cu" signal) (8 "In3.Cu" signal) (10 "In4.Cu" signal) (2 "B.Cu" signal)',
            '    (9 "F.Adhes" user "F.Adhesive") (11 "B.Adhes" user "B.Adhesive") (13 "F.Paste" user) (15 "B.Paste" user)',
            '    (5 "F.SilkS" user "F.Silkscreen") (7 "B.SilkS" user "B.Silkscreen") (1 "F.Mask" user) (3 "B.Mask" user)',
            '    (17 "Dwgs.User" user "User.Drawings") (19 "Cmts.User" user "User.Comments")',
            '    (25 "Edge.Cuts" user) (27 "Margin" user)',
            '    (31 "F.CrtYd" user "F.Courtyard") (29 "B.CrtYd" user "B.Courtyard") (35 "F.Fab" user) (33 "B.Fab" user)',
            '  )',
            '  (setup', '    (pad_to_mask_clearance 0)', '  )']
    netlines = [f'  (net {i} "{n}")' for n, i in sorted(nets.ids.items(), key=lambda kv: kv[1])]
    body = head + netlines + edge + holes + fp + vias + tracks + zones + [label, ")"]
    return "\n".join(body) + "\n"


PRO = """{
  "board": {
    "design_settings": {
      "rules": { "min_clearance": 0.15, "min_track_width": 0.15, "min_via_diameter": 0.5, "min_through_hole_diameter": 0.25 },
      "rule_severities": {
        "lib_footprint_issues": "ignore",
        "lib_footprint_mismatch": "ignore",
        "unconnected_items": "warning"
      }
    }
  },
  "meta": { "filename": "ginkgo_backplane_strip.kicad_pro", "version": 3 }
}
"""


def main():
    path = os.path.join(HERE, "kicad", "ginkgo_backplane_strip.kicad_pcb")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    text = build()
    open(path, "w", encoding="utf-8").write(text)
    open(os.path.join(os.path.dirname(path), "ginkgo_backplane_strip.kicad_pro"), "w", encoding="utf-8").write(PRO)
    print(f"Wrote {path}: nets {len(nets.ids)}, {text.count('(segment')} tracks, {text.count('(via ')} vias")
    if os.path.exists(KICAD_CLI):
        rep = os.path.join(HERE, "kicad", "backplane_drc_report.txt")
        r = subprocess.run([KICAD_CLI, "pcb", "drc", "--refill-zones", "--all-track-errors", "--output", rep, "--severity-all", path],
                           capture_output=True, text=True)
        print("kicad-cli DRC exit code:", r.returncode, (r.stdout + r.stderr).strip()[:200])
        if os.path.exists(rep):
            txt = open(rep, encoding="utf-8", errors="ignore").read()
            import re
            kinds = re.findall(r"^\[(\w+)\]", txt, flags=re.M)
            from collections import Counter
            print("violation kinds:", dict(Counter(kinds)))
            print(txt[:1200])


if __name__ == "__main__":
    main()
