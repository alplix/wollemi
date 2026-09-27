"""Draw the EPS block diagram as SVG (electronics/eps_diagram.svg).

Usage: python electronics/eps_diagram.py
"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))
W, H = 1500, 900
out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="1500" font-family="sans-serif" font-size="14">',
       '<defs><marker id="a" markerWidth="10" markerHeight="8" refX="9" refY="4" orient="auto"><path d="M0,0 L10,4 L0,8 z" fill="#94a3b8"/></marker></defs>',
       f'<rect width="{W}" height="{H}" fill="#0f1420"/>',
       '<text x="20" y="30" fill="#e2e8f0" font-size="20">Wollemi EPS block diagram (draft v0): two main chains plus an independent survival chain</text>']


def box(x, y, w, h, title, lines=(), fill="#1e293b", stroke="#475569"):
    out.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="{stroke}"/>')
    out.append(f'<text x="{x + 10}" y="{y + 22}" fill="#f1f5f9" font-weight="bold">{title}</text>')
    for i, l in enumerate(lines):
        out.append(f'<text x="{x + 10}" y="{y + 42 + 18 * i}" fill="#94a3b8" font-size="12">{l}</text>')


def arrow(x1, y1, x2, y2, label="", color="#94a3b8"):
    out.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="2" marker-end="url(#a)"/>')
    if label:
        out.append(f'<text x="{(x1 + x2) / 2 + 4}" y="{(y1 + y2) / 2 - 6}" fill="{color}" font-size="12">{label}</text>')


# solar sources
box(20, 60, 250, 90, "Wing A: 3 panels (double-sided)", ["10s2p per panel, Vmp 24 V, ~24 W each", "cold Voc ~35 V"])
box(20, 380, 250, 90, "Wing B: 3 panels (double-sided)", ["same as wing A"])
box(20, 700, 250, 110, "Body survival string", ["4s2p, ~9.6 V, 1 A (dedicated cells)", "independent of wings and EPS-A/B"], "#1c2b1f", "#3f6212")

# EPS A / B / survival
box(340, 60, 330, 190, "EPS-A card", ["3 x buck MPPT (24 W in, ~4.6 A out at 5 V)", "pack A charger: CC-CV to 7.3 V, C/2 = 3.3 A",
                                         "no charge below 0 C, cell balancing", "ideal diode to bus A", "hardware OVP/UVP, telemetry MCU + CAN"])
box(340, 380, 330, 190, "EPS-B card", ["identical, wing B strings", "pack B charger", "ideal diode to bus B", "hardware OVP/UVP, telemetry MCU + CAN"])
box(340, 700, 330, 150, "Survival card", ["pack C charger (1 cell LiFePO4)", "ideal diode: string feeds supervisor directly", "3-inhibit burn-wire drivers x2",
                                          "no software in the protection path"], "#1c2b1f", "#3f6212")
arrow(270, 105, 340, 105, "3 x 24 W")
arrow(270, 425, 340, 425, "3 x 24 W")
arrow(270, 755, 340, 755)

# packs
box(760, 60, 250, 90, "Pack A (2S2P 26650, 42 Wh)", ["vault: Al box + poly-imide barrier", "own fuse and BMS"])
box(760, 380, 250, 90, "Pack B (2S2P 26650, 42 Wh)", ["separate deck and vault", "own fuse and BMS"])
box(760, 700, 250, 90, "Pack C (5 Wh, 1 cell)", ["survival, independent vault"], "#1c2b1f", "#3f6212")
arrow(670, 105, 760, 105)
arrow(760, 125, 670, 125, "discharge")
arrow(670, 425, 760, 425)
arrow(760, 445, 670, 445)
arrow(670, 755, 760, 755)

# buses
box(1100, 200, 380, 200, "Backplane buses", ["VBAT_A / VBAT_B planes (5.0..7.3 V)", "each card carries its own eFuse (trip 1.5x)",
                                              "SLOT_SEL + KILL_N: supervisor hardware kill", "CAN-FD A/B, PPS, SYNC"])
arrow(670, 160, 1100, 240, "bus A")
arrow(670, 480, 1100, 360, "bus B")
box(1100, 480, 380, 150, "Loads (cards and modules)", ["FC, comms, ADCS, payloads, computers", "burn mode: 50 W thruster (sunlit only)"])
arrow(1290, 400, 1290, 480)
box(1100, 700, 380, 150, "Supervisor (MSP430FR)", ["powered from bus A/B or survival path", "beacon, kill, watchdogs, key store"], "#1c2b1f", "#3f6212")
arrow(670, 790, 1100, 790, "survival bus", "#84cc16")
arrow(1290, 630, 1290, 700, "control", "#94a3b8")
out.append("</svg>")
open(os.path.join(HERE, "eps_diagram.svg"), "w", encoding="utf-8").write("\n".join(out))
print("wrote electronics/eps_diagram.svg")
