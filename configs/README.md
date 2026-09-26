# Configuration files

| File | Role | Status |
|---|---|---|
| `12u_science.toml` | modules (mass, power, duty, volume, tier), solar geometry, battery, power scenarios | maintained, single source of truth |
| `12u_geometry.toml` | frame, wings and a bounding box per module (flags: fixed, cyl, notched, end, align, tilt) | maintained |
| `12u_layout.toml` | which column and deck each module goes to, plus separation rules | maintained; reconciled with the real packing by `mechanical/reconcile.py` |
| `12u_data.toml` | data streams, link and storage assumptions | maintained |
| `12u_longevity.toml` | degradation, battery cycles and radiation assumptions | maintained |
| `12u_thermal.toml` | coatings, conductances, heaters, limits | maintained |
| `12u_structure.toml` | materials, launch loads, fasteners, wing hold-down | maintained |
| `12u_cost.toml` | rough cost and schedule ranges (unverified) | maintained |
| `2u_baseline.toml`, `3u_science.toml`, `6u_science.toml` | earlier variants (single-estimate budgets, no geometry) | **legacy**: kept for comparison and for the tier idea; not updated with the 12U changes |
