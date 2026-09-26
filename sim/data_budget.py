"""Science data budget: production vs downlink capacity.

Usage: python sim/data_budget.py configs/12u_data.toml
"""
import sys
import tomllib


def main(path):
    cfg = tomllib.load(open(path, "rb"))
    L = cfg["link"]
    per_station_mb = (L["sband_rate_bps"] * L["link_efficiency"] * L["pass_s"]
                      * L["passes_per_station_day"]) / 8 / 1e6
    per_pass_mb = per_station_mb / L["passes_per_station_day"]
    uhf_mb = (L["uhf_rate_bps"] * L["uhf_efficiency"] * L["pass_s"]
              * L["passes_per_station_day"]) / 8 / 1e6

    streams = sorted(cfg["stream"], key=lambda s: s["priority"])
    for s in streams:
        s["mb"] = s["raw_mb_day"] / s["ratio"]
    total = sum(s["mb"] for s in streams)
    by_p = {}
    for s in streams:
        by_p[s["priority"]] = by_p.get(s["priority"], 0) + s["mb"]

    print(f"S-band per pass: {per_pass_mb:.0f} MB; per station per day: {per_station_mb:.0f} MB")
    print(f"UHF LoRa per station per day: {uhf_mb:.2f} MB (housekeeping/beacon only)")
    print(f"Non-imaging science data: {total:.1f} MB/day "
          f"(P1 {by_p.get(1, 0):.1f}, P2 {by_p.get(2, 0):.1f}, P3 {by_p.get(3, 0):.1f})")
    print(f"Reserved for updates/commands: {L['ota_reserve_mb_day']} MB/day")
    tele = cfg["imaging"]["telescope"]
    hyp = cfg["imaging"]["hyperspectral"]
    img_mb = tele["raw_mb_per_image"] / tele["ratio"]
    scene_mb = hyp["raw_mb_per_scene"] / hyp["ratio"]
    print(f"Telescope image: {img_mb:.2f} MB compressed; hyperspectral scene: {scene_mb:.0f} MB compressed "
          f"(= {scene_mb / img_mb:.0f} telescope images)")
    print()
    print(f"{'scenario':42s} {'capacity':>9s} {'non-img':>8s} {'left':>7s} {'telescope imgs/day':>19s} {'or hyperspec scenes':>20s}")
    for sc in cfg["scenario"]:
        cap = per_station_mb * sc["stations"]
        left = cap - total - L["ota_reserve_mb_day"]
        if left < 0:
            print(f"{sc['name']:42s} {cap:8.0f}M {total:7.0f}M {left:6.0f}M   NOT ENOUGH for non-imaging data")
            continue
        print(f"{sc['name']:42s} {cap:8.0f}M {total:7.0f}M {left:6.0f}M {left / img_mb:19.0f} {left / scene_mb:20.1f}")
    st = cfg.get("storage")
    if st:
        raw_non = sum(x["raw_mb_day"] for x in streams)
        n_t, n_h = st["imaging_telescope_per_day"], st["imaging_hyperspectral_per_day"]
        raw_img = n_t * tele["raw_mb_per_image"] + n_h * hyp["raw_mb_per_scene"]
        comp_img = n_t * img_mb + n_h * scene_mb
        raw_gb_day = (raw_non + raw_img) / 1000
        comp_gb_day = (total + comp_img) / 1000
        usable = (st["devices"] - st["parity"]) * st["gb_each"]
        print("-- On-board storage --")
        print(f"Installed {st['devices']} x {st['gb_each']} GB, {st['parity']} parity -> {usable} GB usable")
        print(f"Raw production {raw_gb_day:.2f} GB/day ({st['imaging_telescope_per_day']} telescope images + "
              f"{st['imaging_hyperspectral_per_day']} hyperspectral scenes), compressed {comp_gb_day * 1000:.0f} MB/day")
        print(f"Raw ring buffer {st['raw_ring_gb']} GB holds {st['raw_ring_gb'] / raw_gb_day:.0f} days of raw data")
        arch = usable - st["raw_ring_gb"]
        print(f"Archive space {arch} GB holds {arch / comp_gb_day / 365:.1f} years of compressed data if nothing is deleted")
        f = st["device_failure_per_year"]
        for yr in (10, 25, 50):
            alive = st["devices"] * (1 - f) ** yr
            cap = max(0.0, alive - st["parity"]) * st["gb_each"]
            print(f"  after {yr} yr: ~{alive:.1f} of {st['devices']} devices alive, usable ~{cap:.0f} GB "
                  f"(stripe narrows as devices fail)")
    print()
    if total + L["ota_reserve_mb_day"] > uhf_mb:
        print(f"Note: UHF alone ({uhf_mb:.1f} MB/day) cannot carry the {total:.0f} MB/day of science data; "
              f"S-band is required. UHF carries only priority-1 housekeeping subsets.")


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "configs/12u_data.toml")
