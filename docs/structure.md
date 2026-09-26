# Structure and launch loads (draft v0)

Tool: `python sim/structure.py`; inputs `configs/12u_structure.toml`. Hand calculations with stated assumptions; **no finite-element model, no modal test yet**. The launch provider's
load and stiffness specification replaces the generic values below.

## Results

| Item | Result | Margin |
|---|---|---|
| Frame lateral bending mode (cantilever estimate) | ~900 Hz | 9x over a 100 Hz minimum |
| Side wall panel (3 mm Al, loaded) | ~167 Hz | 1.7x |
| **Stowed wing panel (2.1 mm)** | 99 Hz if held only at its ends; **~190 Hz with three hold-down posts along each long edge** | 1.9x (was 0.99x) |
| Quasi-static 20 g: rails axial / frame bending stress | 10 / 3 MPa against 240 MPa yield | > 18x |
| Bolted mounts (telescope, tank, packs, Jetson, ADCS, vault, GRB) at 40 g local | margins 6x to 27x | all >= 6x |
| Wing hold-down preload vs lift-off (6 points, 120 N preload) | 53 N load per point | 2.3x |
| Card boards, Steinberg at 200 Hz first mode | 0.21 mm 3-sigma deflection vs 0.35 mm allowed | 1.7x |

Verdict: 14 of 14 checks meet their margin after one design change.

## Design change found by the analysis

The stowed wing panels (226 x 340 x 2.1 mm, PCB + cells) would resonate at about 99 Hz, right at the minimum stiffness a rideshare provider usually asks for, and worse if
held only by corner posts. **Each wing stack now has six hold-down posts (three along each long edge, including mid-length)**, which halves the free span and raises the mode to ~190 Hz. Posts pass
through the panel stack and release together with the burn wire. This is a requirement on the wing mechanical design (`mechanical/`, to be detailed).

## Cards and modules

- Cards need a first mode near 200 Hz or above: edge guides on two edges, 3 mm keep-out, stiffener rails on large boards; a 100 Hz card would exceed the solder-joint limit (Steinberg margin 0.6).
- Heavy items are all bolt-mounted with large margins; the propellant tank (2.5 kg with iodine) and the radiation vault (1.6 kg) are the most loaded bolt groups.

## Assumptions and limits

- Design load factor 20 g in every axis, local amplification 2x, random profile flat 0.04 g2/Hz (8.9 Grms) with Q = 10: generic and conservative; real rideshare specifications are usually lower for loads, but stiffness minima can be higher.
- Frame frequency from a uniform cantilever with the whole mass distributed along it: optimistic for the coupled system (heavy modules on brackets, telescope tube overhang, propulsion bay opening in the bulkhead).
- Steinberg constant: the tool uses C = 1.0; for BGA-type parts a value near 1.75 is commonly quoted, which would drop the card margin at 200 Hz to about 1.0 (a marginal pass); component types must be checked per card, and the wall-panel resonance (~167 Hz) amplifies the input to the cards (not modelled).
- No thermal-structural effects, no fatigue life beyond Steinberg, no dispenser-spring or separation shock, no buckling, no bolt preload scatter.
- Iodine propellant sloshing is not an issue (solid at launch); the tank is treated as a rigid mass.

## Open items

- Finite-element model of the frame and modal analysis; sine sweep and random vibration test of an engineering model (see `docs/test-plan.md`).
- Separation shock and deployment shock (burn wire, hinge springs), deployer clearance and rail wear.
- Bulkhead cut-out for the propulsion bay: local stiffness and the load path of the tank.
