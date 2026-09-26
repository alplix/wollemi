"""Lumped-node orbital thermal model of the 12U (columns, battery vault, propellant tank).

Usage: python sim/thermal.py
Nodes: Q1..Q4 (masses and heat from the real CAD placement), BATT (isolated inside Q4) and TANK (propulsion bay).
Environment: sun, Earth infrared and albedo on six faces, nadir-pointing orbit frame (x velocity, y orbit normal,
z zenith). All coatings and conductances are estimates (configs/12u_thermal.toml).
"""
import json
import math
import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
th = tomllib.load(open(os.path.join(ROOT, "configs", "12u_thermal.toml"), "rb"))
cfg = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
pl = json.load(open(os.path.join(ROOT, "mechanical", "out", "placement.json")))

S = th["constants"]["solar_flux"]
EIR = th["constants"]["earth_ir"]
ALB = th["constants"]["albedo"]
SIG = th["constants"]["sigma"]
RE = 6378.137
R = RE + th["orbit"]["altitude_km"]
PERIOD = 2 * math.pi * math.sqrt(R ** 3 / 398600.4418)
RHO = math.asin(RE / R)
VF_NADIR = math.sin(RHO) ** 2
VF_SIDE = (RHO - math.sin(RHO) * math.cos(RHO)) / math.pi   # plate whose normal is perpendicular to nadir (analytic)

A_L = th["geometry"]["face_large_m2"]
A_E = th["geometry"]["face_end_m2"]
FACES = {"px": ((1, 0, 0), A_L), "mx": ((-1, 0, 0), A_L), "py": ((0, 1, 0), A_L), "my": ((0, -1, 0), A_L),
         "pz": ((0, 0, 1), A_E), "mz": ((0, 0, -1), A_E)}
# each face is shared by the columns on its side (ring order Q1(+,+) Q2(-,+) Q3(-,-) Q4(+,-)); +-Z faces by all four
FACE_COLS = {"px": (1, 4), "mx": (2, 3), "py": (1, 2), "my": (3, 4), "pz": (1, 2, 3, 4), "mz": (1, 2, 3, 4)}

# ---- masses and dissipation per column from the packing ----
mods = {m["name"]: m for m in cfg["module"]}
# heaters that are simulated explicitly (thermostats below) must not also count as constant dissipation
EXPLICIT_HEATERS = ("Bus: telescope column thermostatic heater", "Thermal (heaters)", "Battery containment")


def dissipation(m):
    return 0.0 if m["name"].startswith(EXPLICIT_HEATERS) else m["power_w"] * m["duty"]


col_mass = {q: th["conduction"]["structure_mass_per_column_kg"] for q in (1, 2, 3, 4)}
col_power = {q: 0.0 for q in (1, 2, 3, 4)}
col_power_safe = {q: 0.0 for q in (1, 2, 3, 4)}
batt_mass = 0.0
tank_mass = 0.0
for p in pl["placed"]:
    m = mods[p["name"]]
    q = p["col"]
    pw = dissipation(m)
    if p["name"].startswith("LiFePO4 pack"):
        batt_mass += m["mass_kg"]
        col_power[q] += 0.0
        continue
    if p["name"].startswith("Bus: micro-propulsion"):
        tank_mass += m["mass_kg"]
        continue
    tgt = q if q in (1, 2, 3, 4) else 2
    col_mass[tgt] += m["mass_kg"]
    col_power[tgt] += pw
    if m.get("safe_mode"):
        col_power_safe[tgt] += pw
# unplaced modules (skin, spine, harness) spread equally
for m in cfg["module"]:
    if m["name"] not in {p["name"] for p in pl["placed"]}:
        for q in (1, 2, 3, 4):
            col_mass[q] += m["mass_kg"] / 4
            col_power[q] += dissipation(m) / 4
            if m.get("safe_mode"):
                col_power_safe[q] += dissipation(m) / 4
JETSON_Q = next(p["col"] for p in pl["placed"] if p["name"].startswith("Mission computer: Jetson"))
NODES = ["Q1", "Q2", "Q3", "Q4", "BATT", "TANK"]
CP = {"Q1": th["constants"]["cp_body"], "Q2": th["constants"]["cp_body"], "Q3": th["constants"]["cp_body"],
      "Q4": th["constants"]["cp_body"], "BATT": th["constants"]["cp_battery"], "TANK": th["constants"]["cp_body"]}
CAP = {f"Q{q}": col_mass[q] * th["constants"]["cp_body"] for q in (1, 2, 3, 4)}
CAP["BATT"] = max(batt_mass, 0.5) * th["constants"]["cp_battery"]
CAP["TANK"] = max(tank_mass, 0.5) * th["constants"]["cp_body"]

cd = th["conduction"]
G = {}


def link(a, b, g):
    G[(a, b)] = g
    G[(b, a)] = g


