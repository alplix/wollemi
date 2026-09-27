# Structure and launch loads (draft v0)

Tool: `python sim/structure.py`; inputs `configs/12u_structure.toml`. Hand calculations with stated assumptions; **no finite-element model, no modal test yet**. The launch provider's
load and stiffness specification replaces the generic values below.

## Results

| Item | Result | Margin |
|---|---|---|
| Frame lateral bending mode (cantilever estimate) | ~900 Hz | 9x over a 100 Hz minimum |
| Side wall panel (3 mm Al, loaded) | ~167 Hz | 1.7x |
| **Stowed wing panel (2.1 mm)** | 99 Hz if held only at its ends (lower bound); ~190 Hz if the three hold-down posts are idealised as a continuous line (upper bound, optimistic); design value ~137 Hz (geometric mean) | 1.4x (was 0.99x) |
| Quasi-static 20 g: rails axial / frame bending stress | 10 / 3 MPa against 240 MPa yield | > 18x |
| Bolted mounts (telescope, tank, packs, Jetson, ADCS, vault, GRB) at 40 g local | margins 6x to 27x | all >= 6x |
| Wing hold-down preload vs lift-off (6 points, 120 N preload) | 53 N load per point | 2.3x |
| Card boards, Steinberg at 220 Hz first mode | 0.18 mm 3-sigma deflection vs 0.35 mm allowed (leaded parts, C=1.0) | 1.9x |
| Card boards, Steinberg at 220 Hz, BGA/leadless parts (C=1.75) | same deflection vs 0.20 mm allowed | 1.1x |

Verdict: 14 of 14 checks meet their margin after one design change.

## Design change found by the analysis

The stowed wing panels (226 x 340 x 2.1 mm, PCB + cells) would resonate at about 99 Hz, right at the minimum stiffness a rideshare provider usually asks for, and worse if
held only by corner posts. **Each wing stack now has six hold-down posts (three along each long edge, including mid-length)**, which halves the free span. The two idealised hand-calculation
bounds are 99 Hz (posts absent) and ~191 Hz (posts idealised as a continuous line, optimistic, since three points are not a line); `sim/structure.py` now uses their geometric mean, ~138 Hz, as the
design value (margin 1.4x), rather than reporting the optimistic 190 Hz figure as if it were the answer. Posts pass through the panel stack and release together with the burn wire. This is a
requirement on the wing mechanical design (`mechanical/`, to be detailed), and the true point-supported frequency needs an FEM model or a modal survey to pin down within the 99-191 Hz range.

## Cards and modules

- Cards need a first mode near 220 Hz or above (raised from 200 Hz once the BGA/leadless Steinberg constant was checked): edge guides on two edges, 3 mm keep-out, stiffener rails on large boards; a 100 Hz card would exceed the solder-joint limit (Steinberg margin 0.6 for leaded parts, worse for BGA).
- Heavy items are all bolt-mounted with large margins; the propellant tank (2.5 kg with iodine) and the radiation vault (1.6 kg) are the most loaded bolt groups.

## Assumptions and limits

- Design load factor 20 g in every axis, local amplification 2x, random profile flat 0.04 g2/Hz (8.9 Grms) with Q = 10: generic and conservative; real rideshare specifications are usually lower for loads, but stiffness minima can be higher.
- Frame frequency from a uniform cantilever with the whole mass distributed along it: optimistic for the coupled system (heavy modules on brackets, telescope tube overhang, propulsion bay opening in the bulkhead).
- `sim/structure.py` now checks both Steinberg constants (C=1.0 leaded, C=1.75 BGA/leadless) and the 220 Hz target keeps both above 1.0 margin; component types should still be checked per card. The wall-panel resonance (~167 Hz, Q~10) amplifying the input to the cards is still not modelled.
- No thermal-structural effects, no fatigue life beyond Steinberg, no dispenser-spring or separation shock, no buckling, no bolt preload scatter.
- Iodine propellant sloshing is not an issue (solid at launch); the tank is treated as a rigid mass.

## Open items

- Finite-element model of the frame and modal analysis; sine sweep and random vibration test of an engineering model (see `docs/test-plan.md`).
- Separation shock and deployment shock (burn wire, hinge springs), deployer clearance and rail wear.
- Bulkhead cut-out for the propulsion bay: local stiffness and the load path of the tank.
