# Ginkgo

> **Private for now.** The repository will be opened to the public once the design is complete. No licence has been applied yet; the plan (`docs/licensing.md`) is CERN-OHL-S-2.0 for hardware,
> Apache-2.0 for software and CC-BY-4.0 for documents. Analysis-level design only: no hardware exists, nothing here is qualified for flight, and every number is an engineering estimate.

Ginkgo is an open, modular, fully documented small-satellite **platform** and a first mission built on it: a science-first, long-life **12U observatory** with a tiered 50-year survival design.
Everything is generated from configuration files and checked by tools, so a derived mission is a configuration change plus new cards.

*Türkçe özet:* Ginkgo, açık kaynak, modüler bir küçük uydu platformu ve üzerine kurulu ilk görev: uzun ömürlü, bilim öncelikli 12U gözlemevi. Tasarım analiz düzeyinde tamamlandı (donanım yok);
her sayı config dosyalarından üretilen araçlarla doğrulanıyor. Depo şimdilik özel, tasarım olgunlaşınca herkese açılacak.

## Where things stand

The design is **complete at analysis level**: requirements, architecture, CAD with interference checks, power/thermal/attitude/orbit/structure analyses, protocol and firmware core with tests,
electronics interface (KiCad, DRC clean), FMEA, test plan, operations concept, cost and schedule. Start with **`docs/sdd.md`** (system design document) and **`docs/status.md`** (latest regression).
What is missing is physical: vendor data, schematics of the functional cards, prototypes, tests, a launch and an operator. See `docs/plan.md`, `docs/risks.md` and `docs/cost.md`.

| At a glance | Value |
|---|---|
| Form | 12U CubeSat envelope, 2 x 2 x 3 cell grid around a central spine, notched 100 x 100 mm cards |
| Mass / power | about 16.8 kg of 24 kg; 58 W sun-biased, 28 W tumbling, 3 W safe-mode load |
| Science | ~26 instruments: telescope (5 m class) + hyperspectral, thermal IR, magnetometer, particles, X-ray/UV, TSI, VLF, GRB, dosimetry, SEU/flash experiments |
| Compute | MSP430 supervisor, 2 x STM32H7, mass memory unit (8 x 128 GB, 6+2), Pi CM5, Jetson Orin Nano |
| Power | two LiFePO4 chains + independent survival chain, hardware-only protection |
| Propulsion | iodine electric thruster on the centre line, ~570 m/s available (about 190 m/s planned), drag sail |
| Verification | 47 requirements traced (see `docs/verification-matrix.md`); most checked automatically on every run; 29 planned tests |

## Documentation

| Topic | Read |
|---|---|
| Overview | `docs/sdd.md`, `docs/plan.md`, `docs/status.md` |
| Requirements and verification | `mission/requirements.md`, `docs/verification-matrix.md`, `docs/test-plan.md`, `docs/fmea.md`, `docs/risks.md` |
| Design | `docs/architecture.md`, `docs/layout.md`, `docs/structure.md`, `docs/icd.md`, `mechanical/README.md` |
| Power, thermal, attitude, propulsion | `docs/power-architecture.md`, `docs/eps-card.md`, `docs/thermal.md`, `docs/adcs.md`, `docs/propulsion.md`, `docs/orbit-and-debris.md` |
| Electronics, software, data | `docs/electrical-interface.md`, `docs/firmware-architecture.md`, `docs/protocol.md`, `docs/data-plan.md`, `docs/mission-simulation.md` |
| Operations and ground | `docs/ops-concept.md`, `docs/ground-station-kit.md`, `docs/longevity.md` |
| Context | `docs/prior-art.md`, `docs/design-identity.md`, `docs/decisions/`, `docs/outreach-led.md`, `docs/cost.md`, `docs/licensing.md`, `CREDITS.md` |

## Repository layout

| Path | Content |
|---|---|
| `configs/` | Single source of truth: science, geometry, layout, data, longevity, thermal, structure, cost (+ 2U/3U/6U variants) |
| `mission/` | Requirements, `traceability.toml` (requirement -> verification), `tests.toml` (planned tests), `fmea.toml` |
| `sim/` | Budgets, layout rules, balance, data, longevity, link, EPS, ADCS, thermal, structure, orbit lifetime, mission simulation, cost, LED visibility, live verification matrix |
| `mechanical/` | Voxel packing, parametric build123d assembly, interference/mass properties, STEP/STL/renders |
| `electronics/` | Connector pinout (single source), KiCad card template and 15-slot backplane strip (DRC clean), EPS diagram |
| `protocol/` | Message definitions, C/Python generator, tests (round trip, corruption, byte-exact C <-> Python) |
| `firmware/` | Host-testable core: Ed25519 command authentication, modes, FDIR, command queue, A/B OTA (68 unit checks + signature cross-checks) |
| `groundstation/` | Pass prediction, contact plan and reference decoder |
| `tools/` | `check_all.py` (whole regression), FMEA, test-plan and requirement checks, generators for the ICD and the SDD |

## Quick start

```
pip install build123d cryptography sgp4       # CAD kernel, signing tests, orbit propagation (numpy, scipy, pillow come with build123d); KiCad 10 optional for DRC
python tools/check_all.py                     # runs every analysis and test, writes docs/status.md   (--quick skips CAD, thermal and the verification matrix)
python sim/trace_check.py                     # live requirements verification matrix
python mechanical/ginkgo_cad.py               # full CAD assembly and checks, exports into mechanical/out/
python tools/gen_sdd.py                       # regenerate the system design document
```

Requires Python 3.11+ and GCC for the firmware and protocol tests. The `sim/` tools use only the standard library unless noted.

## Status and next steps

Design freeze candidate v0 at analysis level. The decisions that shape everything next: choose the target (flight mission, flight-quality reference design, or the precursor path with a FlatSat and a balloon flight),
confirm the preferred orbit, and get vendor quotes and datasheets. Details in `docs/sdd.md` section 8.
