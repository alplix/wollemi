"""Rough cost and schedule model with Monte Carlo ranges (all inputs unverified estimates, see configs/12u_cost.toml).

Usage: python sim/cost.py
Scenarios: full flight (all tiers), core flight (no imaging, no extras), and a precursor (FlatSat + balloon, no launch and no flight-only hardware).
"""
import os
import random
import statistics
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
C = tomllib.load(open(os.path.join(ROOT, "configs", "12u_cost.toml"), "rb"))
T = tomllib.load(open(os.path.join(ROOT, "mission", "tests.toml"), "rb"))["test"]
A = C["assumptions"]


def tri(rng, low, likely, high):
    return rng.triangular(low, high, likely)


def test_cost_range():
    """External test cost: engineer-days of the test campaigns in outside facilities times a class rate (low/likely/high = 0.5x/1x/2x)."""
    base = sum(t["effort_days"] * A["external_cost_per_test_day"][t["external"]] for t in T)
    return 0.5 * base, base, 2.0 * base


def engineer_days(test_filter=lambda t: True):
    return sum(t["effort_days"] for t in T if test_filter(t))


def sample(scenario, rng):
    hw = other = 0.0
    for it in C["item"]:
        in_scope = False
        if scenario == "full":
            in_scope = True
        elif scenario == "core":
            in_scope = it["tier"] == "core"
        elif scenario == "precursor":
            in_scope = it["tier"] == "core" and it["scope"] == "both"
        if not in_scope:
            continue
        v = tri(rng, it["low"], it["likely"], it["high"])
        if scenario == "precursor" and it["group"] in ("bus", "science"):
            v *= A["flatsat_fraction_of_core_hardware"]      # engineering models are cheaper than flight units
        if it["group"] in ("bus", "science", "optional"):
            hw += v
        else:
            other += v
    tests = 0.0
    lo, mid, hi = test_cost_range()
    tsc = tri(rng, lo, mid, hi)
    if scenario == "precursor":
        # only board, subsystem and precursor level tests are needed without a flight model
        share = engineer_days(lambda t: t["level"] in ("component", "board", "subsystem", "precursor", "ground")) / max(engineer_days(), 1)
        tests = tsc * share * 0.5
        other += tri(rng, *A["balloon_flight_usd"])
    else:
        tests = tsc
    cash = hw * (1 + A["contingency_hardware"]) + (other + tests) * (1 + A["contingency_other"])
    eff = 0.0
    for e in C["effort"]:
        if scenario == "full" or e["tier"] == "core":
            eff += tri(rng, e["low"], e["likely"], e["high"])
    if scenario == "precursor":
        eff *= 0.45
    tdays = engineer_days() if scenario != "precursor" else engineer_days(lambda t: t["level"] in ("component", "board", "subsystem", "precursor", "ground")) * 0.5
    eff += tdays / A["engineer_days_per_year"]
    return cash, eff


def pct(v, p):
    v = sorted(v)
    return v[min(len(v) - 1, int(p / 100 * len(v)))]


def schedule(rng):
    return sum(tri(rng, p["low"], p["likely"], p["high"]) for p in C["phase"])


def main():
    n = A["monte_carlo_samples"]
    rng = random.Random(A["monte_carlo_seed"])
    print("Rough cost model (USD; unverified estimates, +-2x). Monte Carlo over triangular distributions of every item.")
    print(f"{'scenario':46s} {'cash P10':>12s} {'P50':>12s} {'P90':>12s}   {'effort (person-years) P50':>26s}   labour value P50")
    out = {}
    for sc, name in (("precursor", "Precursor: FlatSat + balloon (no launch)"), ("core", "Core flight (bus + long-life science, no imaging)"),
                     ("full", "Full flight (imaging, extras, everything)")):
        cash, eff = zip(*(sample(sc, rng) for _ in range(n)))
        out[sc] = (pct(cash, 10), pct(cash, 50), pct(cash, 90), pct(eff, 50))
        lab = pct(eff, 50) * A["person_year_usd"]
        print(f"{name:46s} {out[sc][0]:12,.0f} {out[sc][1]:12,.0f} {out[sc][2]:12,.0f}   {out[sc][3]:26.1f}   {lab:14,.0f}")
    print()
    sched = [schedule(rng) for _ in range(n)]
    print(f"Schedule to launch (critical path, small team): P10 {pct(sched, 10):.0f} months, P50 {pct(sched, 50):.0f}, P90 {pct(sched, 90):.0f} "
          f"(about {pct(sched, 50) / 12:.1f} years at the median)")
    # biggest cost drivers (likely values)
    items = sorted(C["item"], key=lambda i: -i["likely"])
    print("Largest items (likely value): " + "; ".join(f"{i['name'].split(':')[0][:34]} {i['likely'] / 1000:.0f}k" for i in items[:6]))
    lo, mid, hi = test_cost_range()
    print(f"External test facilities from the test plan: {lo / 1000:.0f}k - {hi / 1000:.0f}k (likely {mid / 1000:.0f}k); test effort {engineer_days()} engineer-days")
    tot = out["full"]
    print(f"Total full flight cash P50 {tot[1]:,.0f} USD (range {tot[0]:,.0f} - {tot[2]:,.0f}); precursor P50 {out['precursor'][1]:,.0f} USD.")
    print("These figures are for orientation only: get vendor quotes (thruster, cells, optics, launch) before using them with anyone.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
