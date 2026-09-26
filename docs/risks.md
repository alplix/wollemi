# Risk register (draft v0)

Likelihood (L) and impact (I) on a 1-5 scale; score = L x I. Mitigations are actions we can take before hardware exists. Reviewed by hand; extend as analyses mature.

| # | Risk | L | I | Score | Mitigation / next action |
|---|---|---|---|---|---|
| R1 | **No launch opportunity or sponsor** (12U rideshare, orbit >= 700 km, cost) | 4 | 5 | 20 | Tiered variants (`configs/`), sponsor brief, use the design as a reusable platform even without a flight; approach agencies and rideshare providers early |
| R2 | **Operator of record, frequency coordination and licensing** not in place (amateur bands, IARU, national authority) | 4 | 5 | 20 | Find a licensed operator/organisation partner; start coordination once the design is frozen (REG-1, COLAV-1) |
| R3 | **Single-person project scope** (5 processors, 26 instruments, firmware, ground) | 5 | 4 | 20 | Freeze a core mission; make research-level payloads optional; open the repository so others can own subsystems |
| R4 | **Cost** far beyond a hobby budget (cells, thruster, optics, tests) | 5 | 4 | 20 | Cost model per tier; sponsor packages; reuse commercial parts; start with a FlatSat and a balloon flight |
| R5 | **Double-sided thin wing panels (2.1 mm)** may not meet stiffness, mass or cost (PWR-5) | 3 | 4 | 12 | Prototype a panel; alternatives: wings on one side of the body only with reduced power, or 2 panels per wing with a recessed wall |
| R6 | **Residual magnetic dipole > 0.1 A m2** compromises the magnetometer and control | 4 | 3 | 12 | Magnetic cleanliness programme, material screening, dipole compensation, boom; measure on an engineering model |
| R7 | **Iodine thruster** power, thrust, plume or corrosion differ from the estimate (contamination of optics, cells, radiators) | 3 | 4 | 12 | Vendor data and plume map, contamination shielding, place thruster away from optics; keep the drag sail as passive backup |
| R8 | **Telescope pointing stability** (structural modes, wheel micro-vibration) worse than the rigid-body estimate | 3 | 4 | 12 | Modal analysis, isolators, jitter test on an engineering model; relax GSD or use TDI |
| R9 | **COTS compute (Jetson, Pi) dies early** from radiation or latch-up | 4 | 2 | 8 | Already tiered: science chain does not depend on Linux nodes (LONG-2); spot shielding; treat as consumables |
| R10 | **Volume estimates wrong** (bounding boxes, +-30 %) | 3 | 3 | 9 | Replace with vendor CAD as parts are chosen; 41 % of the interior is still free but fragmented |
| R11 | **Thermal model wrong** (coatings, conduction estimated) | 3 | 3 | 9 | Detailed nodal model, thermal-vacuum test; heaters give margin; dawn-dusk orbit preferred |
| R12 | **Thermal cycling fatigue** of solder joints (5000+ cycles/yr in eclipse orbits) | 3 | 3 | 9 | Design rules (CTE match, underfill, conformal coating), test; dawn-dusk orbit reduces cycling |
| R13 | **Volunteer S-band ground network too thin**; only the home station at Pamukkale (3.6 passes/day) | 3 | 3 | 9 | Ground kit design, at least two anchor stations, UHF beacon as fallback |
| R14 | **Collision avoidance response time** (few passes/day, commands 24-48 h ahead) | 3 | 4 | 12 | Second station for commanding, autonomous burn execution, keep orbit >= 700 km where conjunctions are rarer |
| R15 | **Ed25519 signing and OTA not implemented**; security model not reviewed | 3 | 4 | 12 | Vetted library, tests, security review before any flight software release (COM-4) |
| R16 | **Debris or micrometeoroid strike** (1 mm - 1 cm class cannot be shielded or tracked) | 2 | 5 | 10 | Redundancy (A/B/C power, computer hierarchy, survival chain), Whipple protection on tank and batteries |
| R17 | **Battery ageing** faster than modelled (LiFePO4 at 5000 cycles/yr) | 3 | 3 | 9 | Larger pack (done), sun-only mode, survival pack; test cells for the LEO cycling profile |
| R18 | **Deployment failure** of wings or antenna | 2 | 4 | 8 | Body cells alone keep safe mode alive (10.9 W vs 3.1 W); independent burn-wire supply on the survival bus |
| R19 | **Parts sourcing and export controls** (iodine thruster, triple-junction cells, Jetson) | 3 | 3 | 9 | Identify alternatives per part; check regulations early; keep interfaces vendor-neutral |
| R20 | **Requirements drift** between design documents | 3 | 2 | 6 | Verification matrix (`sim/trace_check.py`) and configs as the single source keep documents consistent |
| R21 | **Name and trademark** ("Ginkgo") conflicts | 2 | 2 | 4 | Check trademarks before going public; the name is easy to change |
| R22 | **Prior-art or patent conflict** with card/backplane concepts | 2 | 3 | 6 | Prior-art review done (`docs/prior-art.md`), full search before publication; credit OreSat |

## Top actions right now

1. R1/R2/R3/R4: decide the real target: a flight mission, a flight-quality reference design, or a balloon/FlatSat first step (this decides the effort).
2. R5: prototype a double-sided panel and confirm the power model assumption.
3. R6: define a magnetic cleanliness plan before choosing parts.
4. R15: implement signature verification and tests.
5. R7/R8: obtain vendor data (thruster plume, optics tube modes).
