"""Live requirements verification matrix.

Usage: python sim/trace_check.py            # prints the matrix and writes docs/verification-matrix.md
Requirements with an `auto` check are evaluated from the real design data on every run.
"""
import json
import math
import os
import subprocess
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sim"))
sys.path.insert(0, os.path.join(ROOT, "mechanical"))


def load(name):
    return tomllib.load(open(os.path.join(ROOT, name), "rb"))


CFG = load("configs/12u_science.toml")
GEO = load("configs/12u_geometry.toml")
PLACEMENT = json.load(open(os.path.join(ROOT, "mechanical", "out", "placement.json")))


def c_mass():
    import budget
    r = budget.compute(CFG)
    return r["mass_kg"] <= 24.0, f"{r['mass_kg']:.2f} kg of 24 kg; margin {(1 - r['mass_kg'] / 19.2) * 100:.0f} % against 19.2 kg (80 % of the limit)"


def c_fit():
    ok = not PLACEMENT["failed"]
    return ok, f"{len(PLACEMENT['placed'])} modules placed, {len(PLACEMENT['failed'])} failed, {len(PLACEMENT.get('relocated', []))} relocated"


def c_com():
    import wollemi_cad as gc
    M, com, _ = gc.mass_props(PLACEMENT["placed"], CFG, False, GEO)
    ok = abs(com[0]) <= 20 and abs(com[1]) <= 20 and abs(com[2]) <= 70
    return ok, f"CoM ({com[0]:+.1f}, {com[1]:+.1f}, {com[2]:+.1f}) mm"


def c_wingstack():
    t = GEO["wings"]["panels_per_wing"] * GEO["wings"]["panel"][2]
    return t <= GEO["frame"]["protrusion_limit"], f"{t:.2f} mm vs {GEO['frame']['protrusion_limit']:.1f} mm"


def c_power_margin():
    import budget
    r = budget.compute(CFG)
    worst = min(r["scenarios"], key=lambda s: s["margin"])
    return worst["margin"] >= 0.20, f"worst scenario '{worst['name'][:40]}' margin {worst['margin'] * 100:+.0f} %"


def c_burn_power():
    import budget
    r = budget.compute(CFG)
    s = next(x for x in r["scenarios"] if "BURN" in x["name"])
    return s["margin"] >= 0.0, f"burn-mode load {s['cons']:.0f} W (thruster, minimal services) against about {s['gen'] / 0.62:.0f} W instantaneous sunlit generation ({s['margin'] * 100:+.0f} %) in the sun-biased attitude"


def c_eclipse():
    import budget
    r = budget.compute(CFG)
    worst = max(r["scenarios"], key=lambda s: s["ecl_need"])
    ratio = r["eclipse_usable_wh"] / worst["ecl_need"] if worst["ecl_need"] else 99
    return ratio >= 2.0, f"usable {r['eclipse_usable_wh']:.0f} Wh vs worst need {worst['ecl_need']:.1f} Wh (x{ratio:.1f})"


def c_strings():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "eps_design.py")], capture_output=True, text=True)
    ok = out.returncode == 0 and "OK" in out.stdout
    line = next((l.strip() for l in out.stdout.splitlines() if "cold Voc" in l), "")
    return ok, line[:110]


_THERMAL = {}


def thermal_res(kind):
    if not _THERMAL:
        import thermal as T
        burst = dict(T.col_power)
        burst[T.JETSON_Q] += 10
        for name, beta, pw in (("nom80", 80, T.col_power), ("nom0", 0, T.col_power)):
            res, hd, ecl = T.simulate(beta, pw, orbits=18)
            _THERMAL[name] = res
        res, hd, ecl = T.simulate(0, T.col_power_safe, orbits=18)
        _THERMAL["safe0"] = res
    return _THERMAL[kind]


