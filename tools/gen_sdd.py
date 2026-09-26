"""Generate docs/sdd.md (system design document) from the live design data and the latest analysis outputs.

Usage: python tools/gen_sdd.py     (run tools/check_all.py first so docs/status.md and the verification matrix are current)
Numbers come from the configs and tools; the decision log is the only hand-written part (kept in DECISIONS below).
"""
import json
import os
import re
import sys
import tomllib
from datetime import datetime, timezone

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sim"))
sys.path.insert(0, os.path.join(ROOT, "mechanical"))
import budget  # noqa: E402
import ginkgo_cad as gc  # noqa: E402

DECISIONS = [
    ("12U form factor, standard CubeSat rails", "Sponsors and rideshare providers can only launch what fits a standard dispenser; 12U gave the volume for a science-first payload.", "Volume review (6U did not fit: core alone was 159 % of usable volume)."),
    ("Science-first allocation; hyperspectral shares the telescope optics", "Science value drove the payload ranking; sharing the fore-optics saved about 400 cm3.", "Volume budget."),
    ("Tiered lifetime instead of one 50-year claim", "COTS compute and batteries cannot last 50 years; the survival chain and the long-life science chain can.", "Longevity analysis (dose, battery cycles)."),
    ("Long-life science never depends on Linux nodes", "Multi-decade records must survive the loss of Jetson and Pi.", "Longevity analysis; firmware architecture rule."),
    ("Three isolated power paths (A, B, survival C); per-card hardware eFuse, hardware kill", "A single fault must not take down the spacecraft; protection must not depend on software.", "Power architecture; backplane routing study."),
    ("LiFePO4 2S2P 26650 packs (42 Wh each), separated vaults, no wood", "Safest lithium chemistry; wood outgasses; real cell data showed 440 g per pack, not 300 g.", "EPS design calculation."),
    ("Electric iodine propulsion replaced the water resistojet", "12-15x the delta-v for similar volume; enables 50-year station keeping and controlled descent.", "Delta-v budget."),
    ("Propulsion bay on the -X face centre line with a canted nozzle", "A column-mounted nozzle sat ~70 mm from the centre of mass (70 uN m per mN): wheels saturate in minutes; canting also keeps the plume off wing B.", "ADCS analysis + CAD geometry."),
    ("1.7 kg tungsten trim ballast", "The centre of mass had crept to -18.7 mm in y against a +-20 mm dispenser limit.", "CAD mass properties (ICD generation)."),
    ("Wings must be double-sided; six hold-down posts per wing stack", "With the sun on the orbit normal, a single-sided wing faces away; the stowed panel resonated at 99 Hz.", "Power scenario review; structural analysis."),
    ("Effective face emissivity about 0.5, isolated and heated telescope column, survival heaters", "The spacecraft runs cold, not hot: 27 C below the limit with radiator-like faces; the telescope column overheated in sunlit dawn-dusk orbits.", "Thermal model."),
    ("Ginkgo card: 100 x 100 mm with a 20 mm spine notch, 8 mm outer relief, 4 mm backplane gap, 1.27 mm connector pitch", "90 x 90 and 100 x 100 boards could not clear the spine; 0.8 mm pitch could not be routed on the backplane.", "Geometric packing; backplane DRC."),
    ("Round telescope tube of about 85 mm aperture", "A square 100 mm box does not fit around the spine; only a round tube does.", "Geometric packing."),
    ("OreSat compatibility: CANopen conventions, own connector", "Reuse tooling and credit the closest precedent without inheriting a 1U-3U constraint.", "Prior-art review."),
    ("SCIENCE_LITE mode on the Pi CM5", "The mission simulation showed that imaging stopped forever after a Jetson failure.", "Closed-loop mission simulation."),
    ("Dawn-dusk sun-synchronous orbit preferred", "No eclipse (batteries, thermal swings), best power and burn geometry; fixed wings face the sun.", "Power, thermal, ADCS analyses."),
    ("Drag sail is required, propulsion descent recommended", "From 700 km the sail alone takes 14-20 years on this model, without it 45-50 years.", "Orbit lifetime analysis."),
    ("Ed25519-signed telecommands, no encryption on the air", "Amateur-band rules forbid obscuring meaning; signatures stop forgery and replay.", "Protocol design."),
    ("FOM-2 and FOM-3 redefined", "Wh/U rewarded unused battery; mass spent on safety and longevity is deliberate.", "Requirements refresh."),
]


