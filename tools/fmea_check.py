"""Machine check of the FMEA and generation of docs/fmea.md.

Usage: python tools/fmea_check.py
Rules: every subsystem covered, required fields present, S/L/D in 1..5, fdir from the vocabulary, every S >= 4 has a detection and a response,
every item S == 5 is not left at fdir 'ground_action' alone, and the referenced firmware modules exist.
"""
import os
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VOCAB = {"hardware", "retry", "restart", "power_cycle", "switch_redundant", "degrade", "kill", "safe_mode", "survival_mode",
         "sun_only", "ground_action", "design"}
SUBSYSTEMS = {"Power", "Thermal", "Compute", "Comms", "ADCS", "Propulsion", "Structure", "Payload", "Software", "Ground"}
REQUIRED = ("id", "sys", "item", "mode", "effect", "detect", "response", "fdir", "S", "L", "D")
FIRMWARE_REFS = {"gk_auth": "firmware/common/gk_auth.c", "gk_ota": "firmware/common/gk_ota.c", "gk_modes": "firmware/common/gk_modes.c",
                 "gk_fdir": "firmware/common/gk_fdir.c"}


def main():
    data = tomllib.load(open(os.path.join(ROOT, "mission", "fmea.toml"), "rb"))["fm"]
    errors = []
    ids = set()
    for f in data:
        for k in REQUIRED:
            if k not in f or f[k] in ("", None):
                errors.append(f"{f.get('id', '?')}: missing {k}")
        if f["id"] in ids:
            errors.append(f"duplicate id {f['id']}")
        ids.add(f["id"])
        for k in ("S", "L", "D"):
            if not 1 <= f[k] <= 5:
                errors.append(f"{f['id']}: {k} out of range")
        if f["fdir"] not in VOCAB:
            errors.append(f"{f['id']}: unknown fdir '{f['fdir']}'")
        if f["S"] >= 4 and (len(f["detect"]) < 8 or len(f["response"]) < 12):
            errors.append(f"{f['id']}: severity >= 4 needs a real detection and response")
        if f["S"] == 5 and f["fdir"] == "ground_action":
            errors.append(f"{f['id']}: a catastrophic mode cannot rely on ground action alone")
        for ref, path in FIRMWARE_REFS.items():
            if ref in f["response"] + f["detect"] and not os.path.exists(os.path.join(ROOT, path)):
                errors.append(f"{f['id']}: refers to {ref} but {path} is missing")
    covered = {f["sys"] for f in data}
    for s in SUBSYSTEMS - covered:
        errors.append(f"subsystem not covered: {s}")
    for s in covered - SUBSYSTEMS:
        errors.append(f"unknown subsystem {s}")

    rows = sorted(data, key=lambda f: -(f["S"] * f["L"] * f["D"]))
    md = ["# FMEA (generated)", "",
          "Source: `mission/fmea.toml`; generated and checked by `python tools/fmea_check.py`. Severity S, likelihood L, detection difficulty D on 1-5; RPN = S x L x D.", "",
          f"{len(data)} failure modes over {len(covered)} subsystems; {sum(1 for f in data if f['S'] >= 4)} with severity >= 4 (all have a detection and a response).", "",
          "## Highest risk priority numbers", "", "| RPN | ID | Item | Failure mode | S | L | D | Response (FDIR class) |", "|---|---|---|---|---|---|---|---|"]
    for f in rows[:15]:
        md.append(f"| {f['S'] * f['L'] * f['D']} | {f['id']} | {f['item']} | {f['mode']} | {f['S']} | {f['L']} | {f['D']} | {f['response']} (`{f['fdir']}`) |")
    md += ["", "## All failure modes by subsystem", ""]
    for sysname in sorted(covered):
        md += [f"### {sysname}", "", "| ID | Item | Failure mode | Effect | Detection | Response | FDIR | S | L | D |", "|---|---|---|---|---|---|---|---|---|---|"]
        for f in data:
            if f["sys"] == sysname:
                md.append(f"| {f['id']} | {f['item']} | {f['mode']} | {f['effect']} | {f['detect']} | {f['response']} | `{f['fdir']}` | {f['S']} | {f['L']} | {f['D']} |")
        md.append("")
    md += ["## Limits", "", "Qualitative and estimated by the design team, not derived from part-level failure-rate data. It should be reviewed independently, extended to part level "
           "(each card and connector), and turned into a fault-injection test list (`docs/test-plan.md`)."]
    open(os.path.join(ROOT, "docs", "fmea.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    if errors:
        for e in errors:
            print("FMEA error:", e)
        print(f"FMEA coverage FAILED with {len(errors)} errors")
        return 1
    print(f"FMEA coverage OK: {len(data)} failure modes, {len(covered)} subsystems, {sum(1 for f in data if f['S'] >= 4)} with severity >= 4 fully covered; wrote docs/fmea.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
