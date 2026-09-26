# Design identity (draft v0): what makes this design ours

Project name: **Ginkgo**. The ginkgo is a "living fossil" that has survived for ~270 million
years, which is the design philosophy: build for decades, degrade gracefully, never die of a
single fault.

## What is new, what is borrowed

See `docs/prior-art.md` for the honest comparison with OreSat, LibreCube, UPSat and others. In short: the
card/backplane idea is **not** ours (OreSat is the closest precedent); our contribution is the combination below.

We do not claim to have invented every part. We claim a distinctive *combination*, published
openly, and we document prior art honestly. A `docs/prior-art.md` review is part of phase 1.

### Distinctive contributions

1. **Ginkgo Cell Standard (GCS)** (close to OreSat's card/backplane; the differences are the grid, spine, notched card and checked rules). The 12U body is a 2 x 2 x 3 grid of ~113 mm cells around a
   central spine and cross bulkheads. Each payload is a self-contained "cassette" occupying a
   defined number of cells, with fixed mechanical, thermal, power and data interfaces. New
   missions re-use the bus and swap cassettes. The cell grid is derived directly from the
   deployer envelope (226 x 226 x 340 mm = 2 x 2 x 3 cubes), so it adapts to 3U..24U.
2. **Design rules as code.** Thermal and electromagnetic separation rules (magnetometer far from
   batteries and wheels, telescope opposite the hot computer, packs in separate decks, ...)
   live in `configs/12u_layout.toml` and are checked automatically by `sim/layout_check.py`.
   Every design revision is machine-verified against them.
3. **Three-layer power isolation.** Packs A and B (main), plus an independent survival pack C
   with its own string and charger, hardware-only protection, and a degradation ladder down to
   beacon-only (see `docs/power-architecture.md`).
4. **Dual-computer radiation experiment.** A Raspberry Pi CM5 and a Jetson Orin Nano fly side
   by side, each supervised by an MCU, and their error rates are compared as science data.
5. **Science-first mass and volume allocation.** Payload value ranking drives the layout; the
   spacecraft carries a 26-instrument suite designed for long, continuous data records
   (irradiance, magnetic field, radiation, plasma, ionosphere).
6. **Longevity artefacts.** Laser retroreflector for decades of precise orbit tracking; sapphire
   / nickel memory plate carrying the open design archive; open protocol and open ground software
   so the mission outlives its original operators.
7. **Config-driven everything.** Mass, power, volume, layout and scenarios all derive from TOML
   files, so a derived mission is a config change plus new cassettes.

### Borrowed (and credited)

- CubeSat Design Specification (Cal Poly CDS) for envelope and rails.
- CCSDS / CFDP-style file delivery, AX.25 amateur framing, SatNOGS-style volunteer ground network.
- Common COTS parts and open toolchains (STM32, MSP430, Raspberry Pi, Jetson, Zephyr/FreeRTOS).

### Optional visual signature (to decide in the mechanical phase)

- Ginkgo-leaf fan deployment for the solar wings (single pivot, single release line, fewer
  mechanisms). Trade-off: less efficient use of rectangular cell area. To be evaluated.
- Distinctive solar cell pattern and marking on the panels; engraved emblem on the memory plate.
