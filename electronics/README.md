# Electronics

| File | Role |
|---|---|
| `card_pinout.toml` | Single source for the WL-P and WL-D connector pinouts and the card outline |
| `gen_card.py` | Generates the KiCad card template and `pinout.md`, runs `kicad-cli` DRC (needs KiCad 10) |
| `kicad/wollemi_card_template.kicad_pcb` | 100 x 100 mm card with the 20 x 20 mm spine notch, 4 x M2.5 holes, edge-guide keep-outs, WL-P and WL-D connector placeholders with every net assigned |
| `kicad/wollemi_card_template.svg`, `_top.png` | Renders |
| `gen_backplane.py` | Generates the 15-slot passive backplane strip (one per column), runs `kicad-cli` DRC |
| `kicad/wollemi_backplane_strip.kicad_pcb` | Passive backplane strip: 15 card slots, WL-P/WL-D routing per chain, DRC clean |
| `gen_eps_card.py` | Generates function-block floor plans for the EPS-A/EPS-B and survival cards on the real card outline (`docs/eps-card.md`), runs `kicad-cli` DRC |
| `kicad/wollemi_eps_card.kicad_pcb`, `wollemi_survival_card.kicad_pcb` | Floor plans only: labelled placeholder blocks proving the partition fits the card, DRC clean; not a routed schematic |
| `eps_diagram.py` | Generates the EPS block diagram `eps_diagram.svg` |
| `pinout.md` | Generated pin tables |

```
python electronics/gen_card.py
python electronics/gen_backplane.py
python electronics/gen_eps_card.py
```

The card template has no routing yet: `unconnected_items` and generated-library warnings are silenced in its project file on purpose. Cards derived
from it must re-enable them. Connector footprints are placeholders (2-row, 1.27 mm pitch pads); replace with the vendor footprint once the
connector family is chosen (`docs/electrical-interface.md`).

Next: choose real parts and capture a routed schematic for the EPS and survival cards (`docs/eps-card.md`); a first functional (non-EPS) card schematic.
