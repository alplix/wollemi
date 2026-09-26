"""Mass / power / energy budget calculator.

Usage: python sim/budget.py configs/6u_science.toml
Reports the figures of merit defined in mission/requirements.md.

Configs with [geometry] + [[scenario]] get per-scenario power budgets (orbit / attitude /
safe mode). Older configs (2U, 3U) use a single cell_area_m2 * avg_projection estimate.
"""
import sys
import tomllib

ORBIT_H = 1.58  # ~95 min orbit


def solar_factor(solar):
    """W per m2 of effectively lit cell area, before orbit sunlit fraction."""
    return (solar["flux_w_m2"] * solar["cell_efficiency"] * solar["packing_factor"]
            * solar["degradation"] * solar["eps_efficiency"])


def areas(geo):
    body = (2 * geo["large_face_m2"] + 2 * geo["narrow_face_m2"] + 2 * geo["end_face_m2"]) \
        * geo["body_usable_fraction"]
    wings = geo["wings"] * geo["panels_per_wing"] * geo["wing_panel_m2"] * geo["wing_usable_fraction"]
    return body, wings


def scenario_report(cfg, sc, consumed_full, consumed_safe):
    body, wings = areas(cfg["geometry"])
    lit = body * sc["body_proj"] + wings * sc["wing_proj"]
    gen = solar_factor(cfg["solar"]) * lit * sc["sunlit"]
    base = consumed_safe if sc.get("safe") else consumed_full
    extra = sc.get("extra_load_w", 0.0)
    ecl_h = (1 - sc["sunlit"]) * ORBIT_H
    if sc.get("extra_sunlit_only") and extra:
        # extra load (e.g. thruster) runs only while sunlit: compare against instantaneous sunlit power
        cons = base + extra
        margin = (gen / sc["sunlit"] - cons) / cons
    else:
        cons = base + extra
        margin = (gen - cons) / cons if cons else float("inf")
    return {
        "name": sc["name"], "gen": gen, "cons": cons,
        "margin": margin,
        "ecl_need": base * ecl_h,
        "nominal": sc.get("nominal", False), "safe": sc.get("safe", False),
    }


def compute(cfg):
    plat, batt, mods = cfg["platform"], cfg["battery"], cfg["module"]
    units = plat["units"]
    consumed = sum(m["power_w"] * m["duty"] for m in mods)
    consumed_safe = sum(m["power_w"] * m["duty"] for m in mods if m.get("safe_mode"))
    mass = sum(m["mass_kg"] for m in mods)
    payload_mass = sum(m["mass_kg"] for m in mods if m["payload"])
    usable_wh = batt["capacity_wh"] * batt["max_depth_of_discharge"]

    if "scenario" in cfg:
        scen = [scenario_report(cfg, sc, consumed, consumed_safe) for sc in cfg["scenario"]]
        nominal = next((s for s in scen if s["nominal"]), scen[0])
        gen = nominal["gen"]
    else:  # legacy single-estimate configs
        solar, orbit = cfg["solar"], cfg["orbit"]
        gen = solar_factor(solar) * solar["cell_area_m2"] * solar["avg_projection"] * orbit["sunlit_fraction"]
        ecl = (1 - orbit["sunlit_fraction"]) * ORBIT_H * consumed
        scen = [{"name": "single estimate", "gen": gen, "cons": consumed,
                 "margin": (gen - consumed) / consumed, "ecl_need": ecl,
                 "nominal": True, "safe": False}]
        nominal = scen[0]

    return {
        "units": units, "mass_kg": mass, "mass_margin_kg": plat["mass_limit_kg"] - mass,
        "consumed_w": consumed, "scenarios": scen, "nominal": nominal,
        "W_per_U": gen / units, "Wh_per_U": batt["capacity_wh"] / units,
        "payload_fraction": payload_mass / mass,
        "eclipse_usable_wh": usable_wh,
        "battery_mass_kg": batt["capacity_wh"] / batt["specific_energy_wh_kg"],
    }


def volume_report(cfg):
    geo = cfg.get("geometry", {})
    if "envelope_cm3" not in geo or not any("volume_cm3" in m for m in cfg["module"]):
        return None
    usable = geo["envelope_cm3"] * (1 - geo["structure_fraction"]) * geo["packing_efficiency"]
    tiers = {}
    for m in cfg["module"]:
        t = m.get("tier", "core")
        tiers.setdefault(t, []).append(m)
    vol = {t: sum(m.get("volume_cm3", 0) for m in ms) for t, ms in tiers.items()}
    mass = {t: sum(m["mass_kg"] for m in ms) for t, ms in tiers.items()}
    return usable, vol, mass, tiers