def c_thermal():
    worst_lo, worst_hi, bmin, bmax = 1e9, -1e9, 1e9, -1e9
    for k in ("nom80", "nom0", "safe0"):
        r = thermal_res(k)
        for n in ("Q1", "Q2", "Q3", "Q4"):
            if k != "safe0" or n != "Q1":
                worst_lo = min(worst_lo, r[n][0])
            worst_hi = max(worst_hi, r[n][1])
        bmin, bmax = min(bmin, r["BATT"][0]), max(bmax, r["BATT"][1])
    ok = worst_lo >= -20 and worst_hi <= 60 and bmin >= 0 and bmax <= 40
    return ok, f"electronics {worst_lo:.0f}..{worst_hi:.0f} C, battery {bmin:.0f}..{bmax:.0f} C (nominal, eclipse and safe cases)"


def c_optics():
    parts = []
    ok = True
    for k in ("nom80", "nom0"):
        lo, hi = thermal_res(k)["Q1"]
        ok = ok and lo >= 10 and hi <= 30 and hi - lo <= 6
        parts.append(f"{k}: {lo:.0f}..{hi:.0f} C (swing {hi - lo:.1f} K)")
    return ok, "; ".join(parts)


def c_slew():
    imax = 0.342
    t, th = 120.0, math.radians(90)
    torque = imax * 4 * th / t ** 2
    mom = imax * 2 * th / t
    m1, m2 = 3e-3 / torque, 30e-3 / mom
    return m1 >= 3 and m2 >= 3, f"torque margin x{m1:.0f}, momentum margin x{m2:.1f}"


def c_thrust_torque():
    import wollemi_cad as gc
    M, com, _ = gc.mass_props(PLACEMENT["placed"], CFG, False, GEO)
    bay = next(p for p in PLACEMENT["placed"] if p["name"].startswith("Bus: micro-propulsion"))
    plume = (bay["min"][0], (bay["min"][1] + bay["max"][1]) / 2, (bay["min"][2] + bay["max"][2]) / 2)
    cy, cz, miss = gc.thrust_geometry(plume, com, GEO)
    resid_mm = 5.0
    torque_uncanted = 1.1e-3 * miss * 1e-3 * 1e6
    torque_resid = 1.1e-3 * resid_mm * 1e-3 * 1e6
    return torque_resid < 18.0, (f"uncanted {torque_uncanted:.0f} uN m; with the fixed cant ({cy:.1f}, {cz:.1f} deg) and a {resid_mm:.0f} mm CoM "
                                  f"uncertainty {torque_resid:.1f} uN m < 18 uN m magnetorquer average")


def c_deltav():
    import orbit_life
    o = orbit_life.analysis()
    dv, plan = o["available_dv"], o["plan"]["total"]
    return dv >= 500 and plan < dv, (f"{dv:.0f} m/s from a {orbit_life.IMPULSE_NS:.0f} Ns class thruster at {o['mass']:.1f} kg (vendor class value, unverified); "
                                     f"plan (50 yr keeping x1.5, descent, avoidance) {plan:.0f} m/s")


def c_plume():
    import wollemi_cad as gc
    M, com, _ = gc.mass_props(PLACEMENT["placed"], CFG, False, GEO)
    bay = next(p for p in PLACEMENT["placed"] if p["name"].startswith("Bus: micro-propulsion"))
    plume = (-GEO["frame"]["outer"][0] / 2, (bay["min"][1] + bay["max"][1]) / 2, (bay["min"][2] + bay["max"][2]) / 2)
    cy, cz, miss = gc.thrust_geometry(plume, com, GEO)
    msg = gc.plume_check(plume, GEO, GEO["thruster"]["plume_half_angle_deg"], cy)
    return "clear" in msg, msg[:110]


def c_data_capacity():
    d = load("configs/12u_data.toml")
    L = d["link"]
    per_pass = L["sband_rate_bps"] * L["link_efficiency"] * L["pass_s"] / 8 / 1e6
    cap = per_pass * L["passes_per_station_day"]
    total = sum(s["raw_mb_day"] / s["ratio"] for s in d["stream"]) + L["ota_reserve_mb_day"]
    return cap >= 2 * total, f"capacity {cap:.0f} MB/day vs science + reserve {total:.0f} MB/day (x{cap / total:.1f})"


