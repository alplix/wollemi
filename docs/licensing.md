# Licensing plan (draft; nothing is applied while the repository is private)

Goal: everyone can study, build, modify and share the design, and improvements to the hardware stay open. The operator decides the final licences before the repository is made public.

## Recommended timing

The design is at analysis-level freeze candidate v0 (`docs/status.md`, `docs/sdd.md` section 8): 22 automatic checks pass, 47 requirements traced (28 auto PASS, 8 designed, 11 open), reviewed by three independent passes.
Nothing has been built or tested. Recommendation, in order:
1. **Trademark check** (item 3 below) before anything else — it can force a rename, which is far cheaper to do now than after release. (The project was in fact renamed once already, from "Ginkgo" to "Wollemi", after this check found "GINKGO" was a live US trademark of Ginkgo Bioworks, Inc. covering computer hardware/software design services, and a same-named unrelated open-source HPC library.)
2. **Apply the licence texts and SPDX headers** (item 1) while still private, as a mechanical step that can happen at any time; it does not by itself make the repository public. **Done** (2026-09-27): `LICENSES/` holds the real, authoritative texts (fetched from apache.org, creativecommons.org and the SPDX licence-list API, not retyped from memory) for CERN-OHL-S-2.0, Apache-2.0, CC-BY-4.0 and CC0-1.0, plus a `LicenseRef-tweetnacl-public-domain.txt` for the one third-party file. `REUSE.toml` at the repository root declares the licence for every path per the table below (the [REUSE](https://reuse.software/) convention). The firmware core (`firmware/common/`, `firmware/tests/`) and the generated protocol implementations additionally carry inline SPDX headers, since those files are the most likely to be copied out of this repository on their own.
3. **Make the repository public** once one of these is true: (a) a sponsor or launch conversation actually starts and the design needs to be inspectable, (b) the precursor path (FlatSat/balloon) begins and the project wants outside contributors, or (c) the operator simply decides the analysis-level design is mature enough to invite review — whichever comes first. This is the operator's call, not a technical gate; the checklist below is what has to be true *before* that button is pressed, not a recommendation to press it now.

## Proposed licences by directory

| Content | Directories | Licence (SPDX id) | Why |
|---|---|---|---|
| Hardware design (electronics, mechanical models and generators, configs that define the hardware, ICD-level data) | `electronics/`, `mechanical/`, `configs/` | `CERN-OHL-S-2.0` | strongly reciprocal: derivative hardware must stay open |
| Software and tools (analysis tools, firmware core, protocol generator, ground software, checks) | `sim/`, `firmware/common/`, `firmware/tests/`, `protocol/`, `groundstation/`, `tools/` | `Apache-2.0` | permissive with an explicit patent grant; friendly to companies and space agencies |
| Documentation and figures | `docs/`, `mission/`, `README.md`, renders in `mechanical/out/` | `CC-BY-4.0` | attribution only |
| Third-party code | `firmware/third_party/` | keep each upstream licence (TweetNaCl: public domain) | not ours |
| Data products (future) | archive of mission data | `CC0-1.0` or `CC-BY-4.0` | maximum reuse of scientific data |

Alternatives to consider before deciding: CERN-OHL-W (weakly reciprocal) if strong reciprocity would discourage adoption by agencies; a single licence for everything (simpler, but a poor fit for hardware).

## Before going public (checklist)

1. **Done.** Licences decided above; official texts in `LICENSES/`, path-based declarations in `REUSE.toml`, inline SPDX headers on the firmware core and the generated protocol files.
2. Prior-art and patent search (`docs/prior-art.md` lists what to check: card/backplane CubeSat structures, backplane form factors); credit OreSat and others in `CREDITS.md`.
3. **Trademark check for the name "Wollemi" (the project's second name; the first, "Ginkgo", was dropped for exactly this reason -- see below):**
   - **History:** the project was originally named "Ginkgo". A check found "GINKGO" is a live registered US trademark (Ginkgo Bioworks, Inc., Reg. No. 5436236, filed 2017) whose Class 42 coverage explicitly includes *"design and development of computer hardware and software"* -- not a clean different-field case, since this project is exactly hardware-and-software design -- and that a separate, unrelated open-source HPC/linear-algebra library was already using the same name. Both were real, current conflicts, not hypothetical ones, so the project was renamed to "Wollemi" (after the Wollemi Pine, a "living fossil" tree rediscovered alive in 1994 after being known only as a fossil) while the repository is still small and private.
   - **Wollemi, initial check:** a search did not turn up a live trademark or an existing software/aerospace project using "Wollemi" (searched for trademark, software and aerospace/satellite/open-source-project usage). No conflict found at this pass.
   - This is still **not a formal legal clearance** -- that needs USPTO TESS / EUIPO / WIPO Global Brand database searches in the actual relevant classes, done by someone qualified to interpret them -- and should be done properly before public release, but the initial check that caught the Ginkgo conflict does not repeat for Wollemi.
4. Review the repository for private data: personal location details (the home ground station site), keys (none are stored; the Ed25519 test keys are generated at run time), tokens, and file paths.
5. Add a clear disclaimer: analysis-level design, no warranty, not qualified for flight, no safety or regulatory approval; users must do their own review.
6. Decide the governance model: who may merge, how design changes are reviewed, how the requirements matrix is kept honest, and how the operator-of-record role relates to the open community.
7. Export-control and safety notes for parts (propulsion, cells, batteries) where relevant; nothing here is a legal opinion.
8. Publish the release with a signed tag and the generated documents (SDD, status) for that revision.

## Contributions

- Developer certificate of origin (sign-off) is preferred over a contributor licence agreement to keep the barrier low.
- Every contribution must pass `python tools/check_all.py` and update the affected requirement, analysis or test entry.
- Hardware contributions must include the source files (KiCad, generator scripts), not only exports.

## Notes

- Files generated by tools (STEP, STL, PNG, generated C and Python) inherit the licence of the sources that produce them.
- KiCad, build123d, numpy, scipy, Pillow, cryptography and sgp4 are used as tools; the design files are not encumbered by their licences.
- This document is a plan, not legal advice.
