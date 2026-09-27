# Prior-art review (draft v0, September 2026)

Purpose: say honestly what is borrowed, what is close to existing work, and what is genuinely ours, so nobody
can fairly say "copied" and so we know what to reuse instead of reinventing. This was a targeted web search,
**not an exhaustive patent or literature search**; do a proper freedom-to-operate review before any commercial use.

## 1. Closest existing work

| Project | What it is | Relation to Wollemi |
|---|---|---|
| [OreSat](https://www.oresat.org/) (Portland State Aerospace Society) | Fully open-source 2U CubeSat with a **card/backplane bus** replacing PC/104 stacks: cards slide into frames, CAN bus at 1 Mbps, 2-cell Li-ion power bus, scalable 1U-3U | **Closest**: the card-slot idea, CAN control bus, open hardware. See [OreSat overview](https://www.oresat.org/technologies/cubesat-subsystems), [backplane repo](https://github.com/oresat/oresat-backplane), [structure paper](https://arc.aiaa.org/doi/10.2514/6.2021-1256) |
| [LibreCube](https://librecube.org/) | Open ecosystem of PC/104-format boards with ECSS/CCSDS standards | Same spirit; PC/104 stack, not a cell grid. Their use of CCSDS/ECSS matches our protocol choices |
| [UPSat](https://www.libre.space/projects/upsat/) (Libre Space Foundation, Univ. of Patras) | First satellite in orbit whose hardware and software were entirely open source (2U) | Precedent for fully open satellites |
| [AcubeSAT](https://arxiv.org/abs/2503.18473), EIRSAT-1, PULSE-A open bus | Student open-source missions with published OBC/flight software | Reference for flight-software structure |
| [SatNOGS](https://satnogs.org/) | Global open ground-station network and database | Our ground network; currently VHF/UHF, S-band is a stated goal, not the default (see `docs/ground-station-kit.md`) |
| [PC/104 stacks, backplane "card cage" and rack systems](https://www.nasa.gov/wp-content/uploads/2021/10/6.soa_structures_2021.pdf) | Common CubeSat structure practice (stacked PCB, backplane, card retainers) | Backplane and card retainers are established practice |
| AFRL Space Plug-and-Play Avionics (SPA / nanoSPA) | Plug-and-play spacecraft component concept | Prior art for "swap black-box modules" |
| [AMSAT-OSCAR 7](https://en.wikipedia.org/wiki/AMSAT-OSCAR_7) | Launched 1974, battery failed 1981, revived 2002, runs from its solar panels | Inspiration and proof for the sun-only survival mode (see [AMSAT history](https://www.amsat.org/amsat-ao-7-a-fifty-year-anniversary/)) |
| [ThrustMe NPT30-I2](https://www.thrustme.fr/products/npt30-i2) | Commercial iodine gridded-ion thruster for CubeSats, 1U/1.5U, ~1.1 mN, 5500 / 9500 Ns; first in-orbit iodine demonstration in 2020 | Validates our propulsion assumption: 9500 Ns on ~14 kg is about 680 m/s; check power and mass on the datasheet |

Note: the OreSat and Carnegie Mellon PocketQube efforts also show that a small open project can reach flight.

## 2. What we borrow (credited)

CubeSat Design Specification envelope and rails; CCSDS Space Packets and CFDP; AX.25/amateur-band rules;
CAN as control bus; volunteer ground network model (SatNOGS, TinyGS); COTS parts and open toolchains
(Zephyr, KiCad, build123d); the sun-only survival idea from AO-7.

## 3. What is close to existing work (do not oversell)

- **"Cassette/cell" architecture** is closest to OreSat's card/backplane. It is *not* a new invention.
  What differs: a **12U 2 x 2 x 3 cell grid with cross bulkheads and a central spine** derived from the
  deployer envelope, a **corner-notched card format** for the spine, and a **machine-checked design-rule set**.
  Decision to take: consider staying **interoperable with OreSat conventions** (CAN/CANopen object dictionary,
  power bus levels) so existing open cards could be reused, instead of a private variant.
- **Modular open avionics, electric propulsion on cubesats, redundant power** are all established.

## 4. Where Wollemi's contribution really is (claims we can defend)

1. **Design rules as code plus config-driven verification**: one set of TOML files drives budgets, layout rules,
   geometric packing, interference checks, mass properties, data and longevity analysis. To our knowledge this
   level of automated, open verification is uncommon in open CubeSat projects (not verified exhaustively).
2. **Explicit tiered lifetime model** (survival chain, long-life science chain, heavy compute, batteries) with a
   firmware rule that decouples multi-decade science from Linux nodes.
3. **Science-first 12U suite with cross-instrument physics** (magnetometer boom away from wheels and batteries,
   radiation comparison of three compute families, flash retention experiment, TSI/particle/VLF records).
4. **Open, scripted geometric packing workflow** that found real constraints (spine notch, round telescope tube,
   nadir/zenith placement) before any hardware was cut.
5. **Open S-band ground kit** targeting the gap left by VHF/UHF-focused networks (to be built).

## 5. Actions

- Decide on OreSat interoperability (CANopen dictionary, backplane pinout) or document why not.
- Read the OreSat structure paper and backplane repository in detail (the publisher blocked automated access, so
  only the abstract-level summary above was used).
- Search patents (e.g. card-slot CubeSat structures, "Card-Sat" style filings) before publishing card format details.
- **Name check:** the project was renamed from "Ginkgo" to "Wollemi" after a search found the earlier name conflicted with a live trademark (Ginkgo Bioworks) and an unrelated open-source HPC library
  (`docs/licensing.md`). A quick search for "Wollemi" found no satellite or well-known company of that name and no conflict at this pass, but a full trademark clearance is still needed before public
  release; the name is easy to change again while the repository is small.
- Add a `CREDITS.md` when the repository is opened.

Sources: OreSat, LibreCube, UPSat, AcubeSAT, SatNOGS, AMSAT, ThrustMe links above.
