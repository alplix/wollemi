"""Year-by-year longevity model: solar output, battery, and total ionising dose.

Usage: python sim/longevity.py configs/12u_science.toml configs/12u_longevity.toml
"""
import math
import sys
import tomllib

sys.path.insert(0, __file__.rsplit("sim", 1)[0] + "sim")
import budget  # noqa: E402


def main(cfg_path, lg_path):
    cfg = tomllib.load(open(cfg_path, "rb"))
    lg = tomllib.load(open(lg_path, "rb"))
    r = budget.compute(cfg)
    deg0 = cfg["solar"]["degradation"]
    k = lg["solar"]["degradation_per_year"]
    scen = {s["name"]: s for s in r["scenarios"]}
    nominal = next(s for s in r["scenarios"] if s["nominal"])
    tumbling = next(s for s in r["scenarios"] if "tumbling" in s["name"] and not s["safe"])
    safe = next(s for s in r["scenarios"] if s["safe"])
    load = r["consumed_w"]

    alt = lg["orbit"]["altitude_km"]
    a = 6371 + alt
    period_min = 2 * math.pi * math.sqrt(a ** 3 / 398600) / 60
    orbits_yr = 365.25 * 24 * 60 / period_min if lg["orbit"]["has_eclipse"] else 0
    b = lg["battery"]
    dod = nominal["ecl_need"] / b["packs_wh_total"] if lg["orbit"]["has_eclipse"] else 0
    n_life = b["cycle_life_at_100dod"] * (max(dod, 1e-3)) ** (-b["dod_exponent"])
    print(f"Orbit {alt} km: period {period_min:.1f} min, {orbits_yr:.0f} eclipse cycles/year")
    print(f"Battery DoD per cycle {dod * 100:.0f} %, cycle life ~{n_life:,.0f} cycles "
          f"= {n_life / max(orbits_yr, 1):.1f} years to {b['fade_at_end_of_life'] * 100:.0f} % fade")
    print()
    print(f"{'yr':>3s} {'nominal W':>10s} {'tumble W':>9s} {'tumble margin':>14s} {'safe W':>7s} "
          f"{'batt cap':>9s} {'eclipse ok':>11s}")
    events = {}
    for yr in (0, 1, 2, 5, 10, 15, 20, 25, 30, 40, 50):
        f = math.exp(-k * yr) / deg0
        nom, tum, sf = nominal["gen"] * f, tumbling["gen"] * f, safe["gen"] * f
        cycles = orbits_yr * yr
        cap = max(0.0, 1 - b["fade_at_end_of_life"] * cycles / n_life - b["calendar_fade_per_year"] * yr)
        need = nominal["ecl_need"]
        ecl_ok = (not lg["orbit"]["has_eclipse"]) or need <= b["packs_wh_total"] * cap * b["max_dod_usable"]
        print(f"{yr:3d} {nom:10.1f} {tum:9.1f} {(tum - load) / load * 100:13.0f}% {sf:7.1f} "
              f"{cap * 100:8.0f}% {'yes' if ecl_ok else 'NO':>11s}")
    # find crossover years on a fine grid
    for yr10 in range(0, 1001):
        yr = yr10 / 10
        f = math.exp(-k * yr) / deg0
        if "tumble" not in events and tumbling["gen"] * f < load:
            events["tumble"] = yr
        cap = max(0.0, 1 - b["fade_at_end_of_life"] * orbits_yr * yr / n_life - b["calendar_fade_per_year"] * yr)
        if "batt" not in events and lg["orbit"]["has_eclipse"] and nominal["ecl_need"] > b["packs_wh_total"] * cap * b["max_dod_usable"]:
            events["batt"] = yr
        if "safe" not in events and safe["gen"] * f < r["consumed_w"] * 0 + 1.1:
            events["safe"] = yr
    print()
    print(f"Tumbling-mode power no longer covers full load after ~{events.get('tumble', '>100')} yr")
    print(f"Main packs no longer cover eclipse after ~{events.get('batt', '>100')} yr "
          f"(then: sun-only mode, or survival bus only)")
    print(f"Safe-mode power (1.1 W) holds until ~{events.get('safe', '>100')} yr")

    print()
    print("-- Total ionising dose, years until part limit (dose = rate x years) --")
    rates = {int(k_): v for k_, v in lg["radiation"]["dose_rate_by_mm"].items()}
    hdr = "part (limit krad)".ljust(52) + "".join(f"{m:>7d}mm" for m in sorted(rates))
    print(hdr)
    for p in lg["part"]:
        row = "".join(f"{p['tid_krad'] / rates[m]:9.0f}" for m in sorted(rates))
        print(f"{p['name'][:40]} ({p['tid_krad']:>3.0f})".ljust(52) + row)
    print("dose over 50 yr (krad): " + ", ".join(f"{m} mm: {rates[m] * 50:.0f}" for m in sorted(rates)))


if __name__ == "__main__":
    main(*(sys.argv[1:3] or ["configs/12u_science.toml", "configs/12u_longevity.toml"]))
