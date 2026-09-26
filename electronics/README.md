# Electronics

| File | Role |
|---|---|
| `card_pinout.toml` | Single source for the GK-P and GK-D connector pinouts and the card outline |
| `gen_card.py` | Generates the KiCad card template and `pinout.md`, runs `kicad-cli` DRC (needs KiCad 10) |
| `kicad/ginkgo_card_template.kicad_pcb` | 100 x 100 mm card with the 20 x 20 mm spine notch, 4 x M2.5 holes, edge-guide keep-outs, GK-P and GK-D connector placeholders with every net assigned |
| `kicad/ginkgo_card_template.svg`, `_top.png` | Renders |
| `pinout.md` | Generated pin tables |

```
python electronics/gen_card.py
```

The template has no routing yet: `unconnected_items` and generated-library warnings are silenced in its project file on purpose. Cards derived
from it must re-enable them. Connector footprints are placeholders (2-row, 1.27 mm pitch pads); replace with the vendor footprint once the
connector family is chosen (`docs/electrical-interface.md`).

Next: backplane board, EPS card (`sim/eps_design.py` numbers), first functional card schematic.
