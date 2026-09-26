# Propulsion budget (draft v0.2)

Decision: **electric propulsion** (iodine gridded-ion / Hall class) replaces the water resistojet. It is
used only when needed; during a burn every non-essential service is shut down ("burn mode").
All numbers below are estimates; confirm with thruster datasheets and vendors.

## Why electric
- Isp 1500-2500 s versus ~80 s for water: about 0.7-1 g of propellant per 1 m/s instead of ~18 g.
- 0.5 kg of iodine gives roughly 500-700 m/s (water: 0.8 kg gives ~45 m/s).
- That covers 50 years of drag makeup even at ~600 km (~110 m/s), many collision-avoidance burns, and
  a **controlled deorbit** from 700 km (~100 m/s). The drag sail stays as the passive backup.
- Volume is similar (about 1000 cm3 versus 1200 cm3 for the water system); mass is higher (~2 kg).
- Iodine is stored as a solid at low pressure, which suits launch safety.

## Cost
- Power ~40-65 W while firing (budgeted 50 W); thrust only ~0.3-1 mN.
- Burn time for 14 kg: 0.3 m/s (avoidance) ~1-2.5 h; 1 m/s ~4-8 h; 22 m/s ~4-7 days; 100 m/s (deorbit)
  ~17-33 days of accumulated thrusting.
- Emergency avoidance therefore needs 24-48 h notice (CDMs give days) and burns spread over several
  sunlit passes.

## Placement and thrust line

The thruster sits in a **propulsion bay on the -X face centre line** (y = 0, mid-height) and is canted about 8.6 deg (y) and 2.9 deg (z) so the thrust line
passes through the centre of mass; see `docs/adcs.md`. The cant also keeps the exhaust cone clear of wing B (12 deg half-angle assumed).

## Burn mode (minimal services)
- All payloads and heavy computers off; ADCS, flight controller, supervisor, comms RX, heaters stay on.
- Thruster runs **only in sunlight**; the eclipse is covered by the normal (minimal) load.
- Sun-biased attitude required; not possible while tumbling (28 W average is below the 50 W burn).
- Attitude constraint: thrust along the velocity vector while the fixed wings face the sun. This is
  compatible in a **dawn-dusk sun-synchronous orbit** (sun normal to the orbit plane); in other orbits
  it needs a rotatable wing axis or accepts reduced power.

## Risks
- Iodine is corrosive and can contaminate optics, solar cells and radiators: keep the thruster away
  from the telescope aperture and cells, choose plume-tolerant materials, add shielding.
- Neutraliser and grid wear over hundreds of hours; thermal management of the thruster.
- Lower thrust than the water resistojet (~4 mN): slower response for urgent burns.
- Option: xenon is cleaner but needs a heavier high-pressure tank. Both options, or a water resistojet
  as well, would cost about +1000 cm3, which the 12U volume budget cannot absorb.

## Superseded (water resistojet)
0.8 kg of water gave ~45 m/s (about 18 g per m/s), was consumed, and could not do a deorbit.
