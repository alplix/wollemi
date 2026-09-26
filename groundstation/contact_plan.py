"""Contact plan for the reference station: passes with roles (command, bulk downlink, housekeeping).

Usage: python groundstation/contact_plan.py [days] [--lat 37.92 --lon 29.12 --alt 0.35]
Roles: the highest pass of each day carries the bulk S-band downlink; the first pass of each day is used for command upload and time sync;
passes below 20 degrees maximum elevation are housekeeping/UHF only. Uses the synthetic 700 km sun-synchronous orbit of predict.py.
Times are UTC and Turkey local time (UTC+3).
"""
import argparse
import os
import sys
from datetime import timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sgp4.api import Satrec
from sgp4.conveniences import sat_epoch_datetime
import predict


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("days", nargs="?", type=float, default=3.0)
    ap.add_argument("--lat", type=float, default=37.92)
    ap.add_argument("--lon", type=float, default=29.12)
    ap.add_argument("--alt", type=float, default=0.35)
    a = ap.parse_args()
    l1, l2 = predict.make_tle(98.19, 94.5, 0.0011, 90.0, 0.0, 14.575, epoch=(2026, 270.0))
    sat = Satrec.twoline2rv(l1, l2)
    start = sat_epoch_datetime(sat).astimezone(timezone.utc)
    site = (a.lat, a.lon, a.alt)
    passes = predict.passes(sat, site, start, a.days, 10.0, step=10)
    tz = timedelta(hours=3)
    print(f"Contact plan for {a.days:.0f} days at {a.lat:.2f} N {a.lon:.2f} E (synthetic orbit, UTC / local UTC+3):")
    print(f"{'day':>3s} {'AOS UTC':>8s} {'local':>6s} {'dur s':>6s} {'max el':>7s}  role")
    by_day = {}
    for p in passes:
        by_day.setdefault((p["aos"] - start).days, []).append(p)
    total_bulk = 0.0
    for day in sorted(by_day):
        ps = by_day[day]
        best = max(ps, key=lambda p: p["max_el"])
        first = ps[0]
        for p in ps:
            dur = (p["los"] - p["aos"]).total_seconds()
            roles = []
            if p is first:
                roles.append("command upload + time sync")
            if p is best:
                roles.append("BULK S-band downlink")
            if not roles:
                roles.append("housekeeping / extra downlink" if p["max_el"] >= 20 else "UHF housekeeping only")
            if "BULK" in roles[-1] or p["max_el"] >= 20:
                total_bulk += dur
            print(f"{day:3d} {p['aos'].strftime('%H:%M:%S'):>8s} {(p['aos'] + tz).strftime('%H:%M'):>6s} {dur:6.0f} {p['max_el']:6.0f}d  {' + '.join(roles)}")
    n_days = max(len(by_day), 1)
    print(f"\nUsable S-band time (passes >= 20 deg or bulk role): {total_bulk / n_days / 60:.1f} min/day on average")
    print("A missed pass moves its role to the next pass of the day; commands are always sent 24-48 h ahead of their execution time (COLAV-2).")


if __name__ == "__main__":
    main()
