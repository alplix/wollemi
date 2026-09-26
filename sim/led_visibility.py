"""Visibility of an LED flasher on the spacecraft as seen from the ground (first-order).

Usage: python sim/led_visibility.py
Magnitude from illuminance: mag 0 = 2.54e-6 lux; naked-eye limit about magnitude 6 at a dark site.
Beam figures are on-axis: the beam must be pointed at the observer, which the nadir-pointing attitude only allows
near the sub-satellite point, so the useful geometry is a short window when the observer is close to the ground track.
"""
import math


def mag(lumens, beam_full_deg, d_km):
    om = 2 * math.pi * (1 - math.cos(math.radians(beam_full_deg / 2)))
    intensity = lumens / om
    lux = intensity / (d_km * 1e3) ** 2
    return intensity, -2.5 * math.log10(lux / 2.54e-6)


if __name__ == "__main__":
    print("LED flasher seen from the ground, on axis, clear sky")
    print(f"{'power':>7s} {'lumens':>7s} {'beam':>6s} {'range':>8s} {'intensity':>11s} {'magnitude':>10s}")
    for watts, lm in ((1, 100), (10, 1000), (30, 3000)):
        for beam in (120, 30, 10, 5):
            for d in (700, 1000):
                i, m = mag(lm, beam, d)
                print(f"{watts:5d} W {lm:7d} {beam:5d}d {d:6d}km {i:9.0f} cd {m:10.1f}")
    print()
    print("Reference: naked-eye limit ~6, Iridium flares reached about -8, the ISS about -4.")
    print("A wide-angle status LED (120 deg) is invisible from orbit; a collimated 10 W flasher can reach the")
    print("naked-eye limit only when pointed at the observer, and is easy to record with a long-exposure camera.")