for a, b in (("Q1", "Q2"), ("Q2", "Q3"), ("Q3", "Q4"), ("Q4", "Q1")):
    link(a, b, cd["ring_neighbour"])
link("Q1", "Q3", cd["diagonal_spine"])
link("Q2", "Q4", cd["diagonal_spine"])
link("BATT", "Q4", cd["battery_to_column"])
link("TANK", "Q2", cd["tank_to_column"])
link("TANK", "Q3", cd["tank_to_column"])


OPT = th.get("optics", {})
ISO = OPT.get("isolation_factor", 1.0)
for (a, b) in list(G):
    if a == "Q1" or b == "Q1":
        G[(a, b)] *= ISO


def coat_for(col, fk):
    if col == 1 and fk in ("px", "py") and "face_alpha" in OPT:
        return {"alpha": OPT["face_alpha"], "eps": OPT["face_eps"]}
    return th["faces"][fk]


def sun_vector(beta, u):
    return (math.cos(beta) * math.sin(u), math.sin(beta), math.cos(beta) * math.cos(u))


def env_loads(beta_deg, u):
    """Absorbed environment heat (W) per column at orbit angle u (0 = sub-solar point), and radiator areas."""
    beta = math.radians(beta_deg)
    s = sun_vector(beta, u)
    in_eclipse = s[2] < -math.sqrt(1 - (RE / R) ** 2 * 1.0) + 0.0 and (s[2] < -math.cos(RHO) * 0 - math.sqrt(1 - (RE / R) ** 2))
    # shadow condition: behind the Earth and inside the shadow cylinder
    in_eclipse = s[2] < 0 and R * math.sqrt(1 - s[2] ** 2) < RE
    sub = max(0.0, s[2])                               # cosine of the sun angle at the sub-satellite point
    q_in = {i: 0.0 for i in (1, 2, 3, 4)}
    for fk, (n, area) in FACES.items():
        f = th["faces"][fk]
        solar = 0.0 if in_eclipse else S * max(0.0, sum(a * b for a, b in zip(n, s)))
        vf = VF_NADIR if fk == "mz" else (0.0 if fk == "pz" else VF_SIDE)
        alb = 0.0 if in_eclipse else ALB * S * sub * vf
        eir = EIR * vf
        absorbed = area * (f["alpha"] * (solar + alb) + f["eps"] * eir)
        cols = FACE_COLS[fk]
        for c in cols:
            ff = coat_for(c, fk)
            q_in[c] += area * (ff["alpha"] * (solar + alb) + ff["eps"] * eir) / len(cols)
    return q_in, in_eclipse


def rad_out(T, fkeys_area):
    return sum(SIG * f["eps"] * a * (T + 273.15) ** 4 for f, a in fkeys_area)


COL_RAD = {}
for q in (1, 2, 3, 4):
    lst = []
    for fk, (n, area) in FACES.items():
        if q in FACE_COLS[fk]:
            lst.append((coat_for(q, fk), area / len(FACE_COLS[fk])))
    COL_RAD[q] = lst


def simulate(beta_deg, power, extra=None, orbits=25, dt=10.0, heater=True, tank_w=0.0, optics_heater=True):
    """Return per-node (min, max) over the last 5 orbits, heater duty and eclipse minutes per orbit."""
    lim = th["limits"]
    T = {n: 15.0 for n in NODES}
    heat_state = 0
    opt_state = 0
    opt_on_steps = 0
    hist = {n: [] for n in NODES}
    heater_on_steps = 0
    steps_last = 0
    eclipse_steps = 0
    n_steps = int(orbits * PERIOD / dt)
    for i in range(n_steps):
        t = i * dt
        u = 2 * math.pi * (t % PERIOD) / PERIOD
        q_in, ecl = env_loads(beta_deg, u)
        q = {n: 0.0 for n in NODES}
        for c in (1, 2, 3, 4):
            q[f"Q{c}"] += q_in[c] + power[c] - rad_out(T[f"Q{c}"], COL_RAD[c])
        if extra:
            for n, w in extra.items():
                q[n] += w
        q["TANK"] += tank_w
        for (a, b), g in G.items():
            q[a] += g * (T[b] - T[a])
        if heater:
            if T["BATT"] < lim["battery_heater_on_c"]:
                heat_state = 1
            elif T["BATT"] > lim["battery_heater_off_c"]:
                heat_state = 0
            q["BATT"] += lim["battery_heater_w"] * heat_state
        if OPT and heater and optics_heater:
            if T["Q1"] < OPT["heater_on_c"]:
                opt_state = 1
            elif T["Q1"] > OPT["heater_off_c"]:
                opt_state = 0
            q["Q1"] += OPT["heater_w"] * opt_state
        for n in NODES:
            T[n] += q[n] * dt / CAP[n]
        if i >= n_steps - int(5 * PERIOD / dt):
            steps_last += 1
            heater_on_steps += heat_state
            opt_on_steps += opt_state
            eclipse_steps += 1 if ecl else 0
            for n in NODES:
                hist[n].append(T[n])
    res = {n: (min(v), max(v)) for n, v in hist.items()}
    simulate.last_opt_duty = opt_on_steps / max(steps_last, 1)
    return res, heater_on_steps / max(steps_last, 1), eclipse_steps * dt / 5 / 60