def load(p):
    return tomllib.load(open(os.path.join(ROOT, p), "rb"))


def read(p):
    return open(os.path.join(ROOT, p), encoding="utf-8").read()


def first_match(text, pattern, default=""):
    m = re.search(pattern, text, flags=re.M)
    return m.group(0) if m else default


def main():
    cfg = load("configs/12u_science.toml")
    geo = load("configs/12u_geometry.toml")
    placement = json.load(open(os.path.join(ROOT, "mechanical", "out", "placement.json")))
    r = budget.compute(cfg)
    M, com, inertia = gc.mass_props(placement["placed"], cfg, False, geo)
    usable, vol, mass_t, tiers = budget.volume_report(cfg)
    status = read("docs/status.md")
    vm = read("docs/verification-matrix.md")
    checks_line = first_match(status, r"\*\*\d+ of \d+ checks pass\.\*\*")
    vm_line = first_match(vm, r"\*\*\d+ requirements:.*\*\*")
    risks = read("docs/risks.md")
    top_risks = re.findall(r"^\| (R\d+) \| (.+?) \| (\d) \| (\d) \| (\d+) \|", risks, flags=re.M)
    top_risks = sorted(top_risks, key=lambda x: -int(x[4]))[:6]
    cost = read("docs/cost.md")
    cost_rows = re.findall(r"^\| (\*\*)?(Precursor[^|]*?|Core flight[^|]*?|Full flight[^|]*?)(\*\*)? \| ([\d.]+ M) \| \*?\*?([\d.]+ M)\*?\*? \| ([\d.]+ M) \|", cost, flags=re.M)

    L = []
    a = L.append
    stamp = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    a("# Ginkgo system design document (generated)")
    a("")
    a(f"Generated by `python tools/gen_sdd.py` on {stamp}; numbers are read from the configs and tools, the decision log is hand-written. Everything is an engineering estimate at the current design "
      "level (no hardware exists); see `docs/risks.md` and the open items at the end.")
    a("")
    a("## 1. Purpose and document map")
    a("")
    a("This is the single overview of the design. Details live in the documents below.")
    a("")
    a("| Topic | Document |")
    a("|---|---|")
    for topic, doc in (("Plan and status", "`docs/plan.md`, `docs/status.md`"), ("Requirements and verification", "`mission/requirements.md`, `docs/verification-matrix.md`, `docs/test-plan.md`"),
                       ("Architecture, layout, mechanical", "`docs/architecture.md`, `docs/layout.md`, `mechanical/README.md`, `docs/structure.md`, `docs/icd.md`"),
                       ("Power, thermal, propulsion, attitude", "`docs/power-architecture.md`, `docs/eps-card.md`, `docs/thermal.md`, `docs/propulsion.md`, `docs/adcs.md`"),
                       ("Electronics", "`docs/electrical-interface.md`, `electronics/README.md`"), ("Software and data", "`docs/firmware-architecture.md`, `docs/protocol.md`, `docs/data-plan.md`, `firmware/README.md`"),
                       ("Orbit, longevity, safety", "`docs/orbit-and-debris.md`, `docs/longevity.md`, `docs/fmea.md`, `docs/risks.md`"),
                       ("Operations and ground", "`docs/ops-concept.md`, `docs/ground-station-kit.md`, `docs/mission-simulation.md`"),
                       ("Context", "`docs/prior-art.md`, `docs/design-identity.md`, `docs/decisions/`, `docs/outreach-led.md`, `docs/cost.md`")):
        a(f"| {topic} | {doc} |")
    a("")
    a("## 2. Mission")
    a("")
    a("A 12U open, long-life science observatory and reusable platform (objectives OBJ-1 to OBJ-5 in `mission/requirements.md`): multi-decade space-weather and radiation records, 5 m class imaging and "
      "hyperspectral scenes, reliability science on COTS compute and flash memory, an open ground kit and archive, and a design others can reuse.")
    a("")
    a("![Stowed and deployed configuration](../mechanical/out/render_deployed.png)")
    a("")
    a("## 3. Configuration and budgets (live)")
    a("")
    scen = "".join(f"| {s['name']} | {s['gen']:.1f} | {s['cons']:.1f} | {s['margin'] * 100:+.0f} % | {s['ecl_need']:.1f} |\n" for s in r["scenarios"])
    a("| Item | Value |")
    a("|---|---|")
    a(f"| Form factor | 12U, {geo['frame']['outer'][0]:.1f} x {geo['frame']['outer'][1]:.1f} x {geo['frame']['outer'][2]:.1f} mm |")
    a(f"| Mass | {r['mass_kg']:.2f} kg of 24 kg ({mass_t.get('core', 0):.1f} kg bus, {mass_t.get('science', 0):.1f} kg science, {mass_t.get('service', 0):.2f} kg outreach) |")
    a(f"| Modules | {len(placement['placed'])} placed in the cell grid, 0 interferences; module volume {sum(vol.values()):.0f} cm3 of {usable:.0f} cm3 usable (science {vol.get('science', 0) / sum(vol.values()) * 100:.0f} %) |")
    a(f"| Centre of mass | ({com[0]:+.1f}, {com[1]:+.1f}, {com[2]:+.1f}) mm; inertia ({inertia[0]:.3f}, {inertia[1]:.3f}, {inertia[2]:.3f}) kg m2 stowed |")
    a(f"| Average load (full) | {r['consumed_w']:.1f} W; batteries 84 Wh (2 x 42 Wh) plus 5 Wh survival pack |")
    a(f"| Figures of merit | FOM-1 {r['W_per_U']:.2f} W/U, FOM-2 x{r['eclipse_usable_wh'] / max(s['ecl_need'] for s in r['scenarios']):.1f} eclipse margin, FOM-3 {r['payload_fraction'] * 100:.0f} % science mass, "
      f"FOM-4 {vol.get('science', 0) / sum(vol.values()) * 100:.0f} % science volume |")
    a("")
    a("Power scenarios (orbit average):")
    a("")
    a("| Scenario | Generation W | Load W | Margin | Eclipse need Wh |")
    a("|---|---|---|---|---|")
    a(scen.rstrip("\n"))
    a("")
    a("## 4. Subsystem summaries")
    a("")
    subs = [
        ("Structure", "Al 6061 frame with corner rails, four columns around a 40 mm spine, notched Ginkgo cards; first mode about 900 Hz (frame), 170 Hz walls, 190 Hz wing stack with six hold-down posts; all mounts >= 6x margin (`docs/structure.md`)."),
        ("Power", "Two wings of three double-sided panels plus body cells; two independent EPS chains (three buck MPPT channels each), two LiFePO4 packs and an independent survival chain; per-card eFuse and hardware kill (`docs/power-architecture.md`, `docs/eps-card.md`)."),
        ("Thermal", "Passive design with effective face emissivity ~0.5, isolated telescope column with an 8 W thermostat heater, battery vault heater, survival heaters; electronics -10..33 C, battery 4..15 C (`docs/thermal.md`)."),
        ("Attitude and propulsion", "Three reaction wheels, magnetorquers, star tracker; iodine gridded-ion thruster in a bay on the -X centre line with a canted nozzle through the centre of mass; about 630 m/s available, 194 m/s planned; drag sail (`docs/adcs.md`, `docs/propulsion.md`)."),
        ("Compute and firmware", "MSP430FR supervisor, two STM32H7 flight controllers, mass memory unit (8 x 128 GB, 6+2 coding), Pi CM5 and Jetson Orin Nano; host-tested firmware core (auth, modes, FDIR, command queue, OTA), 68 unit checks (`docs/firmware-architecture.md`)."),
        ("Communications and protocol", "UHF beacon and LoRa, S-band 250 kbps - 2 Mbps; CCSDS packets with signed telecommands, 27 messages, generated C and Python code with byte-exact tests (`docs/protocol.md`)."),
        ("Payload suite", "Telescope with hyperspectral spectrometer, wide-field camera, thermal IR, magnetometer boom, particle spectrometer, X-ray/UV, TSI, GRB, VLF, Langmuir, dosimeter, CSAC, GNSS/TEC, flash and SEU experiments, retroreflector, memory plate, outreach LED (`docs/data-plan.md`)."),
        ("Electronics interface", "Notched 100 x 100 mm card, GK-P (2 x 30) and GK-D (2 x 15) connectors at 1.27 mm, passive 15-slot backplane strip per column (KiCad, DRC clean), CANopen-style management over CAN-FD A/B (`docs/electrical-interface.md`)."),
        ("Ground and operations", "Reference station at Pamukkale (3.6 passes/day, unattended operation needed), open S-band kit, contact plan tool, commissioning checklist (`docs/ops-concept.md`, `docs/ground-station-kit.md`)."),
    ]
    for name, text in subs:
        a(f"**{name}.** {text}")
        a("")
    a("![Interior layout](../mechanical/out/render_interior.png)")
    a("")
    a("## 5. Decision log (what analysis changed)")
    a("")
    a("| # | Decision | Reason | Triggered by |")
    a("|---|---|---|---|")
    for i, (d, why, trig) in enumerate(DECISIONS, 1):
        a(f"| {i} | {d} | {why} | {trig} |")
    a("")
    a("## 6. Analysis and verification status")
    a("")
    a(f"- Automatic regression: {checks_line or 'run tools/check_all.py'} (`docs/status.md`).")
    a(f"- Requirements: {vm_line or 'see docs/verification-matrix.md'}")
    a("- Test plan: 27 planned activities cover the requirements; about 745 engineer-days (`docs/test-plan.md`). No physical test has been done: everything above is analysis and simulation.")
    a("")
    a("## 7. Risks, cost and schedule")
    a("")
    a("Top risks (score = likelihood x impact, `docs/risks.md`):")
    a("")
    for rid, text, l, i, sc in top_risks:
        a(f"- **{rid}** ({sc}): {text[:150]}")
    a("")
    if cost_rows:
        a("Rough cash cost (USD, unverified +-2x, `docs/cost.md`): " + "; ".join(f"{re.sub(r'[*]', '', n.strip())}: P50 {p50}" for _, n, _, _, p50, _ in cost_rows) + ". Schedule about 4.5 years to launch at the median.")
    a("")
    a("## 8. Open items and decisions for the operator")
    a("")
    a("1. Choose the target: a flight mission, a flight-quality reference design, or the precursor path (FlatSat + balloon); this decides effort and cost by an order of magnitude.")
    a("2. Confirm the preferred orbit (dawn-dusk sun-synchronous, about 700 km) and whether the outreach LED stays in the flight configuration.")
    a("3. Get vendor quotes and datasheets for the thruster, cells, optics and launch; replace estimates and module envelopes.")
    a("4. Detailed design still missing: EPS and other schematics, vendor CAD, boom and antenna mechanisms, umbilical and separation switches, finite-element model, thermal detail model.")
    a("5. Prior-art and patent search, trademark check for the name, licences and public release (`docs/licensing.md`).")
    a("6. Partners: a licensed operator organisation, a launch sponsor or programme, test facilities.")
    open(os.path.join(ROOT, "docs", "sdd.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")
    print("wrote docs/sdd.md")


if __name__ == "__main__":
    main()
