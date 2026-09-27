"""First-order structural and launch-load analysis for the 12U (no finite-element model yet).

Usage: python sim/structure.py
Covers: fundamental frequency estimates, quasi-static load on the rails, bolted mounts of the heavy items, wing hold-down, and random
vibration of the card boards (Miles and Steinberg). Every figure is a hand calculation with stated assumptions; the launch provider's real
load specification and a finite-element model with modal testing must replace it.
"""
import math
import os
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
S = tomllib.load(open(os.path.join(ROOT, "configs", "12u_structure.toml"), "rb"))
CFG = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
GEO = tomllib.load(open(os.path.join(ROOT, "configs", "12u_geometry.toml"), "rb"))

G = 9.81
E = S["materials"]["al6061"]["E_gpa"] * 1e9
RHO = S["materials"]["al6061"]["rho"]
SY = S["materials"]["al6061"]["yield_mpa"] * 1e6
LQ = S["launch"]
MASS = sum(m["mass_kg"] for m in CFG["module"])
results = []          # (name, margin, required, note)


def record(name, margin, required, note=""):
    results.append((name, margin, required, note))
    flag = "OK  " if margin >= required else "FAIL"
    print(f"[{flag}] {name}: margin {margin:.2f} (needs >= {required:.2f}) {note}")


def frame_frequencies():
    f = S["frame"]
    b, t, L = f["outer_m"], f["wall_m"], f["length_m"]
    I = (b ** 4 - (b - 2 * t) ** 4) / 12                       # thin-walled square tube
    m_line = MASS / L
    # uniform cantilever: rails clamped at the dispenser plane, whole mass distributed along the length
    f_bend = (1.875 ** 2) / (2 * math.pi) * math.sqrt(E * I / (m_line * L ** 4))
    # axial: stiff rails carry the load; lumped mass on the rail area
    A = 4 * f["rail_m"] ** 2 + 4 * b * t * 0.5
    f_axial = 1 / (2 * math.pi) * math.sqrt(E * A / (L * MASS / 3.0)) / 1.0
    # side wall plate, simply supported on the rails and bulkheads
    a, bb = b, L
    D = E * t ** 3 / (12 * (1 - S["materials"]["al6061"]["nu"] ** 2))
    f_plate = (math.pi / 2) * math.sqrt(D / (RHO * t)) * (1 / a ** 2 + 1 / bb ** 2)
    f_plate_loaded = f_plate / math.sqrt(1 + 0.5)              # attached cells and modules add ~50 % mass
    print(f"Mass {MASS:.2f} kg; frame lateral bending (cantilever estimate) {f_bend:.0f} Hz; axial {f_axial:.0f} Hz; "
          f"side wall panel {f_plate:.0f} Hz bare, {f_plate_loaded:.0f} Hz loaded")
    return f_bend, f_axial, f_plate_loaded


def wing_panel_frequency():
    wp = S["materials"]["pcb_cell_panel"]
    t = GEO["wings"]["panel"][2] * 1e-3
    a, bb = GEO["wings"]["panel"][0] * 1e-3, GEO["wings"]["panel"][1] * 1e-3
    D = wp["E_gpa"] * 1e9 * t ** 3 / (12 * (1 - 0.3 ** 2))
    f_edges = (math.pi / 2) * math.sqrt(D / (wp["rho"] * t)) * (1 / a ** 2 + 1 / bb ** 2)
    per_edge = S["wing"]["hold_down_points"] // 2
    b_eff = bb / (per_edge - 1) if per_edge >= 2 else bb
    f_ss = (math.pi / 2) * math.sqrt(D / (wp["rho"] * t)) * (1 / a ** 2 + 1 / b_eff ** 2)
    print(f"Stowed wing panel ({a * 1e3:.0f} x {bb * 1e3:.0f} x {t * 1e3:.1f} mm): {f_edges:.0f} Hz if supported only at its ends; with {per_edge} hold-down posts "
          f"along each long edge the free span is {b_eff * 1e3:.0f} mm and the mode rises to {f_ss:.0f} Hz")
    return f_ss


def rails_and_loads():
    a = LQ["quasi_static_g"] * G
    f = S["frame"]
    force = MASS * a
    A_rails = 4 * f["rail_m"] ** 2
    stress = force / A_rails
    print(f"Quasi-static {LQ['quasi_static_g']:.0f} g: total load {force:.0f} N; axial stress in the rails {stress / 1e6:.1f} MPa "
          f"(yield {SY / 1e6:.0f} MPa)")
    record("Rails axial stress", SY / (stress * LQ["factor_of_safety_yield"]), 1.0, "(margin of safety = yield / (FoS x stress))")
    # overturning: lateral load at the centre of mass acting on the rail cantilever
    M = force * f["length_m"] / 2
    b = f["outer_m"]
    I = (b ** 4 - (b - 2 * f["wall_m"]) ** 4) / 12
    sigma = M * (b / 2) / I
    record("Frame bending stress (lateral)", SY / (sigma * LQ["factor_of_safety_yield"]), 1.0,
           f"(bending stress {sigma / 1e6:.1f} MPa at {LQ['quasi_static_g']:.0f} g)")


