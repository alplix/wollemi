# Architecture (v1, 12U observatory)

Overview of how the pieces fit; details are in the documents listed at the end. All numbers are engineering estimates (`docs/sdd.md` has the live values).

## Principle: platform, cells and cards

```
 +--------------------------------- 12U frame (rails, walls, plates) ---------------------------------+
 |  Column Q1        Column Q2          Column Q3            Column Q4              central spine     |
 |  telescope        attitude, optics   compute, comms,      energy vault,          (backplane hub,   |
 |  + spectrometer   + trim ballast     quiet science        hard-radiation science  harness)         |
 |        each column: 3 decks of Ginkgo cards (100 x 100 mm, spine notch) on a passive backplane strip |
 |                       propulsion bay across Q2/Q3 on the -X centre line                             |
 +------------------------------------------------------------------------------------------------------+
   wings (2 x 3 double-sided panels), body cells, antennas, apertures on the outer skin
```

- The frame is split into a 2 x 2 x 3 **cell grid** around a 40 mm spine. Every card is 100 x 100 mm with a 20 mm corner notch (clears the spine), an 8 mm outer relief (clears the rail) and a 4 mm gap to the backplane.
  Non-card items (telescope tube, tank, packs, ballast) occupy defined cell volumes. This is close to OreSat's card/backplane idea; the grid, notched card and machine-checked rules are ours (`docs/prior-art.md`).
- A new mission changes the configuration files and the cards; the bus, the tools and the protocol stay.

## Subsystems in one page

| Subsystem | Architecture | Key document |
|---|---|---|
| Structure | Al frame, corner rails, four columns, hold-down posts for wing stacks | `docs/structure.md` |
| Power | two independent MPPT/battery chains (A, B) plus an independent survival chain (C); per-card eFuse, hardware kill, no software in the protection path | `docs/power-architecture.md`, `docs/eps-card.md` |
| Thermal | passive with MLI patches (effective emissivity ~0.5), isolated telescope column, battery vault and survival heaters | `docs/thermal.md` |
| Attitude and propulsion | wheels, torquers, star tracker; iodine thruster on the centre line, canted through the CoM; drag sail | `docs/adcs.md`, `docs/propulsion.md` |
| Compute | supervisor (MSP430FR), two flight controllers (STM32H7), mass memory unit, Pi CM5, Jetson | `docs/firmware-architecture.md` |
| Data and comms | CCSDS packets with signed commands, CAN-FD A/B control plane, Ethernet data plane, UHF and S-band | `docs/protocol.md`, `docs/data-plan.md` |
| Payload | 26 instruments; long-life science chain acquired by the flight controllers, imaging by the Linux computers | `docs/data-plan.md`, `docs/layout.md` |
| Ground and operations | open S-band kit, unattended reference station, contact plan | `docs/ops-concept.md`, `docs/ground-station-kit.md` |

## Reliability approach (COTS in LEO)

- **Tiers** (`docs/longevity.md`): survival chain (50+ years), long-life science chain (30-50), heavy compute (10-15), main batteries (10-28).
- Three independent power paths; every card protects itself in hardware; the supervisor can kill any slot without firmware (`SLOT_SEL`, `KILL_N`).
- Latch-up protection per card, ECC and scrubbing, critical data in FRAM with checksums, erasure-coded mass memory, spot shielding (Ta/Al vault) for the control electronics.
- Degradation ladder L0-L3 with modes NOMINAL, SCIENCE, SCIENCE_LITE, ECLIPSE, BURN, SAFE, SURVIVAL (`docs/mission-simulation.md`).
- Failure modes covered in `docs/fmea.md`; verification in `docs/verification-matrix.md` and `docs/test-plan.md`.

## Density levers used

1. Deployable double-sided wings on top of body cells (largest power gain).
2. Shared optics (hyperspectral behind the telescope), cards packed by contact-maximising 3D packing.
3. Dense shielding metal (tantalum) where volume, not mass, is the constraint.
4. Duty cycling with battery buffering and a burn mode that cuts every other load.
5. On-board processing and priority queues to fit the science data into the S-band pass budget.

## Scaling

Form factor and module lists are configuration (`configs/`): the 2U, 3U and 6U files are earlier variants kept for comparison (`configs/README.md`); the 12U configuration is the maintained design.
