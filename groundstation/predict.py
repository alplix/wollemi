"""Pass prediction and Doppler for the Wollemi ground kit (uses the sgp4 package: pip install sgp4).

Usage:
  python groundstation/predict.py                     # demo: 700 km sun-synchronous orbit, three sites
  python groundstation/predict.py --tle L1 L2 --lat 39.93 --lon 32.86 --alt 0.9 --days 3

The demo orbit is synthetic (a nominal dawn-dusk-like 700 km sun-synchronous orbit); use real orbit
elements from the operator once the spacecraft exists.
"""
import argparse
import math
from datetime import datetime, timedelta, timezone

from sgp4.api import Satrec, jday
from sgp4.conveniences import sat_epoch_datetime

WGS84_A = 6378.137
WGS84_F = 1 / 298.257223563
C_KM_S = 299792.458


def tle_checksum(line):
    total = 0
    for ch in line[:68]:
        if ch.isdigit():
            total += int(ch)
        elif ch == "-":
            total += 1
    return total % 10


def make_tle(inc_deg, raan_deg, ecc, argp_deg, ma_deg, mean_motion, epoch=(2026, 270.5), satnum=99999, name="WOLLEMI"):
    yy, doy = epoch
    l1 = f"1 {satnum:05d}U 26001A   {yy % 100:02d}{doy:012.8f}  .00000200  00000-0  10000-3 0  999"
    l1 = l1[:68].ljust(68)
    l2 = (f"2 {satnum:05d} {inc_deg:8.4f} {raan_deg:8.4f} {int(round(ecc * 1e7)):07d} {argp_deg:8.4f} {ma_deg:8.4f} "
          f"{mean_motion:11.8f}00001")
    l2 = l2[:68].ljust(68)
    return l1 + str(tle_checksum(l1)), l2 + str(tle_checksum(l2))


def gmst(jd, fr):
    from sgp4.propagation import gstime
    return gstime(jd + fr)


def geodetic_to_ecef(lat_deg, lon_deg, alt_km):
    lat, lon = math.radians(lat_deg), math.radians(lon_deg)
    e2 = WGS84_F * (2 - WGS84_F)
    n = WGS84_A / math.sqrt(1 - e2 * math.sin(lat) ** 2)
    return ((n + alt_km) * math.cos(lat) * math.cos(lon), (n + alt_km) * math.cos(lat) * math.sin(lon),
            (n * (1 - e2) + alt_km) * math.sin(lat))


def teme_to_ecef(r, theta):
    c, s = math.cos(theta), math.sin(theta)
    return (c * r[0] + s * r[1], -s * r[0] + c * r[1], r[2])


def look(sat, t, site):
    """Return (elevation deg, range km) of the satellite from the site at datetime t (UTC)."""
    jd, fr = jday(t.year, t.month, t.day, t.hour, t.minute, t.second + t.microsecond / 1e6)
    e, r, v = sat.sgp4(jd, fr)
    if e != 0:
        return -90.0, 1e9
    rec = teme_to_ecef(r, gmst(jd, fr))
    lat, lon = math.radians(site[0]), math.radians(site[1])
    ox, oy, oz = geodetic_to_ecef(*site)
    dx, dy, dz = rec[0] - ox, rec[1] - oy, rec[2] - oz
    east = -math.sin(lon) * dx + math.cos(lon) * dy
    north = -math.sin(lat) * math.cos(lon) * dx - math.sin(lat) * math.sin(lon) * dy + math.cos(lat) * dz
    up = math.cos(lat) * math.cos(lon) * dx + math.cos(lat) * math.sin(lon) * dy + math.sin(lat) * dz
    rng = math.sqrt(east ** 2 + north ** 2 + up ** 2)
    return math.degrees(math.asin(up / rng)), rng


def doppler(sat, t, site, freq_hz):
    """Doppler shift (Hz) and rate (Hz/s) by finite differences of the slant range."""
    dt = timedelta(seconds=0.5)
    e0, r0 = look(sat, t - dt, site)
    e1, r1 = look(sat, t + dt, site)
    rr = (r1 - r0) / 1.0                    # km/s, positive when receding
    return -rr / C_KM_S * freq_hz


