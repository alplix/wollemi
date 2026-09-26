# Mechanical model (parametric CAD)

Everything is generated from the TOML configs; nothing is hand-drawn.

| File | Role |
|---|---|
| `../configs/12u_geometry.toml` | Frame, wings and a bounding box (mm) for every module; flags `fixed`, `shape = "cyl"`, `notched`, `end = "nadir"/"zenith"`, `align = "top"` |
| `pack.py` | Voxel packing (2.5 mm) of every box into its assigned column/deck; maximum-contact placement, disk footprints for cylinders, corner-notched card format; writes `out/placement.json` |
| `ginkgo_cad.py` | build123d / OpenCascade assembly: rails, walls, plates with windows, bulkheads, spine, modules, wings, antennas, thruster nozzle; exact boolean interference check; centre of mass and inertia; STEP, STL, renders, BOM |

```
pip install build123d            # OpenCascade based CAD kernel (also pulls numpy, scipy, pillow)
python mechanical/pack.py        # packing report
python mechanical/ginkgo_cad.py  # full assembly, checks, exports into mechanical/out/
```

Outputs in `out/`: `ginkgo_12u_stowed.step/.stl`, `ginkgo_12u_deployed.step/.stl`, `render_*.png`
(stowed, deployed, interior, cutaway, nadir), `bom_geometry.csv`, `placement.json`.

## What the geometry taught us

- **Volume was not the problem, footprint was.** The 20 x 20 mm spine notch at every column's inner corner
  stops any 90 x 90 mm or 100 x 100 mm board. Fix: the **Ginkgo card format**, a board with its own
  20 x 20 mm corner cut-out that seats against the spine.
- A 100 mm-wide telescope tube only fits as a **round** Ø95 mm tube; a square 100 mm box does not fit.
  The 90 mm aperture therefore became ~85 mm (about 5 m ground sampling at 700 km).
- Modules with windows (wide-field camera, thermal IR, lightning) must sit against the nadir plate;
  the star tracker, GNSS, boom and antenna deployer against the zenith plate (`end` flag).
- The propulsion column (Q2) is vertically almost full: cameras + ADCS + tank + star tracker = ~333 of
  334.5 mm. Any growth there needs a design decision.
- Stowed wing stack: 3 x 2.1 mm = 6.3 mm, inside the 6.5 mm protrusion allowance (2.2 mm panels would fail).
- Thruster plume at 15 degrees half-angle just reaches the tip of wing B (last ~30 mm of panel 3);
  a wider plume (Hall thruster) would impinge on panels 2-3. Mitigation: gridded ion thruster, shorter
  wing B, or a canted nozzle.

- **Thruster line vs centre of mass:** with the nozzle in a column the lever arm was ~70 mm (about 70 uN m at 1.1 mN). The propulsion module is now a bay on the -X face centre
  line (keep-out in Q2/Q3) with a fixed cant of about 8.6/2.9 deg through the CoM; that cant also clears the exhaust from wing B. See `docs/adcs.md`.
- **Wings must be double-sided:** with the sun on +Y in a dawn-dusk orbit, one single-sided wing faces away; the power scenarios assume cells on both faces.

## Limits (be honest)

- Modules are bounding boxes (cylinder for telescope and tank), not vendor CAD; sizes are estimates.
- No fasteners, harness, brackets, thermal straps or shielding walls are modelled yet.
- Body solar cells are not modelled as a skin layer (their thickness counts against the protrusion limit
  on faces without wings).
- The dispenser interface (rails, tabs, springs) is simplified: check against the chosen dispenser drawing.
