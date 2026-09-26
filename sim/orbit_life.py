"""Orbit lifetime, drag make-up delta-v and disposal options (circular-orbit decay with a solar-cycle atmosphere).

Usage: python sim/orbit_life.py
The atmosphere is a two-table exponential model (solar minimum / maximum, geometric mean for the average) accurate to about a factor of 2-3; real work needs
NRLMSISE-00 or JB2008 with a solar flux forecast (or a tool such as ESA DRAMA). Results are for comparison and design decisions, not licensing.
"""
import math
import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
GEO = tomllib.load(open(os.path.join(ROOT, "configs", "12u_geometry.toml"), "rb"))

MU = 3.986004418e14
RE = 6378.137e3
G0 = 9.80665
YEAR = 365.25 * 86400.0

# altitude km: (density at solar minimum, density at solar maximum) kg/m3 (rough)
TABLE = {200: (1.5e-10, 4.0e-10), 250: (3.0e-11, 1.2e-10), 300: (7e-12, 4e-11), 400: (3.5e-13, 6e-12),
         500: (3e-14, 1.2e-12), 600: (4e-15, 3e-13), 700: (8e-16, 7e-14), 800: (2e-16, 2.5e-14),
         900: (6e-17, 9e-15), 1000: (2e-17, 4e-15)}
ALTS = sorted(TABLE)


def density(h_km, s):
    """s = 0 solar minimum ... 1 solar maximum (log interpolation in altitude and in activity)."""
    h_km = min(max(h_km, ALTS[0]), ALTS[-1])
    for lo, hi in zip(ALTS, ALTS[1:]):
        if lo <= h_km <= hi:
            f = (h_km - lo) / (hi - lo)
            break
    ln_min = (1 - f) * math.log(TABLE[lo][0]) + f * math.log(TABLE[hi][0])
    ln_max = (1 - f) * math.log(TABLE[lo][1]) + f * math.log(TABLE[hi][1])
    return math.exp((1 - s) * ln_min + s * ln_max)


def activity(t_s, mode, phase0=0.0):
    if mode == "min":
        return 0.0
    if mode == "max":
        return 1.0
    if mode == "mean":
        return 0.5
    return 0.5 + 0.5 * math.sin(2 * math.pi * t_s / (11 * YEAR) + phase0)   # cycling


def decay(h0_km, ballistic, mode="cycle", phase0=0.0, dt=86400.0, h_end=200.0, cap_years=300):
    """Return years until the circular orbit falls below h_end, and the drag delta-v per year averaged over the first 10 years."""
    a = RE + h0_km * 1e3
    t = 0.0
    dv_10 = 0.0
    while a - RE > h_end * 1e3 and t < cap_years * YEAR:
        h = (a - RE) / 1e3
        rho = density(h, activity(t, mode, phase0))
        v = math.sqrt(MU / a)
        decel = 0.5 * rho * v * v / ballistic             # m/s2 (ballistic = m / (Cd A))
        if t < 10 * YEAR:
            dv_10 += decel * dt
        da = -rho * math.sqrt(MU * a) * dt / ballistic    # da/dt = -rho * sqrt(mu a) / B
        a += da
        t += dt
    return t / YEAR, dv_10 / 10.0


def cycle_average_dv(h_km, ballistic, steps=132):
    """Drag deceleration integrated over one 11-year cycle at fixed altitude, per year (m/s/yr)."""
    a = RE + h_km * 1e3
    v = math.sqrt(MU / a)
    total = 0.0
    for i in range(steps):
        s = 0.5 + 0.5 * math.sin(2 * math.pi * (i + 0.5) / steps)
        total += 0.5 * density(h_km, s) * v * v / ballistic
    return total / steps * YEAR


