# Ginkgo

> **Private for now.** The repository will be opened to the public once the design is complete.
> No licence has been applied yet; the plan is CERN-OHL-S-2.0 (hardware), Apache-2.0 (software),
> CC-BY-4.0 (documents).

Ginkgo is an open, modular, fully documented small-satellite **platform** and a first mission built on it:
a science-first 12U observatory designed for very long life. Design-to-manufacture stage only;
nothing is built or launched from this repo yet. Everything is meant to be adapted to other missions.

*Türkçe özet:* Ginkgo, açık kaynak, modüler bir küçük uydu platformu ve üzerine kurulu ilk görev: uzun ömürlü,
bilim öncelikli 12U gözlemevi. Depo şimdilik özel; tasarım tamamlanınca herkese açılacak.

## Current design (12U science-first observatory)

- Form: 12U CubeSat envelope (226 x 226 x 340 mm), internal 2 x 2 x 3 cell grid + central spine.
- Science: ~26 instruments (telescope + hyperspectral, thermal IR, magnetometer, particle, X-ray/UV,
  VLF, plasma, GRB, TSI radiometer, GNSS/TEC, dosimeter, atomic clock, flash/computer radiation experiments...).
- Compute: Jetson Orin Nano + Raspberry Pi CM5 + STM32H7 flight controller + MSP430FR supervisor,
  dedicated mass memory unit (8 x 128 GB, 6+2 erasure coding).
- Power: two LiFePO4 packs + independent survival pack, hardware-only protection, 2 deployable wings.
- Propulsion: electric (iodine), burn mode with minimal services; collision avoidance from the ground.
- Longevity: tiered 50-year design (survival chain, long-life science chain, heavy compute, batteries).
- Open access once launched: public telemetry/data, LoRa relay, open protocol.

## Layout

| Path | Content |
|---|---|
| `mission/` | Requirements, figures of merit, open access, collision avoidance |
| `docs/` | Architecture, power, layout, data plan, propulsion, longevity, firmware, design identity |
| `configs/` | Single source of truth: `12u_science.toml`, `12u_layout.toml`, `12u_data.toml`, `12u_longevity.toml` (+ 2U/3U/6U variants) |
| `sim/` | `budget.py`, `layout_check.py`, `balance.py`, `data_budget.py`, `longevity.py` |
| `mechanical/` | Parametric CAD (build123d): voxel packing, full 12U assembly, STEP/STL/renders, interference + mass properties |
| `electronics/`, `firmware/`, `groundstation/` | Planned |

## Quick start

```
python sim/budget.py configs/12u_science.toml        # mass, power scenarios, volume, FOMs
python sim/layout_check.py                           # cell fill and separation rules
python sim/balance.py                                # centre of mass and per-column heat
python sim/data_budget.py                            # science data vs downlink and storage
python sim/longevity.py                              # year-by-year power, battery and radiation dose
```

`sim/` needs only Python 3.11+ (uses `tomllib`). `mechanical/` needs `pip install build123d` (also brings numpy, scipy, pillow).

Mechanical model:

```
python mechanical/pack.py
python mechanical/ginkgo_cad.py     # STEP/STL/PNG into mechanical/out/
```

## Status

Phase 0 complete: requirements, architecture, budgets, layout and analysis tooling. All numbers are
engineering estimates (module sizes are bounding boxes, not vendor CAD). Parametric CAD assembly now exists and passes
the interference check; firmware architecture drafted; next: prior-art review, open ground-station kit, protocol spec.
