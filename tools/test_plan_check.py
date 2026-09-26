"""Check that every requirement is covered by a planned test (or explicitly waived) and generate docs/test-plan.md.

Usage: python tools/test_plan_check.py
"""
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
LEVELS = ["component", "board", "subsystem", "system", "environmental", "precursor", "ground", "review"]
EXTERNAL_COST = {"none": 0, "low": 1, "medium": 2, "high": 3}


def main():
    reqs = tomllib.load(open(os.path.join(ROOT, "mission", "traceability.toml"), "rb"))["req"]
    plan = tomllib.load(open(os.path.join(ROOT, "mission", "tests.toml"), "rb"))
    tests, waive = plan["test"], plan.get("waive", {})
    req_ids = {r["id"] for r in reqs}
    errors = []
    covered = {}
    ids = set()
    for t in tests:
        if t["id"] in ids:
            errors.append(f"duplicate test id {t['id']}")
        ids.add(t["id"])
        if t["level"] not in LEVELS:
            errors.append(f"{t['id']}: unknown level {t['level']}")
        if t["external"] not in EXTERNAL_COST:
            errors.append(f"{t['id']}: unknown external cost class")
        for rid in t["covers"]:
            if rid not in req_ids:
                errors.append(f"{t['id']}: unknown requirement {rid}")
            covered.setdefault(rid, []).append(t["id"])
    for rid in waive:
        if rid not in req_ids:
            errors.append(f"waiver for unknown requirement {rid}")
    uncovered = [r["id"] for r in reqs if r["id"] not in covered and r["id"] not in waive]
    for rid in uncovered:
        errors.append(f"requirement {rid} has no planned test and no waiver")

    by_level = {lv: [t for t in tests if t["level"] == lv] for lv in LEVELS}
    total_days = sum(t["effort_days"] for t in tests)
    ext_days = {k: sum(t["effort_days"] for t in tests if t["external"] == k) for k in EXTERNAL_COST}
    md = ["# Verification and test plan (generated)", "",
          "Source: `mission/tests.toml` against `mission/traceability.toml`; generated and checked by `python tools/test_plan_check.py`. Effort figures are estimates in engineer-days for one campaign.", "",
          f"{len(tests)} planned activities, {len(covered)} requirements covered by tests, {len(waive)} waived (analysis only, with a reason); {len(uncovered)} uncovered. Total effort about {total_days} engineer-days "
          f"(about {total_days / 220:.1f} person-years), of which {ext_days['medium'] + ext_days['high']} days involve medium/high-cost external facilities.", "",
          "## Approach", "",
          "1. Verify by analysis first (the automatic checks of `sim/trace_check.py`), then confirm with test at the lowest level where the risk can be retired.",
          "2. Build the integrated **FlatSat** early: it exercises the electronics, firmware, protocol and mission simulation on real hardware long before flight hardware exists.",
          "3. A **high-altitude balloon** precursor flies the computers, cameras, LoRa/GNSS and the ground chain (`PRE-01`), retiring software and link risk cheaply.",
          "4. Environmental tests (vibration, shock, thermal vacuum, EMC, battery safety) use the launch provider's levels; qualification level and acceptance level are decided with the provider.",
          "5. Every severity >= 4 failure mode of the FMEA is injected on the FlatSat (`SYS-03`).", "",
          "## Test list", ""]
    for lv in LEVELS:
        if not by_level[lv]:
            continue
        md += [f"### {lv.capitalize()}", "", "| ID | Activity | Covers | Method | Days | External |", "|---|---|---|---|---|---|"]
        for t in by_level[lv]:
            md.append(f"| {t['id']} | {t['name']} | {', '.join(t['covers'])} | {t['method']} | {t['effort_days']} | {t['external']} |")
        md.append("")
    md += ["## Requirement coverage", "", "| Requirement | Planned tests | Note |", "|---|---|---|"]
    for r in reqs:
        ts = covered.get(r["id"], [])
        note = waive.get(r["id"], "")
        md.append(f"| {r['id']} | {', '.join(ts) if ts else '-'} | {('waived: ' + note) if note else ''} |")
    md += ["", "## Facilities and external cost drivers", "",
           f"- No external facility: {ext_days['none']} engineer-days (FlatSat, board work, software, ground).",
           f"- Low: {ext_days['low']} days; medium: {ext_days['medium']} days; high: {ext_days['high']} days (radiation screening, thermal vacuum, thruster tests are the cost drivers).", "",
           "## Open items", "", "- Choose facilities and quotes; align test levels with the launch provider's requirements; decide flight-model versus proto-flight approach (one flight model reduces cost, raises risk).",
           "- Write detailed procedures per test with pass/fail criteria linked to the requirement text; keep the results in the repository next to the requirement that they verify."]
    open(os.path.join(ROOT, "docs", "test-plan.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    if errors:
        for e in errors:
            print("TEST PLAN error:", e)
        print(f"TEST PLAN coverage FAILED ({len(errors)} errors)")
        return 1
    print(f"TEST PLAN coverage OK: {len(tests)} tests, {len(covered)} requirements covered, {len(waive)} waived, effort {total_days} days; wrote docs/test-plan.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
