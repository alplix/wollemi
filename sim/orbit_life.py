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


IMPULSE_NS = 9500.0        # 1.5U iodine gridded-ion class total impulse (ThrustMe NPT30-I2 1.5U, see docs/propulsion.md)
THRUST_N = 1.1e-3


def analysis():
    """All numbers of the orbit-lifetime study as a dictionary (used by the printout, the document generator and the checks)."""
    mass = sum(m["mass_kg"] for m in CFG["module"])
    cd = 2.2
    body_area = 2 * (0.2263 * 0.3405 * 2 + 0.2263 * 0.2263) / 4
    wing_area = 2 * 3 * (GEO["wings"]["panel"][0] * 1e-3) * (GEO["wings"]["panel"][1] * 1e-3)
    wings_avg = wing_area / 2
    sail = 1.0
    areas = {"stowed (no wings)": body_area, "wings deployed": body_area + wings_avg, "wings + 1 m2 drag sail": body_area + wings_avg + sail / 2}
    out = {"mass": mass, "cd": cd, "body_area": body_area, "wings_avg": wings_avg, "sail_avg": sail / 2, "cases": list(areas), "decay": {}, "dv": {}}
    for h in (500, 600, 700, 800):
        for name, area in areas.items():
            B = mass / (cd * area)
            y_a, _ = decay(h, B, "cycle", 0.0)
            y_b, _ = decay(h, B, "cycle", math.pi)
            out["decay"][(h, name)] = (min(y_a, y_b), max(y_a, y_b))
        B = mass / (cd * areas["wings deployed"])
        a_ = RE + h * 1e3
        v = math.sqrt(MU / a_)
        out["dv"][h] = (cycle_average_dv(h, B), 0.5 * density(h, 0.0) * v * v / B * YEAR, 0.5 * density(h, 1.0) * v * v / B * YEAR)
    h0 = 700
    B_s = mass / (cd * areas["wings + 1 m2 drag sail"])
    v700 = math.sqrt(MU / (RE + h0 * 1e3))
    out["descent"] = {}
    for target in (600, 500):
        vt = math.sqrt(MU / (RE + target * 1e3))
        dv = abs(vt - v700)
        y_r = (decay(target, B_s, "cycle", 0.0)[0], decay(target, B_s, "cycle", math.pi)[0])
        out["descent"][target] = {"dv": dv, "days": mass * dv / THRUST_N / 86400, "years": (min(y_r), max(y_r))}
    a1, a2 = RE + 700e3, RE + 300e3
    at = (a1 + a2) / 2
    dv_p = math.sqrt(MU / a1) - math.sqrt(MU * (2 / a1 - 1 / at))
    out["perigee"] = {"dv": dv_p, "days": mass * dv_p / THRUST_N / 86400}
    out["available_dv"] = IMPULSE_NS / mass
    keep = out["dv"][700][0] * 50
    out["plan"] = {"keeping_50y": keep, "keeping_margin": keep * 1.5, "descent": out["descent"][500]["dv"], "avoidance": 20.0}
    out["plan"]["total"] = out["plan"]["keeping_margin"] + out["plan"]["descent"] + out["plan"]["avoidance"]
    sail_y = out["decay"][(700, "wings + 1 m2 drag sail")]
    wing_y = out["decay"][(700, "wings deployed")]
    out["ok"] = sail_y[1] <= 25 and out["plan"]["total"] < out["available_dv"] and wing_y[1] > 25
    return out


def main():
    o = analysis()
    print(f"Mass {o['mass']:.1f} kg, Cd {o['cd']}; tumbling projected area: body {o['body_area']:.3f} m2, wings {o['wings_avg']:.3f} m2, sail {o['sail_avg']:.2f} m2 (1 m2 sail)")
    print()
    print("Natural decay time to 200 km (years), solar cycle model; range = best and worst starting phase of the 11-year cycle (cap 300 yr):")
    print(f"{'altitude':>9s} " + "".join(f"{c[:24]:>26s}" for c in o["cases"]))
    for h in (500, 600, 700, 800):
        print(f"{h:6d} km " + "".join(f"{o['decay'][(h, c)][0]:7.1f} - {o['decay'][(h, c)][1]:7.1f}".rjust(26) for c in o["cases"]))
    print("(a constant mean-density model would look much slower: the solar-maximum years dominate the drag, so it is not used)")
    print()
    print("Drag make-up delta-v to hold the altitude, wings deployed (m/s per year averaged over the solar cycle; range solar min .. max):")
    for h in (500, 600, 700, 800):
        avg, lo, hi = o["dv"][h]
        print(f"  {h} km: {avg:8.2f} m/s/yr (min {lo:.2f} .. max {hi:.1f}); 50 years: {avg * 50:7.0f} m/s")
    print()
    y_w = o["decay"][(700, "wings deployed")]
    y_s = o["decay"][(700, "wings + 1 m2 drag sail")]
    print("Disposal from 700 km (IADC guideline: reenter or reach a graveyard within 25 years of end of mission)")
    print(f"  passive, wings deployed: {y_w[0]:.0f}-{y_w[1]:.0f} years: {'meets' if y_w[1] <= 25 else 'does NOT meet'} 25 years")
    print(f"  passive with a 1 m2 sail: {y_s[0]:.0f}-{y_s[1]:.0f} years: {'meets' if y_s[1] <= 25 else 'does NOT meet'} 25 years (model uncertainty is a factor 2-3)")
    for t, d in o["descent"].items():
        print(f"  electric spiral 700 -> {t} km ({d['dv']:.0f} m/s, ~{d['days']:.0f} days of thrusting) then drag with the sail: {d['years'][0]:.1f}-{d['years'][1]:.1f} years")
    print(f"  perigee lowering to 300 km (elliptical orbit, rapid decay): {o['perigee']['dv']:.0f} m/s, ~{o['perigee']['days']:.0f} days of thrusting at 1.1 mN")
    print(f"  available electric delta-v: about {o['available_dv']:.0f} m/s ({IMPULSE_NS:.0f} Ns class thruster on {o['mass']:.1f} kg; see docs/propulsion.md)")
    p = o["plan"]
    print()
    print(f"Delta-v plan at 700 km: 50 years of station keeping {p['keeping_50y']:.0f} m/s (x1.5 margin = {p['keeping_margin']:.0f}) + descent {p['descent']:.0f} m/s + collision avoidance {p['avoidance']:.0f} m/s = {p['total']:.0f} m/s of {o['available_dv']:.0f} m/s available")
    print("Debris and collision risk are not evaluated here (needs ESA MASTER or NASA ORDEM and the conjunction-assessment service).")
    print(f"Verdict: at 700 km the sail alone gives {y_s[0]:.0f}-{y_s[1]:.0f} years (meets 25 years on this model, with a factor 2-3 uncertainty), without the sail {y_w[0]:.0f}-{y_w[1]:.0f} years (fails); "
          f"the propulsive descent to 500-600 km ({o['descent'][600]['dv']:.0f}-{o['descent'][500]['dv']:.0f} m/s) restores margin, and the total plan fits the available delta-v: {'OK' if o['ok'] else 'CHECK'}.")
    return 0 if o["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
