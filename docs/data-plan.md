# Science data plan (draft v0)

Tools: `sim/data_budget.py`, `configs/12u_data.toml`.

- Non-imaging science data: ~44 MB/day compressed (P1 17 MB must-have, P2 26 MB, P3 ~0).
- S-band (1 Mbps, 65 % efficiency, 7 min pass): ~34 MB per pass, ~170 MB/day per station.
- One S-band station therefore carries all science data plus ~54 telescope images per day, or ~2.5
  hyperspectral scenes; ten volunteer stations carry an order of magnitude more.
- UHF LoRa (~0.7 MB/day) only carries housekeeping subsets and beacons.

Strategy: priority queue on board (P1 streams first, imaging fills the remainder), on-board
compression and selection (cloud/target selection on the Jetson), store-and-forward with
CFDP-style resume, and open publication of all data.

Open items: real compression ratios per instrument, on-board storage sizing and retention policy,
S-band ground station availability in the volunteer network, and a full link budget.
