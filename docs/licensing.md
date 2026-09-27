# Licensing plan (draft; nothing is applied while the repository is private)

Goal: everyone can study, build, modify and share the design, and improvements to the hardware stay open. The operator decides the final licences before the repository is made public.

## Recommended timing

The design is at analysis-level freeze candidate v0 (`docs/status.md`, `docs/sdd.md` section 8): 22 automatic checks pass, 47 requirements traced (28 auto PASS, 8 designed, 11 open), reviewed by three independent passes.
Nothing has been built or tested. Recommendation, in order:
1. **Trademark check** (item 3 below) before anything else — it can force a rename, which is far cheaper to do now than after release.
2. **Apply the licence texts and SPDX headers** (item 1) while still private, as a mechanical step that can happen at any time; it does not by itself make the repository public.
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

1. Decide the licences above and add the official texts (SPDX `LICENSE` files or a `LICENSES/` directory following the REUSE convention) plus a short SPDX header in each source file.
2. Prior-art and patent search (`docs/prior-art.md` lists what to check: card/backplane CubeSat structures, backplane form factors); credit OreSat and others in `CREDITS.md`.
3. **Trademark check for the name "Ginkgo" -- real conflicts found, take this seriously before public release:**
   - **"GINKGO" is a live registered US trademark** (Ginkgo Bioworks, Inc., Reg. No. 5436236, filed 2017), and its Class 42 coverage explicitly includes *"design and development of computer hardware and software"* alongside its core biotech business -- not a clean different-field case, since this project is exactly hardware-and-software design. This does not automatically bar an open, non-commercial hobby project's use of the word, but it is a real conflict, not a hypothetical one, and it would be the first thing a lawyer flags.
   - **A separate, unrelated open-source project is already named "Ginkgo"**: a BSD-licensed linear-algebra/HPC library used in scientific computing, findable on GitHub and in academic papers. This creates a direct search-engine and community-discoverability collision inside the same broad space (open-source scientific software), independent of the trademark question.
   - Neither point is a formal legal clearance (that needs USPTO TESS / EUIPO / WIPO Global Brand database searches in the actual relevant classes, done by someone qualified to interpret them), but together they are enough that **a rename should be seriously considered**, and is far cheaper to do now, while the repository is small and private, than after any public release or sponsor conversation.
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
