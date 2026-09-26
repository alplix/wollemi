# Science data plan (draft v0)

Tools: `sim/data_budget.py`, `configs/12u_data.toml`.

- Non-imaging science data: ~44 MB/day compressed (P1 17 MB must-have, P2 26 MB, P3 ~0).
- S-band (1 Mbps, 65 % efficiency): reference site is the operator's home, **Pamukkale (37.9 N, 29.1 E)**. Orbit calculation
  (`groundstation/predict.py`, 700 km sun-synchronous): 3.6 passes/day of ~7.6 min (~27 min/day), ~37 MB per pass, about 134 MB/day.
  Other sites for comparison: Ankara 3.9, Singapore 2.7, a polar station ~9.7 passes/day.
- One S-band station at Pamukkale therefore carries all science data plus ~38 telescope images per day, or ~1.8
  hyperspectral scenes; ten volunteer stations carry an order of magnitude more; a polar station more than doubles a mid-latitude one.
- UHF LoRa (~0.5 MB/day) only carries housekeeping subsets and beacons.

Strategy: priority queue on board (P1 streams first, imaging fills the remainder), on-board
compression and selection (cloud/target selection on the Jetson), store-and-forward with
CFDP-style resume, and open publication of all data.

Open items: real compression ratios per instrument, on-board storage sizing and retention policy,
S-band ground station availability in the volunteer network, and a full link budget.
