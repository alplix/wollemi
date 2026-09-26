"""S-band downlink budget (first-order) for the open ground-station kit.

Usage: python sim/link_budget.py
All inputs are estimates; a full budget needs antenna patterns, pointing loss, atmospheric and
polarisation losses and the real modem's required Eb/N0.
"""
import math

FREQ = 2.4e9
ALT_KM = 700
MIN_ELEV = 10.0
TX_W = 2.0                 # spacecraft transmitter power (W)
G_SAT_DBI = 6.0            # patch antenna gain
LOSSES_DB = 3.0            # pointing, polarisation, atmosphere, cable
SYS_TEMP_K = 150.0         # ground receive system noise temperature
REQ_EBN0_DB = 6.5          # QPSK + coding + implementation loss
EFF = 0.55                 # dish aperture efficiency


def slant_range_km(alt, elev_deg):
    re = 6371.0
    e = math.radians(elev_deg)
    return -re * math.sin(e) + math.sqrt((re * math.sin(e)) ** 2 + alt * alt + 2 * re * alt)


def margin(dish_m, rate_bps, elev=MIN_ELEV):
    d = slant_range_km(ALT_KM, elev) * 1e3
    fspl = 20 * math.log10(d) + 20 * math.log10(FREQ) - 147.55
    lam = 3e8 / FREQ
    g_gs = 10 * math.log10(EFF * (math.pi * dish_m / lam) ** 2)
    prx = 10 * math.log10(TX_W) + G_SAT_DBI + g_gs - fspl - LOSSES_DB
    n0 = -228.6 + 10 * math.log10(SYS_TEMP_K)
    ebn0 = prx - n0 - 10 * math.log10(rate_bps)
    return ebn0 - REQ_EBN0_DB, g_gs, d / 1e3


if __name__ == "__main__":
    print(f"{ALT_KM} km, min elevation {MIN_ELEV} deg: slant range {slant_range_km(ALT_KM, MIN_ELEV):.0f} km")
    print(f"{'dish':>6s} {'gain':>7s} " + "".join(f"{r/1e3:>9.0f}kbps" for r in (250e3, 500e3, 1e6, 2e6)))
    for dish in (0.6, 0.9, 1.2, 1.8, 2.4):
        row = []
        for r in (250e3, 500e3, 1e6, 2e6):
            m, g, _ = margin(dish, r)
            row.append(m)
        print(f"{dish:5.1f}m {g:6.1f}dBi " + "".join(f"{m:+11.1f} dB" for m in row))
