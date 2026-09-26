# Longevity and radiation analysis (draft v0)

Tools: `sim/longevity.py`, `configs/12u_longevity.toml`. All inputs are engineering estimates;
replace with SPENVIS/OMERE dose runs, cell data and part-level radiation test data.

## Findings (700 km, sun-synchronous, eclipse cycling)

| Item | Result |
|---|---|
| Solar arrays (1.5 %/yr loss) | Full load still covered in ADCS-biased mode for 50 yr; tumbling mode falls below full load at ~48 yr |
| Safe mode (body cells only, 1.1 W) | Holds for well over 50 yr |
| Main LiFePO4 packs A+B (2S2P 26650, 42 Wh each) | ~5300 eclipse cycles/yr, ~11 % DoD: ~15 yr to 20 % fade; can no longer cover eclipse after ~36 yr |
| Total ionising dose (2 mm Al) | 2 krad/yr, ~100 krad over 50 yr |
| COTS SoC (Jetson / Pi, ~15 krad) | ~8 yr at 2 mm, ~17 yr at 5 mm, ~33 yr at 10 mm |
| STM32H7 (~30 krad) | ~33 yr at 5 mm, ~67 yr at 10 mm |
| MSP430FR + FRAM (~50 krad) | ~56 yr at 5 mm |

## What this means: 50 years is a *tiered* lifetime, not one number

1. **Survival chain (target 50+ yr):** MSP430 supervisor, beacon transmitter, survival bus, body-
   mounted cells. Must keep working with no battery (sun-only, AO-7 style); design the beacon so
   it runs directly from the solar string.
2. **Long-life science chain (target 30-50 yr):** magnetometer, TSI radiometer, dosimeter,
   particle spectrometer, atomic clock, housekeeping, logged and downlinked by the **STM32
   flight controller, not by the Linux computers**. Rule: no long-record instrument may depend
   on the Pi or Jetson for its data path.
3. **Heavy compute (target ~10-15 yr):** Jetson and Pi. Expect radiation-limited life; treat as
   consumables. Design for graceful loss (science keeps flowing through chain 2).
4. **Main batteries (target ~15-35 yr):** after fade, switch to sun-only operation (no eclipse
   operations for heavy loads). A dawn-dusk orbit removes the eclipse problem entirely.

## Design responses adopted

- Spot radiation shielding module (Ta/Al on MCU, FRAM, supervisor, radio ICs), +0.4 kg, +60 cm3.
- Long-life science chain rule above (firmware architecture requirement).
- Sun-only beacon mode without battery.
- Optional high-reliability variant: rad-hard MCU (SAMRH71 / VA41630 class, ~100 krad) for the
  flight controller.
- Prefer a dawn-dusk sun-synchronous orbit if the launch offers it (no eclipse cycling).

## Open issues

- Survival pack C (5 Wh) cycles at a similar depth as A/B; after ~10 yr it too fades. The beacon
  must therefore not depend on it (sun-only mode).
- Thermal cycling (~5300 cycles/yr, ~265k cycles in 50 yr) is a solder-joint and connector
  fatigue risk; needs low-CTE-mismatch design, underfill, conformal coating and testing.
- Space debris and micrometeoroid risk over 50 yr is not yet quantified; propulsion enables avoidance.
- Full-vault shielding (10-20 mm Al) would extend compute life but costs 1-3 kg and 400-1500 cm3.

## Protection (shielding) design

**Radiation.** Mass is abundant (about 11.7 kg spare) while volume is scarce (about 95 % full), so
use dense high-Z material for volume efficiency: a graded-Z Al/Ta vault (~10 mm Al-equivalent,
2.7 g/cm2) needs about 1.6 mm of tantalum instead of 10 mm of aluminium (roughly 6x less volume for
similar mass). The vault covers the flight controller, supervisor, FRAM, mass-memory controller and
radio ICs. Layout also helps: heavy items (packs, tank, wheels) placed around sensitive boards.

**Impact.** Whipple-type double walls (bumper, gap, rear wall, Nextel/Kevlar layers) protect the
propellant tank and battery vaults; the gap must be integral to the internal structure because the
external protrusion allowance is only a few mm. Shielding stops particles up to about 1 mm; the
1 mm - 1 cm class can neither be tracked nor stopped, so redundancy (packs A/B/C, computer
hierarchy, survival chain) is the real defence. Quantify with ESA MASTER / NASA ORDEM.
