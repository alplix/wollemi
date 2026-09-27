"""Visibility of an LED flasher on the spacecraft: to the naked eye on the ground and to cameras / star trackers (first-order).

Usage: python sim/led_visibility.py
Human eye: photopic luminous efficacy V(lambda); mag 0 = 2.54e-6 lux, naked-eye limit about magnitude 6 (dark site).
Cameras and star trackers: energy-equivalent broadband magnitude, mag 0 ~ 1.0e-8 W/m2 over 400-700 nm (approximate Vega).
Violet (405 nm) is almost invisible to the eye (V = 0.0008) but is well inside silicon camera response, so a 'purple' flasher is
mainly a beacon for cameras (ground long-exposure, other spacecraft, star trackers), not for the naked eye.
"""
import math

# (name, wavelength nm, photopic V(lambda), scotopic V'(lambda) [CIE 1951], wall-plug efficiency)
# A dark-site naked-eye limit near magnitude 6 is a rod (scotopic), not cone (photopic), threshold: rods are much more sensitive to blue/violet
# and much less sensitive to red than photopic V(lambda) suggests (the Purkinje effect). Both columns are reported; the scotopic one is the
# physically relevant one for judging whether a point source is visible at the naked-eye limit.
EMITTERS = [
    ("white phosphor LED", 555, 1.0, 0.402, 0.40),      # treated as 100 lm/W electrical for the eye table below
    ("red 630 nm", 630, 0.265, 0.0033, 0.35),
    ("blue 450 nm", 450, 0.038, 0.455, 0.50),
    ("violet 405 nm", 405, 0.0008, 0.022, 0.40),
]
E0_BROAD = 1.0e-8        # W/m2 per magnitude-0 source, 400-700 nm (approximate)
LUX0 = 2.54e-6
EXTINCTION = {630: 0.15, 555: 0.20, 450: 0.32, 405: 0.55}   # magnitudes of atmospheric extinction near 45 deg elevation (approx.)


def solid_angle(beam_full_deg):
    return 2 * math.pi * (1 - math.cos(math.radians(beam_full_deg / 2)))


def eye_mag(elec_w, wl, v, eff, beam, d_km, scotopic_v=None):
    """Photopic-system magnitude by default; pass scotopic_v to get the dark-adapted (rod-vision) equivalent instead
    (same 683 lm/W peak conversion and the same mag-6 threshold, but with V'(lambda) instead of V(lambda))."""
    vv = v if scotopic_v is None else scotopic_v
    if wl == 555 and scotopic_v is None:
        lumens = elec_w * 100.0                   # a white LED: about 100 lm per electrical watt (photopic only; scotopic has no standard lm/W figure)
    else:
        lumens = elec_w * eff * vv * 683.0
    lux = lumens / solid_angle(beam) / (d_km * 1e3) ** 2
    return lumens, -2.5 * math.log10(lux / LUX0) + EXTINCTION[wl]


def off_nadir_angle_deg(elev_deg, alt_km, re_km=6378.137):
    """Off-nadir look angle from the spacecraft to a ground observer at the given elevation (spherical Earth, no refraction)."""
    return math.degrees(math.asin(re_km / (re_km + alt_km) * math.cos(math.radians(elev_deg))))


def camera_mag(elec_w, eff, beam, d_km, qe_rel=1.0):
    opt = elec_w * eff
    e = opt / solid_angle(beam) / (d_km * 1e3) ** 2 * qe_rel
    return opt, -2.5 * math.log10(e / E0_BROAD)


if __name__ == "__main__":
    P, BEAM = 10.0, 10.0
    print(f"{P:.0f} W electrical, {BEAM:.0f} degree beam")
    print()
    elev, alt = 45.0, 700.0
    eta = off_nadir_angle_deg(elev, alt)
    print(f"Naked eye on the ground (range 1000 km, ~{elev:.0f} deg elevation, with atmospheric extinction):")
    print(f"A {elev:.0f} deg elevation observer is about {eta:.0f} deg off nadir at {alt:.0f} km altitude; a {BEAM:.0f} deg beam fixed on nadir does not reach that far, "
          f"so the beacon must be steered (attitude control aims it at the ground track) for this case to apply.")
    print(f"{'emitter':22s} {'lumens (photopic)':>17s} {'mag (photopic)':>15s} {'mag (scotopic, dark-adapted eye)':>33s}   verdict (scotopic)")
    for name, wl, v, vp, eff in EMITTERS:
        lm, m = eye_mag(P, wl, v, eff, BEAM, 1000)
        _, m_scot = eye_mag(P, wl, v, eff, BEAM, 1000, scotopic_v=vp if wl != 555 else v)
        verdict = "easily visible" if m_scot < 4.5 else "visible" if m_scot < 6 else "marginal" if m_scot < 7 else "invisible to the eye"
        print(f"{name:22s} {lm:17.1f} {m:15.1f} {m_scot:33.1f}   {verdict}")
    print()
    print("Long-exposure camera / star tracker / another spacecraft (broadband energy-equivalent magnitude, silicon QE at 405 nm ~ 0.6 of peak):")
    print(f"{'emitter':22s} {'optical W':>9s} " + "".join(f"{d:>9d}km" for d in (1000, 100, 10)))
    for name, wl, v, vp, eff in EMITTERS:
        qe = 0.6 if wl == 405 else 1.0
        row = "".join(f"{camera_mag(P, eff, BEAM, d, qe)[1]:11.1f}" for d in (1000, 100, 10))
        print(f"{name:22s} {P * eff:9.1f} {row}")
    print()
    print("A purple look to the naked eye (photopic, adapted vision looking directly at a bright source) needs red and blue/violet of similar perceived brightness; because the eye is")
    lm_red = P * 0.35 * 0.265 * 683
    print(f"~7x less sensitive to 450 nm and ~330x less to 405 nm than to 630 nm on the photopic scale, 10 W of red gives {lm_red:.0f} lm; the blue side would need on the order of "
          f"{lm_red / (0.5 * 0.038 * 683):.0f} W of electrical power to match it on that scale.")
    print("At the dark-site naked-eye *detection* limit (scotopic, rod vision, not looking straight at it) the ordering reverses: blue and violet are far more visible per watt than red")
    print("(the Purkinje effect), so the scotopic verdicts above are the ones that matter for 'is it visible at all', not the photopic colour-matching ones.")
    print("Reference: a mag 6 star is the naked-eye limit, the ISS is about mag -4; camera magnitudes above are versus a bright star (mag 0).")