def mounts():
    print()
    print("Bolted mounts of the heavy items (quasi-static load x local amplification, shear plus overturning tension):")
    factor = LQ["quasi_static_g"] * LQ["local_amplification"] * G
    for mt in S["mount"]:
        mod = next((m for m in CFG["module"] if m["name"].startswith(mt["match"])), None)
        if not mod:
            continue
        fs = S["fastener"][mt["type"]]
        m = mod["mass_kg"]
        F = m * factor
        shear_each = F / mt["count"]
        M = F * mt["lever_m"]
        tens_each = M / (mt["bolt_circle_m"] * mt["count"] / 4)   # crude: moment carried by the bolts on the tension side
        cap_shear = fs["shear_area_mm2"] * 1e-6 * fs["shear_strength_mpa"] * 1e6
        cap_tens = fs["tensile_area_mm2"] * 1e-6 * fs["tensile_strength_mpa"] * 1e6
        ratio = (shear_each / cap_shear) ** 2 + (tens_each / cap_tens) ** 2     # interaction (ellipse)
        margin = 1 / (math.sqrt(ratio) * LQ["factor_of_safety_ultimate"])
        record(f"Mount {mt['match'][:32]}", margin, 1.0, f"({m:.2f} kg, {mt['count']} x {mt['type'][:2].upper()}, {shear_each:.0f} N shear, {tens_each:.0f} N tension per bolt)")


def wing_hold_down():
    print()
    w = S["wing"]
    pw, pl, pt = GEO["wings"]["panel"]
    n = GEO["wings"]["panels_per_wing"]
    m_stack = n * (pw * 1e-3) * (pl * 1e-3) * w["panel_areal_mass_kg_m2"]
    F = m_stack * LQ["quasi_static_g"] * LQ["local_amplification"] * G
    per_point = F / w["hold_down_points"]
    print(f"Wing stack {m_stack:.2f} kg; load at {LQ['quasi_static_g'] * LQ['local_amplification']:.0f} g: {F:.0f} N, {per_point:.0f} N per hold-down point; preload {w['preload_n']:.0f} N per point")
    # the stack presses onto the wall: friction plus the preload keeps it from sliding; tension = preload must exceed the lifting load
    lift_per_point = per_point                                   # worst case: whole load as lift-off
    record("Wing hold-down preload vs lift-off", w["preload_n"] / (lift_per_point * 1.0), 1.0,
           "(preload must exceed the per-point inertia load; burn-wire release adds a margin)")


def random_vibration():
    print()
    asd = LQ["random_asd_g2_per_hz"]
    Q = LQ["q_factor"]
    gr = math.sqrt(asd * (LQ["random_f_high"] - LQ["random_f_low"]))
    print(f"Input random profile: flat {asd} g2/Hz, {gr:.1f} Grms. Miles: response at resonance f -> Grms = sqrt(pi/2 * f * Q * ASD)")
    print(f"{'card fundamental':>18s} {'3-sigma G':>10s} {'3-sigma deflection':>19s} {'Steinberg limit':>16s} {'margin':>7s}")
    B_in, h_in, L_in = 3.94, 0.063, 1.0          # 100 mm card, 1.6 mm, 25 mm component at the centre
    C_LEADED, C_BGA = 1.0, 1.75                  # Steinberg component constant: 1.0 leaded/through-hole, 1.75 leadless/BGA-like (more fatigue-sensitive)
    z_allow_leaded_in = 0.00022 * B_in / (C_LEADED * h_in * math.sqrt(L_in))
    z_allow_bga_in = 0.00022 * B_in / (C_BGA * h_in * math.sqrt(L_in))
    for f in (100, 150, 200, 220, 300, 500):
        grms = math.sqrt(math.pi / 2 * f * Q * asd)
        g3 = 3 * grms
        z_m = 0.248 * g3 / f ** 2
        z_in = z_m / 0.0254
        margin_leaded = z_allow_leaded_in / z_in
        margin_bga = z_allow_bga_in / z_in
        print(f"{f:16d} Hz {g3:10.1f} {z_m * 1e3:16.3f} mm {z_allow_leaded_in * 25.4:13.3f} mm {margin_leaded:7.2f}  {margin_bga:7.2f} (BGA/leadless, C={C_BGA})")
        if f == 220:
            m200_leaded, m200_bga = margin_leaded, margin_bga
    print("Cards must therefore keep their first mode near or above 220 Hz (edge guides on two edges, 3 mm keep-out, stiffener rails on large boards; the extra 20 Hz over the original 200 Hz target covers BGA/leadless parts at Steinberg C=1.75).")
    print("This does not include amplification by the wall-panel mode (~167 Hz, Q~10): a card resonance close to that frequency would see a higher input than modelled here.")
    record("Card board Steinberg margin at 220 Hz (leaded parts)", m200_leaded, 1.0)
    record("Card board Steinberg margin at 220 Hz (BGA/leadless parts, C=1.75)", m200_bga, 1.0)


def main():
    print("== Structural analysis (hand calculations, no FEM) ==")
    fb, fa, fp = frame_frequencies()
    fw = wing_panel_frequency()
    fmin = S["launch"]["minimum_first_mode_hz"]
    record("First mode (frame bending) vs minimum", fb / fmin, 1.0, f"({fb:.0f} Hz vs {fmin:.0f} Hz)")
    record("Side wall panel mode vs minimum", fp / fmin, 1.0, f"({fp:.0f} Hz)")
    record("Stowed wing panel mode vs minimum", fw / fmin, 1.0, f"({fw:.0f} Hz)")
    rails_and_loads()
    mounts()
    wing_hold_down()
    random_vibration()
    fails = [r for r in results if r[1] < r[2]]
    print()
    print(f"Verdict: {len(results) - len(fails)} of {len(results)} structural checks meet their margin"
          + ("; failing: " + ", ".join(r[0] for r in fails) if fails else "."))
    return 1 if fails else 0


if __name__ == "__main__":
    raise SystemExit(main())
