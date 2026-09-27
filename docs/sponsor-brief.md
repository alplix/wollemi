# Wollemi sponsor brief (draft, one page)

*Analysis-level design, private repository. All numbers are engineering estimates with the uncertainty stated in `docs/cost.md`; nothing has been built or tested.*

## What it is

An open, modular **12U CubeSat observatory** (CubeSat envelope 226 x 226 x 340 mm, about 16.8 kg of the 24 kg limit) for long, continuous space-weather, radiation and Earth-observation data records,
with a tiered design life aimed at decades (survival chain 40+ years, long-record science 30-50 years, heavy compute about 10-15 years, batteries about 10 years in an eclipse orbit, no wear-out limit in a dawn-dusk orbit).
Everything is generated from configuration files and machine-checked (`docs/status.md`): mass, power, thermal, structure, orbit lifetime, protocol, firmware logic, CAD interferences.

## Why it is worth launching

- **Science per volume:** about 26 instruments (5 m class telescope with a shared-optics hyperspectral imager, thermal IR, magnetometer, particle spectrometer, X-ray/UV, TSI, VLF, GRB, GNSS/TEC, dosimetry, radiation-effects experiments).
- **Fully open:** design, protocol and data are meant to be public; anyone with a low-cost station can receive it; a public relay for licensed amateurs. Nothing is encrypted except command authentication (signed, not hidden).
- **Reusable platform:** the cell grid, notched 100 x 100 mm card and backplane are a standard other missions can reuse by changing configuration and cards.
- **Responsible by design:** electric propulsion for station keeping, collision avoidance and a propulsive descent, plus a drag sail as the passive backup (from 700 km: sail alone 14-20 years on this model).

## What a sponsor would be asked for

| Path | Scope | Cash estimate (P50, unverified, +-2x) | Time |
|---|---|---|---|
| Flight mission | Build, test, launch and operate the 12U | about 4.5 M USD (4.0-5.1 M modelled range) | about 4.5 years |
| Precursor | FlatSat plus a balloon flight to retire the largest risks first | about 0.85 M USD | shorter, then decide |
| Reference design | Release the design as an open, flight-quality reference; no flight | engineering effort only | - |

Ask list for a launch: a rideshare slot (12U, preferred dawn-dusk sun-synchronous orbit near 700 km), frequency coordination and amateur licensing (open, `REG-1`), an operator of record for conjunction data (`COLAV-1`).

## Honest state and open risks

- 28 of 47 requirements are checked automatically and pass, 8 are designed but unproven, 11 are open (licensing, operator, ground network, physical tests); `docs/verification-matrix.md`.
- No physical test yet: 29 planned test activities, about 780 engineer-days (`docs/test-plan.md`).
- Tightest items: interior volume (about 95 % of usable volume), safe-mode thermal margin (about 3 K above the electronics limit), a 50-year mission versus the 25-year disposal guideline (`LONG-4`), COTS compute radiation life, the cost and schedule model.
- Decisions the project owner has to take: target (flight, reference design or precursor), orbit, whether the violet LED beacon stays in the flight design (`docs/outreach-led.md`), when to open the repository and the licences (`docs/licensing.md`).

Start reading at `docs/sdd.md`.