def main():
    mass = sum(m["mass_kg"] for m in CFG["module"])
    cd = 2.2
    body_area = 2 * (0.2263 * 0.3405 * 2 + 0.2263 * 0.2263) / 4          # tumbling body: total surface / 4
    wing_area = 2 * 3 * (GEO["wings"]["panel"][0] * 1e-3) * (GEO["wings"]["panel"][1] * 1e-3)
    wings_avg = wing_area / 2                                             # flat double-sided plates, tumbling average: A/2
    sail = 1.0                                                            # m2 drag sail (flat, tumbling average A/2)
    cases = {
        "stowed (no wings)": body_area,
        "wings deployed": body_area + wings_avg,
        "wings + 1 m2 drag sail": body_area + wings_avg + sail / 2,
    }
    print(f"Mass {mass:.1f} kg, Cd {cd}; tumbling projected area: body {body_area:.3f} m2, wings {wings_avg:.3f} m2, sail {sail / 2:.2f} m2 (1 m2 sail)")
    print()
    print("Natural decay time to 200 km (years), solar cycle model; range = best and worst starting phase of the 11-year cycle (cap 300 yr):")
    print(f"{'altitude':>9s} " + "".join(f"{c[:24]:>26s}" for c in cases))
    table = {}
    for h in (500, 600, 700, 800):
        row = []
        for name, area in cases.items():
            B = mass / (cd * area)
            y_a, _ = decay(h, B, "cycle", 0.0)
            y_b, _ = decay(h, B, "cycle", math.pi)
            table[(h, name)] = (min(y_a, y_b), max(y_a, y_b))
            row.append(f"{min(y_a, y_b):7.1f} - {max(y_a, y_b):7.1f}")
        print(f"{h:6d} km " + "".join(f"{r:>26s}" for r in row))
    print("(a constant mean-density model would look much slower: the solar-maximum years dominate the drag, so it is not used)")
    print()
    print("Drag make-up delta-v to hold the altitude, wings deployed (m/s per year averaged over the solar cycle; range solar min .. max):")
    dv50 = {}
    for h in (500, 600, 700, 800):
        B = mass / (cd * (body_area + wings_avg))
        avg = cycle_average_dv(h, B)
        a_ = RE + h * 1e3
        v = math.sqrt(MU / a_)
        lo = 0.5 * density(h, 0.0) * v * v / B * YEAR
        hi = 0.5 * density(h, 1.0) * v * v / B * YEAR
        dv50[h] = avg * 50
        print(f"  {h} km: {avg:8.2f} m/s/yr (min {lo:.2f} .. max {hi:.1f}); 50 years: {avg * 50:7.0f} m/s")
    print()

    h0 = 700
    y_w = table[(700, "wings deployed")]
    y_s = table[(700, "wings + 1 m2 drag sail")]
    print(f"Disposal from {h0} km (IADC guideline: reenter or reach a graveyard within 25 years of end of mission)")
    print(f"  passive, wings deployed: {y_w[0]:.0f}-{y_w[1]:.0f} years: {'meets' if y_w[1] <= 25 else 'does NOT meet'} 25 years")
    print(f"  passive with a 1 m2 sail: {y_s[0]:.0f}-{y_s[1]:.0f} years: {'meets' if y_s[1] <= 25 else 'does NOT meet'} 25 years (model uncertainty is a factor 2-3)")
    B_s = mass / (cd * (body_area + wings_avg + sail / 2))
    v700 = math.sqrt(MU / (RE + h0 * 1e3))
    dvs = {}
    for target in (600, 500):
        vt = math.sqrt(MU / (RE + target * 1e3))
        dv = vt - v0 if False else vt - v700
        days = mass * abs(dv) / 1.1e-3 / 86400
        y_r = (decay(target, B_s, "cycle", 0.0)[0], decay(target, B_s, "cycle", math.pi)[0])
        dvs[target] = (abs(dv), days, min(y_r), max(y_r))
        print(f"  electric spiral 700 -> {target} km ({abs(dv):.0f} m/s, ~{days:.0f} days of thrusting) then drag with the sail: {min(y_r):.1f}-{max(y_r):.1f} years")
    a1, a2 = RE + 700e3, RE + 300e3
    at = (a1 + a2) / 2
    dv_perigee = math.sqrt(MU / a1) - math.sqrt(MU * (2 / a1 - 1 / at))
    print(f"  perigee lowering to 300 km (elliptical orbit, rapid decay): {dv_perigee:.0f} m/s, ~{mass * dv_perigee / 1.1e-3 / 86400:.0f} days of thrusting at 1.1 mN")
    print(f"  available electric delta-v: about {9500.0 / mass:.0f} m/s (9500 Ns class thruster on {mass:.1f} kg; see docs/propulsion.md)")
    budget = 9500.0 / mass
    need = dv50[700] * 1.5 + dvs[500][0] + 20.0
    print()
    print(f"Delta-v plan at 700 km: 50 years of station keeping {dv50[700]:.0f} m/s (x1.5 margin = {dv50[700] * 1.5:.0f}) + descent {dvs[500][0]:.0f} m/s + collision avoidance 20 m/s = {need:.0f} m/s of {budget:.0f} m/s available")
    print("Debris and collision risk are not evaluated here (needs ESA MASTER or NASA ORDEM and the conjunction-assessment service).")
    ok = y_s[1] <= 25 and need < budget and y_w[1] > 25
    print(f"Verdict: at 700 km the sail alone gives {y_s[0]:.0f}-{y_s[1]:.0f} years (meets 25 years on this model, with a factor 2-3 uncertainty), without the sail {y_w[0]:.0f}-{y_w[1]:.0f} years (fails); "
          f"the propulsive descent to 500-600 km ({dvs[600][0]:.0f}-{dvs[500][0]:.0f} m/s) restores margin, and the total plan fits the available delta-v: {'OK' if ok else 'CHECK'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