def print_volume(cfg):
    v = volume_report(cfg)
    if not v:
        return
    usable, vol, mass, tiers = v
    print("-- Volume (module volume vs usable = envelope x (1 - structure) x packing) --")
    print(f"Usable volume: {usable:.0f} cm3 of {cfg['geometry']['envelope_cm3']} cm3 envelope")
    cum = 0
    for t in ("core", "science", "expansion", "research", "service"):
        if t not in vol:
            continue
        cum += vol[t]
        fit = "fits" if cum <= usable else "OVER"
        print(f"  {t:10s} {vol[t]:6.0f} cm3, {mass[t]:5.2f} kg   cumulative {cum:6.0f} cm3 "
              f"({cum/usable*100:4.0f} % of usable) [{fit}]")
    if "science" in vol:
        n = sum(1 for m in cfg["module"] if m.get("tier") == "science")
        tot = sum(vol.values())
        print(f"  science payloads: {n}, {vol['science']:.0f} cm3 ({vol['science']/tot*100:.0f} % of module volume), "
              f"{mass['science']:.2f} kg")
    largest = sorted((m for m in cfg["module"]), key=lambda m: -m.get("volume_cm3", 0))[:6]
    print("  largest: " + "; ".join(f"{m['name'].split(':')[0][:28]} {m.get('volume_cm3',0)}" for m in largest))


def main(path):
    with open(path, "rb") as f:
        cfg = tomllib.load(f)
    r = compute(cfg)
    ok = lambda c: "OK  " if c else "FAIL"
    print(f"== {cfg['platform']['name']} ({r['units']}U) ==")
    print(f"Mass:      {r['mass_kg']:.2f} kg (margin {r['mass_margin_kg']:+.2f} kg) "
          f"[{ok(r['mass_margin_kg'] >= 0)}]")
    if "geometry" in cfg:
        b, w = areas(cfg["geometry"])
        print(f"Cells:     body {b:.3f} m2 + wings {w:.3f} m2 "
              f"({cfg['geometry']['wings']} wings x {cfg['geometry']['panels_per_wing']} panels)")
    print(f"Load:      {r['consumed_w']:.1f} W avg (full)")
    print(f"Battery:   {cfg['battery']['capacity_wh']} Wh, usable {r['eclipse_usable_wh']:.0f} Wh")
    print("-- Scenarios (REQ-8: margin >= +20 %, eclipse energy covered) --")
    for s in r["scenarios"]:
        tag = " [nominal]" if s["nominal"] else ""
        load = "safe loads" if s["safe"] else "full loads"
        good = s["margin"] >= 0.20 and s["ecl_need"] <= r["eclipse_usable_wh"]
        print(f"[{ok(good)}] {s['name']}{tag}\n        gen {s['gen']:.1f} W, {load} {s['cons']:.1f} W, "
              f"margin {s['margin']*100:+.0f} %, eclipse need {s['ecl_need']:.1f} Wh")
    print_volume(cfg)
    print("-- Figures of merit (definitions in mission/requirements.md) --")
    print(f"FOM-1 orbit-average power per U:      {r['W_per_U']:.2f} W/U  (target >= 3, nominal scenario) [{ok(r['W_per_U'] >= 3)}]")
    worst_need = max(sc["ecl_need"] for sc in r["scenarios"])
    ecl_margin = r["eclipse_usable_wh"] / worst_need if worst_need else 99.0
    print(f"FOM-2 eclipse energy margin:          x{ecl_margin:.1f}  (usable battery energy / worst eclipse need, target >= 2) [{ok(ecl_margin >= 2)}]")
    sci_mass = sum(m["mass_kg"] for m in cfg["module"] if m.get("tier") == "science" or (m.get("payload") and "tier" not in m))
    print(f"FOM-3 science payload mass fraction:  {r['payload_fraction'] * 100:.0f} %  (target >= 25; mass spent on longevity and safety is deliberate) "
          f"[{ok(r['payload_fraction'] >= 0.25)}]")
    v = volume_report(cfg)
    if v:
        _usable, vol, _mass, _tiers = v
        share = vol.get("science", 0.0) / max(sum(vol.values()), 1e-9)
        print(f"FOM-4 science share of module volume: {share * 100:.0f} %  (target >= 45) [{ok(share >= 0.45)}]")

if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/6u_science.toml")
