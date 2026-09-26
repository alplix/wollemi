"""Visibility of an LED flasher on the spacecraft: to the naked eye on the ground and to cameras / star trackers (first-order).

Usage: python sim/led_visibility.py
Human eye: photopic luminous efficacy V(lambda); mag 0 = 2.54e-6 lux, naked-eye limit about magnitude 6 (dark site).
Cameras and star trackers: energy-equivalent broadband magnitude, mag 0 ~ 1.0e-8 W/m2 over 400-700 nm (approximate Vega).
Violet (405 nm) is almost invisible to the eye (V = 0.0008) but is well inside silicon camera response, so a 'purple' flasher is
mainly a beacon for cameras (ground long-exposure, other spacecraft, star trackers), not for the naked eye.
"""
import math

# (name, wavelength nm, photopic V, wall-plug efficiency)
EMITTERS = [
    ("white phosphor LED", 555, 1.0, 0.40),      # treated as 100 lm/W electrical for the eye table below
    ("red 630 nm", 630, 0.265, 0.35),
    ("blue 450 nm", 450, 0.038, 0.50),
    ("violet 405 nm", 405, 0.0008, 0.40),
]
E0_BROAD = 1.0e-8        # W/m2 per magnitude-0 source, 400-700 nm (approximate)
LUX0 = 2.54e-6
EXTINCTION = {630: 0.15, 555: 0.20, 450: 0.32, 405: 0.55}   # magnitudes of atmospheric extinction near 45 deg elevation (approx.)


def solid_angle(beam_full_deg):
    return 2 * math.pi * (1 - math.cos(math.radians(beam_full_deg / 2)))


def eye_mag(elec_w, wl, v, eff, beam, d_km):
    if wl == 555:
        lumens = elec_w * 100.0                   # a white LED: about 100 lm per electrical watt
    else:
        lumens = elec_w * eff * v * 683.0
    lux = lumens / solid_angle(beam) / (d_km * 1e3) ** 2
    return lumens, -2.5 * math.log10(lux / LUX0) + EXTINCTION[wl]


def camera_mag(elec_w, eff, beam, d_km, qe_rel=1.0):
    opt = elec_w * eff
    e = opt / solid_angle(beam) / (d_km * 1e3) ** 2 * qe_rel
    return opt, -2.5 * math.log10(e / E0_BROAD)


if __name__ == "__main__":
    P, BEAM = 10.0, 10.0
    print(f"{P:.0f} W electrical, {BEAM:.0f} degree beam")
    print()
    print("Naked eye on the ground (range 1000 km, ~45 deg elevation, with atmospheric extinction):")
    print(f"{'emitter':22s} {'lumens':>8s} {'magnitude':>10s}   verdict")
    for name, wl, v, eff in EMITTERS:
        lm, m = eye_mag(P, wl, v, eff, BEAM, 1000)
        verdict = "easily visible" if m < 4.5 else "visible" if m < 6 else "marginal" if m < 7 else "invisible to the eye"
        print(f"{name:22s} {lm:8.1f} {m:10.1f}   {verdict}")
    print()
    print("Long-exposure camera / star tracker / another spacecraft (broadband energy-equivalent magnitude, silicon QE at 405 nm ~ 0.6 of peak):")
    print(f"{'emitter':22s} {'optical W':>9s} " + "".join(f"{d:>9d}km" for d in (1000, 100, 10)))
    for name, wl, v, eff in EMITTERS:
        qe = 0.6 if wl == 405 else 1.0
        row = "".join(f"{camera_mag(P, eff, BEAM, d, qe)[1]:11.1f}" for d in (1000, 100, 10))
        print(f"{name:22s} {P * eff:9.1f} {row}")
    print()
    print("A purple look to the naked eye needs red and blue/violet of similar perceived brightness; because the eye is ~30x less sensitive to 450 nm and ~300x")
    lm_red = P * 0.35 * 0.265 * 683
    print(f"less to 405 nm than to 630 nm, 10 W of red gives {lm_red:.0f} lm; the blue side would need on the order of {lm_red / (0.5 * 0.038 * 683):.0f} W of electrical power to match it.")
    print("Reference: a mag 6 star is the naked-eye limit, the ISS is about mag -4; camera magnitudes above are versus a bright star (mag 0).")