def passes(sat, site, start, days, min_elev=10.0, step=15):
    out, prev_up, cur = [], False, None
    n = int(days * 86400 / step)
    for i in range(n + 1):
        t = start + timedelta(seconds=i * step)
        el, rng = look(sat, t, site)
        up = el >= min_elev
        if up and not prev_up:
            cur = {"aos": t, "max_el": el, "t_max": t}
        if up and cur and el > cur["max_el"]:
            cur["max_el"], cur["t_max"] = el, t
        if not up and prev_up and cur:
            cur["los"] = t
            out.append(cur)
            cur = None
        prev_up = up
    return out


def report(name, sat, site, start, days, min_elev):
    ps = passes(sat, site, start, days, min_elev)
    dur = [(p["los"] - p["aos"]).total_seconds() for p in ps]
    per_day = len(ps) / days
    tot = sum(dur) / days
    print(f"{name:28s} passes/day {per_day:5.1f}  mean {sum(dur) / max(len(dur), 1):5.0f} s  "
          f"longest {max(dur, default=0):5.0f} s  contact {tot / 60:5.1f} min/day  "
          f"max elev >= 40 deg: {sum(1 for p in ps if p['max_el'] >= 40) / days:4.1f}/day")
    return ps


def doppler_stats(sat, ps, site):
    best = (0.0, 0.0)
    for p in ps[:12]:
        t = p["aos"]
        while t < p["los"]:
            for f in (433e6, 2.4e9):
                d = doppler(sat, t, site, f)
                d2 = doppler(sat, t + timedelta(seconds=1), site, f)
                if f == 2.4e9:
                    best = (max(best[0], abs(d)), max(best[1], abs(d2 - d)))
            t += timedelta(seconds=5)
    return best


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--tle", nargs=2)
    ap.add_argument("--lat", type=float)
    ap.add_argument("--lon", type=float)
    ap.add_argument("--alt", type=float, default=0.0)
    ap.add_argument("--days", type=float, default=7.0)
    ap.add_argument("--min-elev", type=float, default=10.0)
    a = ap.parse_args()
    if a.tle:
        l1, l2 = a.tle
    else:
        l1, l2 = make_tle(98.19, 94.5, 0.0011, 90.0, 0.0, 14.575, epoch=(2026, 270.0))
        print("Synthetic TLE (700 km dawn-dusk sun-synchronous, RAAN = Sun RA - 90 deg):")
        print(l1)
        print(l2)
    sat = Satrec.twoline2rv(l1, l2)
    start = sat_epoch_datetime(sat).astimezone(timezone.utc) if hasattr(sat_epoch_datetime(sat), "astimezone") \
        else datetime(2026, 9, 27, tzinfo=timezone.utc)
    sites = [("custom", (a.lat, a.lon, a.alt))] if a.lat is not None else \
        [("Ankara (39.9N 32.9E)", (39.93, 32.86, 0.9)), ("Istanbul (41.0N 29.0E)", (41.01, 28.98, 0.05)),
         ("Tromso (69.7N 19.0E)", (69.65, 18.96, 0.05)), ("Singapore (1.3N 103.8E)", (1.35, 103.82, 0.02))]
    print(f"\nPass statistics, minimum elevation {a.min_elev:.0f} deg, {a.days:.0f} days from the TLE epoch:")
    ps_first = None
    for nme, site in sites:
        ps = report(nme, sat, site, start, a.days, a.min_elev)
        if ps_first is None:
            ps_first, site_first = ps, site
    if ps_first:
        dmax, drate = doppler_stats(sat, ps_first, site_first)
        print(f"\nDoppler at 2.4 GHz (first site): up to +-{dmax / 1e3:.0f} kHz, rate up to {drate / 1e3:.1f} kHz/s")
        print(f"Doppler at 433 MHz would be about +-{dmax * 433 / 2400 / 1e3:.0f} kHz")


if __name__ == "__main__":
    main()