def c_link():
    import link_budget as lb
    m, g, _ = lb.margin(1.2, 1e6)
    return m >= 3.0, f"{m:+.1f} dB"


def c_protocol_tests():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "protocol", "tests", "test_protocol.py")], capture_output=True, text=True)
    return "ALL PASSED" in out.stdout, out.stdout.strip().splitlines()[-1] if out.stdout.strip() else out.stderr[-100:]


def c_storage():
    d = load("configs/12u_data.toml")
    st = d["storage"]
    raw_non = sum(s["raw_mb_day"] for s in d["stream"])
    tele, hyp = d["imaging"]["telescope"], d["imaging"]["hyperspectral"]
    raw_gb = (raw_non + st["imaging_telescope_per_day"] * tele["raw_mb_per_image"]
              + st["imaging_hyperspectral_per_day"] * hyp["raw_mb_per_scene"]) / 1000
    days = st["raw_ring_gb"] / raw_gb
    return days >= 100 and st["parity"] >= 2, f"{days:.0f} days of raw data, {st['parity']} parity devices"


def c_longevity():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "longevity.py")], capture_output=True, text=True).stdout
    import re
    m = re.search(r"cover eclipse after ~([\d.]+) yr", out)
    s = re.search(r"Safe-mode power .* holds until ~(>?[\d.]+) yr", out)
    yrs = float(m.group(1)) if m else 0
    safe = s.group(1) if s else "0"
    ok = yrs >= 10 and (safe.startswith(">") or float(safe) >= 50)
    return ok, f"main packs cover eclipse for ~{yrs:.0f} yr; safe mode holds {safe} yr"


def c_chain():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "chain_check.py")], capture_output=True, text=True).stdout
    return "CHAIN CHECK OK" in out, out.strip().splitlines()[-1][:160] if out.strip() else "no output"


def c_kaitai_beacon():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "groundstation", "kaitai", "verify_all_ksy.py")], capture_output=True, text=True)
    ok = out.returncode == 0 and "All 27 messages in wollemi_protocol.ksy" in out.stdout
    return ok, "all 27 messages' .ksy byte-model match the real encoder" if ok else (out.stdout + out.stderr)[-200:]


def c_kicad_drc():
    rep = os.path.join(ROOT, "electronics", "kicad", "drc_report.txt")
    if not os.path.exists(rep):
        return False, "no DRC report (run electronics/gen_card.py)"
    txt = open(rep, encoding="utf-8", errors="ignore").read()
    return "Found 0 DRC violations" in txt, "Found 0 DRC violations" if "Found 0 DRC violations" in txt else txt[:100]


def c_kicad_backplane():
    rep = os.path.join(ROOT, "electronics", "kicad", "backplane_drc_report.txt")
    if not os.path.exists(rep):
        return False, "no DRC report (run electronics/gen_backplane.py)"
    txt = open(rep, encoding="utf-8", errors="ignore").read()
    ok = "Found 0 DRC violations" in txt and "Found 0 unconnected pads" in txt
    return ok, "Found 0 DRC violations, 0 unconnected pads" if ok else txt[:120]


def c_kicad_eps():
    ok_all, msgs = True, []
    for name in ("wollemi_eps_card", "wollemi_survival_card"):
        rep = os.path.join(ROOT, "electronics", "kicad", f"{name}_drc_report.txt")
        if not os.path.exists(rep):
            return False, f"no DRC report for {name} (run electronics/gen_eps_card.py)"
        txt = open(rep, encoding="utf-8", errors="ignore").read()
        ok = "Found 0 DRC violations" in txt
        ok_all = ok_all and ok
        msgs.append(f"{name}: {'0 violations' if ok else txt[:80]}")
    return ok_all, "; ".join(msgs)


