# Cost and schedule estimate (draft v0)

**Read this first: every number below is an unverified order-of-magnitude estimate made without vendor quotes; treat each as +-2x.** Purpose: to see the scale of the project and which choices drive it, not to
plan a budget. Tool: `python sim/cost.py`; inputs `configs/12u_cost.toml`; test effort from `mission/tests.toml`. Each item is a triangular distribution (low, likely, high) and the totals are Monte Carlo
percentiles (20 000 samples). Labour is shown separately because volunteer time is not cash.

## Scenarios (USD)

| Scenario | Cash P10 | Cash P50 | Cash P90 | Effort (person-years, P50) | Labour value at 90 k per person-year |
|---|---|---|---|---|---|
| **Precursor: FlatSat + balloon flight** (no launch, no flight-only hardware) | 0.72 M | **0.84 M** | 0.97 M | 7.4 | 0.67 M |
| Core flight (bus + long-life science chain, no imaging) | 3.4 M | 3.9 M | 4.4 M | 17.5 | 1.6 M |
| **Full flight** (imaging, hyperspectral, extras) | 4.0 M | **4.5 M** | 5.0 M | 20.3 | 1.8 M |

Schedule to launch (critical path, small team): P10 48 months, **P50 54 months (4.5 years)**, P90 62 months, dominated by long-lead items, the FlatSat and environmental campaign, and the wait for a launch.

## Largest items (likely values)

| Item | Likely cost |
|---|---|
| Launch: 12U rideshare slot with integration | 500 k (250 k - 1.2 M) |
| Electric propulsion (iodine thruster, vendor price unknown) | 380 k |
| Space-weather instruments (particle, X-ray, TSI, GRB, VLF, Langmuir, micrometeoroid) | 220 k |
| Solar wings and body cells (~330 space-grade cells) | 200 k |
| Telescope | 180 k |
| Hyperspectral spectrometer (research level) | 150 k |
| External test facilities (radiation, thermal vacuum, thruster, vibration, EMC) | ~0.7 M (0.35 - 1.4 M) |

Contingency: 30 % on hardware, 15 % on services and tests. Engineering effort excludes the test campaigns (counted from the test plan, `docs/test-plan.md`).

## What this tells us

- A flight of this design is a **multi-million-dollar, multi-year programme**, far beyond hobby scale. Even the cheapest credible flight (core, no imaging) costs about 3.9 M cash.
- The **precursor path** (FlatSat, balloon flight, ground station, the open design and the verified tooling) costs about 0.8 M in cash at these assumptions and is mostly labour; it retires most software, electronics and link
  risk and is the natural first stage for sponsors and partners. Much of it can be reduced further with volunteers and donated parts.
- Cost drivers to attack first: launch price (rideshare aggregators, university programmes), the thruster (a decision on whether a lighter, cheaper propulsion option meets the mission), solar cell count (single-sided or
  smaller wings), the number of science instruments (research-level ones are optional), and test facilities (share campaigns with partners, use university facilities).
- Reducing scope is the strongest lever: dropping imaging saves about 0.6 M, dropping the propulsion and its consequences (disposal, collision avoidance) would save about 0.4-0.7 M but conflicts with the 25-year disposal
  guideline at 700 km unless the orbit is lower (`docs/orbit-and-debris.md`).

## Assumptions and limits

- No vendor quotes; several items (thruster, hyperspectral, GRB detector, TSI radiometer) could be off by more than 2x.
- Labour value at 90 000 USD per person-year is a professional rate; volunteers and partners change the cash needed but not the effort.
- Launch prices vary widely with provider, orbit and date; a dawn-dusk sun-synchronous slot at 700 km may cost more than a mid-inclination slot.
- Not included: cost of failure (a second unit), insurance beyond the allowance, taxes and import duties, currency effects, cost of the science analysis after launch, and operations over decades
  (about one to two people plus ground stations; not modelled).
- The FlatSat is assumed at 40 % of core electronics hardware cost; the balloon flight at 8-30 k.

## Next

- Ask vendors for indicative quotes (thruster, cells and panels, optics, launch aggregators) and replace the ranges.
- Build the scenario table for the sponsor brief (`docs/sponsor-brief.md`, to be written) with the precursor as stage one.
