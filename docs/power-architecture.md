# Power architecture: fault containment and redundancy (draft v0)

Principle: **no single failure in power may kill the spacecraft.** Every failure is contained
to its own zone by hardware, without relying on software.

## Zones (physically separated)

```
 [Solar strings A,B,C,D]  independent, one per panel group
        |  (blocking diode + fuse per string)
 [MPPT/charger 1] [MPPT/charger 2]        <- two independent EPS boards
        |                 |
 [Battery pack 1]   [Battery pack 2]      <- separate compartments, thermal barrier,
   (own BMS, fuse,     (own BMS, fuse,       vent path away from electronics
    disconnect)         disconnect)
        |                 |
        +---- ideal-diode OR-ing ---- Main bus A / Main bus B
                                        |
                          [per-load latching current limiter (LCL)]
                                        |
                          loads: OBC, Pi, Jetson, ADCS, radio, payloads
```

## Rules

1. **Batteries are isolated**: own enclosure/compartment, thermal barrier (polyimide/ceramic
   fibre), mechanical restraint, vent path directed away from electronics. Each pack has its own
   fuse, cell-level protection and hardware disconnect switch.
2. **Redundant EPS**: two independent EPS boards; either can carry essential loads alone.
3. **Two buses (A/B)** joined by ideal-diode OR-ing; a short on one side cannot pull the other down.
4. **Per-load protection**: every load has a latching current limiter with over-current trip and
   autonomous retry, implemented in hardware and monitored by the MSP430 supervisor.
5. **Independent solar strings** with blocking diodes and fuses; a shorted string is dropped.
6. **Cross-strapping**: essential loads (supervisor, beacon radio, OBC) can be powered from A or B.
7. **Connectors and harness**: separate power and data routing, redundant pins on every power
   connector, no power through a single pin, strain relief, keep-out from battery zone.
8. **No software in the protection path**: OCP/OVP/UVP/thermal cutoffs are analog/hardware.
9. **Cell chemistry**: prefer LTO (no lithium plating, high cycle life, wide temperature) or LiFePO4;
   plain Li-ion only where energy density is needed and containment is proven.
10. **Deployment inhibits**: three independent inhibits before any deployable or propulsion
    energises (launch-provider requirement style).
11. **Degradation ladder**: full mode -> sun-only mode (no battery) -> supervisor + beacon only.

## Trade-offs

More mass, volume and board area (~0.3-0.6 kg, ~0.3-0.5U for 6U). Accepted: reliability and
50-year durability outweigh density for the power subsystem.

## Survival bus (independent emergency source)

A third, fully independent power path: **pack C (2S1P LiFePO4, 5 Wh, 6.4 V nominal, ~780 mAh)** with its own solar string,
charger, BMS, fuse and containment. The 2S configuration matches packs A/B's bus convention on purpose (`docs/eps-card.md`): it lets the survival card reuse the same
charger, ideal-diode and eFuse parts as EPS-A/B (fewer unique parts to qualify and stock for the whole spacecraft), at the cost of needing a small-format LiFePO4 cell
in this capacity class (not yet sourced). It is not connected to buses A/B and feeds only:

- MSP430 supervisor and beacon transmitter
- antenna and wing deployment drivers (burn wire), so deployment never depends on packs A/B
- minimal heater for the survival electronics

Behaviour:
1. After dispenser separation, a timer (with independent inhibits) uses pack C to deploy antenna and wings.
2. In any fault where A/B are lost or shut down, the spacecraft keeps beaconing and can be commanded to recover.
3. Pack C is charged only from its own dedicated body-mounted string so a fault on the main strings cannot drain it.
4. Option under study: a non-rechargeable primary cell as a last-resort backup for deployment only.

Degradation ladder becomes: full mode -> sun-only mode -> supervisor + beacon on survival bus.