def report(title, beta, power, **kw):
    lim = th["limits"]
    res, hduty, ecl_min = simulate(beta, power, **kw)
    imaging = kw.get("optics_heater", True)      # optics window applies only when the telescope is meant to image
    report.last_heater_w = hduty * lim["battery_heater_w"] + simulate.last_opt_duty * (OPT["heater_w"] if OPT else 0.0)
    report.failed = getattr(report, "failed", False)
    print(f"-- {title} (beta {beta} deg, eclipse {ecl_min:.0f} min/orbit, battery heater duty {hduty * 100:.0f} %, "
          f"optics heater {simulate.last_opt_duty * 100:.0f} %, total heat {sum(power.values()):.1f} W) --")
    for n in NODES:
        lo, hi = res[n]
        flag = ""
        if n == "BATT" and (lo < lim["battery_min_c"] or hi > lim["battery_max_c"]):
            flag = "  <-- OUT OF BATTERY LIMITS"
        elif n == "Q1" and imaging and (hi - lo > lim["optics_swing_max_k"] or lo < lim["optics_min_c"] or hi > lim["optics_max_c"]):
            flag = "  <-- telescope column outside optics limits (10..30 C, swing <= 6 K)"
        elif n.startswith("Q") and (lo < lim["electronics_min_c"] or hi > lim["electronics_max_c"]):
            flag = "  <-- OUT OF ELECTRONICS LIMITS"
        if flag and ("BATTERY" in flag or "ELECTRONICS" in flag):
            report.failed = True
        print(f"   {n:5s} {lo:6.1f} .. {hi:6.1f} C   swing {hi - lo:5.1f} K{flag}")
    return res


def main():
    print(f"Orbit period {PERIOD / 60:.1f} min, Earth angular radius {math.degrees(RHO):.1f} deg")
    print("Column masses (kg): " + ", ".join(f"Q{q} {col_mass[q]:.2f}" for q in (1, 2, 3, 4)) +
          f"; battery {batt_mass:.2f}; tank {tank_mass:.2f}")
    print("Average dissipation (W): " + ", ".join(f"Q{q} {col_power[q]:.2f}" for q in (1, 2, 3, 4)))
    print()
    report("NOMINAL, dawn-dusk", 80, col_power)
    print()
    report("NOMINAL, hot case with eclipse", 0, col_power)
    print()
    burst = dict(col_power)
    burst[JETSON_Q] += 10.0
    report("SCIENCE BURST (Jetson +10 W continuous), dawn-dusk", 80, burst)
    print()
    report("SAFE MODE (essential loads only, optics heater off: telescope may cool to the electronics limit), with eclipse", 0, col_power_safe, optics_heater=False)
    heater_w = report.last_heater_w
    safe_budget = sum(m["power_w"] * m["duty"] for m in cfg["module"] if m.get("safe_mode") and ("heater" in m["name"].lower() or "battery containment" in m["name"].lower()))
    print(f"   safe-mode heater power from this model: {heater_w:.1f} W average; budgeted for heaters in safe mode: {safe_budget:.1f} W "
          f"-> {'OK' if heater_w <= safe_budget else 'BUDGET TOO LOW'}")
    if heater_w > safe_budget:
        report.failed = True
    print()
    # environment extremes: cold (aphelion, low albedo) safe mode and hot (perihelion, high albedo) science burst
    global S, ALB, EIR
    keep = (S, ALB, EIR)
    S, ALB, EIR = 1322.0, 0.25, 218.0
    print()
    report("SAFE MODE, COLD environment extreme (flux 1322, albedo 0.25, Earth IR 218)", 0, col_power_safe, optics_heater=False)
    S, ALB, EIR = 1414.0, 0.35, 258.0
    print()
    report("SCIENCE BURST, HOT environment extreme (flux 1414, albedo 0.35, Earth IR 258)", 80, burst)
    S, ALB, EIR = keep
    print()
    burn = dict(col_power_safe)
    burn[JETSON_Q] += 0.0
    res = report("BURN MODE (minimal loads, 50 W thruster; ~35 W lost as heat into the bay), dawn-dusk", 80, burn,
                 tank_w=35.0, optics_heater=False)
    print()
    print("Reading: batteries and electronics limits are checked automatically; a flagged line means the coating, conduction or")
    print("heater assumptions need to change (radiator area, heat straps, wing-back radiators, heater power).")
    return 1 if report.failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