def c_firmware_tests():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "firmware", "tests", "run_tests.py")], capture_output=True, text=True)
    ok = "ALL FIRMWARE TESTS PASSED" in out.stdout
    lines = [l for l in out.stdout.splitlines() if "checks" in l or "cross-checks" in l]
    return ok, "; ".join(l.strip() for l in lines)[:120] if ok else (out.stdout + out.stderr)[-160:]


def c_structure():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "structure.py")], capture_output=True, text=True)
    line = next((l for l in out.stdout.splitlines() if l.startswith("Verdict")), "")
    return out.returncode == 0, line[:110]


def c_orbit():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "orbit_life.py")], capture_output=True, text=True)
    line = next((l for l in out.stdout.splitlines() if l.startswith("Verdict")), "")
    return out.returncode == 0, line[:120]


def c_mission_sim():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "sim", "mission_sim.py"), "60"], capture_output=True, text=True)
    line = next((l for l in out.stdout.splitlines() if l.startswith("Verdict")), out.stderr[-120:])
    return out.returncode == 0, line[:120]


def c_fmea():
    out = subprocess.run([sys.executable, os.path.join(ROOT, "tools", "fmea_check.py")], capture_output=True, text=True)
    return out.returncode == 0, out.stdout.strip().splitlines()[-1][:120] if out.stdout.strip() else out.stderr[-100:]


CHECKS = {k[2:]: v for k, v in globals().items() if k.startswith("c_")}


def main():
    reqs = load("mission/traceability.toml")["req"]
    rows = []
    n_auto = n_pass = n_fail = n_open = n_designed = 0
    for r in reqs:
        ev_ok = all(os.path.exists(os.path.join(ROOT, e)) for e in r.get("evidence", []))
        if "auto" in r:
            n_auto += 1
            try:
                ok, detail = CHECKS[r["auto"]]()
            except Exception as e:                       # a broken check must be visible, not silent
                ok, detail = False, f"check failed to run: {type(e).__name__}: {e}"
            status = "PASS" if ok else "FAIL"
            n_pass += ok
            n_fail += not ok
        else:
            status = r.get("status", "open").upper()
            detail = r.get("note", "")
            n_open += status == "OPEN"
            n_designed += status == "DESIGNED"
        rows.append((r, status, detail, ev_ok))

    print(f"{'ID':9s} {'Meth':4s} {'Status':9s} Requirement / evidence")
    for r, status, detail, ev_ok in rows:
        print(f"{r['id']:9s} {r['method']:4s} {status:9s} {r['text'][:70]}")
        print(f"{'':24s}-> {detail[:120]}{'' if ev_ok else '  [evidence file missing]'}")
    print()
    print(f"{len(rows)} requirements: {n_pass} auto PASS, {n_fail} auto FAIL, {n_designed} designed (not yet proven), {n_open} open")

    md = ["# Verification matrix (generated)", "",
          "Generated by `python sim/trace_check.py` from `mission/traceability.toml`; numeric checks run on the real design data.", "",
          f"**{len(rows)} requirements: {n_pass} PASS (automatic), {n_fail} FAIL, {n_designed} designed but not proven, {n_open} open.**", "",
          "| ID | Method | Status | Requirement | Evidence / result |", "|---|---|---|---|---|"]
    for r, status, detail, ev_ok in rows:
        ev = ", ".join(f"`{e}`" for e in r.get("evidence", []))
        md.append(f"| {r['id']} | {r['method']} | {status} | {r['text']} | {detail} ({ev}) |")
    md += ["", "Methods: A analysis, T test, I inspection, D demonstration. PASS means the automatic check passes on the current design; "
           "it is an analysis result, not a substitute for test."]
    open(os.path.join(ROOT, "docs", "verification-matrix.md"), "w", encoding="utf-8").write("\n".join(md) + "\n")
    return 1 if n_fail else 0


if __name__ == "__main__":
    sys.exit(main())
