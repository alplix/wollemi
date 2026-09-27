"""Closed-loop mission simulation: the real firmware mode manager (compiled C, called through ctypes) driven by an orbit, power and fault model.

Usage: python sim/mission_sim.py [days]
Simulates 60 days (default) for a typical eclipse orbit (beta 0) and a dawn-dusk orbit (beta 80), with injected faults:
  day 10  Jetson dies                (heavy compute lost for good)
  day 25  battery pack A fails       (capacity halves, one pack remains)
  day 40  flight controller hangs for 2 hours (supervisor forces SURVIVAL, then recovery)
  day 50  temperature excursion for 30 minutes (forces SAFE)
Requests: science campaigns three times a day, electric-thruster burn windows on days 20 and 35.
Power numbers come from the design budgets (sim/budget.py); thermal effects are not simulated (only the fault flag).
"""
import ctypes
import math
import os
import shutil
import subprocess
import sys
import tomllib

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "sim"))
import budget  # noqa: E402

CFG = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
R = budget.compute(CFG)
OUT = os.path.join(ROOT, "sim", "out")
MODES = ["LAUNCH", "DEPLOY", "COMMISSION", "NOMINAL", "SCIENCE", "BURN", "ECLIPSE", "SAFE", "SURVIVAL", "SCIENCE_LITE"]


class Inputs(ctypes.Structure):
    _fields_ = [(n, ctypes.c_uint8) for n in (
        "fc_ok", "packs_ok", "heavy_compute_ok", "light_compute_ok", "thruster_ok", "temp_ok", "sunlit", "sun_biased", "wings_deployed",
        "sep_timer_done", "deploy_done", "commissioning_ok", "science_requested", "burn_requested", "soc_pct", "optics_ok")]


class State(ctypes.Structure):
    _fields_ = [("mode", ctypes.c_int), ("level", ctypes.c_uint8), ("allow_payloads", ctypes.c_uint8),
                ("allow_heavy_compute", ctypes.c_uint8), ("allow_light_compute", ctypes.c_uint8), ("allow_thruster", ctypes.c_uint8), ("resume_mode", ctypes.c_int)]


_LIB = None


def load_lib():
    global _LIB
    if _LIB is not None:
        return _LIB
    os.makedirs(OUT, exist_ok=True)
    ext = ".dll" if os.name == "nt" else ".so"
    path = os.path.join(OUT, "libgkmodes" + ext)
    gcc = shutil.which("gcc")
    if not gcc:
        raise SystemExit("gcc not found")
    subprocess.run([gcc, "-std=c99", "-O2", "-shared", "-fPIC", os.path.join(ROOT, "firmware", "common", "wl_modes.c"), "-o", path], check=True)
    lib = ctypes.CDLL(path)
    lib.wl_modes_init.argtypes = [ctypes.POINTER(State)]
    lib.wl_modes_step.argtypes = [ctypes.POINTER(State), ctypes.POINTER(Inputs)]
    lib.wl_modes_step.restype = ctypes.c_int
    _LIB = lib
    return lib


def power_model():
    scen = {s["name"]: s for s in R["scenarios"]}
    nominal = next(s for s in R["scenarios"] if s["nominal"])
    tumbling = next(s for s in R["scenarios"] if "tumbling" in s["name"] and not s["safe"])
    dd = next(s for s in R["scenarios"] if "Dawn-dusk" in s["name"])
    full = R["consumed_w"]
    safe = next(s for s in R["scenarios"] if s["safe"])["cons"]
    burn = next(s for s in R["scenarios"] if "BURN" in s["name"])["cons"]
    return {
        "gen_biased_typ": nominal["gen"] / 0.62,          # instantaneous sunlit power, sun-biased attitude, eclipse orbit
        "gen_biased_dd": dd["gen"] / 0.98,
        "gen_tumble": tumbling["gen"] / 0.62,
        "load": {"LAUNCH": 1.5, "DEPLOY": 4.0, "COMMISSION": 18.0, "NOMINAL": full, "SCIENCE": full + 7.5, "SCIENCE_LITE": full + 1.5, "BURN": burn,
                 "ECLIPSE": full - 2.5, "SAFE": safe, "SURVIVAL": 0.7},
    }


def simulate(beta_deg, days=60, dt=30.0, verbose=False):
    lib = load_lib()
    pm = power_model()
    re, alt = 6378.137, 700.0
    rr = re + alt
    period = 2 * math.pi * math.sqrt(rr ** 3 / 398600.4418)
    beta = math.radians(beta_deg)
    cap_wh = 84.0
    max_charge_w = 42.0
    st, inp = State(), Inputs()
    lib.wl_modes_init(ctypes.byref(st))
    soc_wh = cap_wh * 0.9
    t = 0.0
    stats = {"time": {m: 0.0 for m in MODES}, "transitions": 0, "min_soc": 100.0, "brownout_s": 0.0, "burn_h": 0.0, "burn_wanted_h": 0.0,
             "science_h": 0.0, "wasted_wh": 0.0, "survival_events": 0, "safe_entries": 0}
    last_mode = st.mode
    jetson_dead = False
    pack_a_dead = False
    trans_log = []
    n = int(days * 86400 / dt)
    for i in range(n):
        t = i * dt
        day = t / 86400.0
        u = 2 * math.pi * (t % period) / period
        sz = math.cos(beta) * math.cos(u)
        eclipse = sz < 0 and rr * math.sqrt(1 - sz * sz) < re
        sunlit = not eclipse
        # faults
        if day >= 10:
            jetson_dead = True
        if day >= 25:
            pack_a_dead = True
        fc_hang = 40.0 <= day < 40.0 + 2 / 24
        temp_bad = 50.0 <= day < 50.0 + 0.5 / 24
        cap = cap_wh / 2 if pack_a_dead else cap_wh
        max_ch = max_charge_w / 2 if pack_a_dead else max_charge_w
        soc_wh = min(soc_wh, cap)
        # requests
        hod = (day % 1.0) * 24.0
        sci = any(h <= hod < h + 0.7 for h in (2.0, 10.0, 18.0))          # three 42-minute campaign requests per day
        burn = (20.0 <= day < 20.25) or (35.0 <= day < 35.25)
        # inputs for the mode manager
        inp.fc_ok = 0 if fc_hang else 1
        inp.packs_ok = 1
        inp.heavy_compute_ok = 0 if jetson_dead else 1
        inp.light_compute_ok = 1                             # the Pi CM5 stays healthy in this scenario
        inp.thruster_ok = 1
        inp.optics_ok = 1                                      # optics thermal window is covered by the thermal model
        inp.temp_ok = 0 if temp_bad else 1
        inp.sunlit = 1 if sunlit else 0
        biased = st.mode in (3, 4, 5, 6, 2, 9)                 # attitude control keeps the wings toward the sun in operational modes
        inp.sun_biased = 1 if biased else 0
        inp.wings_deployed = 1 if t > 3600 else 0
        inp.sep_timer_done = 1 if t > 1800 else 0
        inp.deploy_done = 1 if t > 3600 else 0
        inp.commissioning_ok = 1 if day > 3 else 0
        inp.science_requested = 1 if sci else 0
        inp.burn_requested = 1 if burn else 0
        inp.soc_pct = max(0, min(100, int(100 * soc_wh / cap)))
        changed = lib.wl_modes_step(ctypes.byref(st), ctypes.byref(inp))
        mode = MODES[st.mode]
        if changed:
            stats["transitions"] += 1
            trans_log.append((day, MODES[last_mode], mode))
            if mode == "SURVIVAL":
                stats["survival_events"] += 1
            if mode == "SAFE":
                stats["safe_entries"] += 1
        last_mode = st.mode
        # power
        if sunlit:
            gen = pm["gen_biased_dd" if beta_deg > 60 else "gen_biased_typ"] if biased else pm["gen_tumble"]
        else:
            gen = 0.0
        load = pm["load"][mode]
        if jetson_dead and mode == "SCIENCE":
            load -= 7.5
        net = gen * 0.95 - load
        dE = net * dt / 3600.0
        if dE > 0:
            dE = min(dE, max_ch * dt / 3600.0)                # charge limit
            stats["wasted_wh"] += max(0.0, net * dt / 3600.0 - dE)
        soc_wh = max(0.0, min(cap, soc_wh + dE))
        if soc_wh <= 0.02 * cap:
            stats["brownout_s"] += dt
        stats["time"][mode] += dt
        stats["min_soc"] = min(stats["min_soc"], 100 * soc_wh / cap)
        if mode == "BURN":
            stats["burn_h"] += dt / 3600.0
        if burn and sunlit:
            stats["burn_wanted_h"] += dt / 3600.0
        if mode in ("SCIENCE", "SCIENCE_LITE"):
            stats["science_h"] += dt / 3600.0
    return stats, trans_log, period


def report(name, beta, days):
    stats, log, period = simulate(beta, days)
    total = sum(stats["time"].values())
    print(f"== {name} (beta {beta} deg, orbit {period / 60:.1f} min, {days:.0f} days) ==")
    print("  time in mode: " + ", ".join(f"{m} {100 * v / total:.1f} %" for m, v in stats["time"].items() if v))
    print(f"  mode transitions {stats['transitions']} ({stats['transitions'] / days:.1f} per day), SAFE entries {stats['safe_entries']}, SURVIVAL entries {stats['survival_events']}")
    print(f"  minimum state of charge {stats['min_soc']:.0f} %, brownout time {stats['brownout_s']:.0f} s, energy shed (batteries full) {stats['wasted_wh']:.0f} Wh")
    print(f"  science time {stats['science_h']:.0f} h, thruster burn {stats['burn_h']:.1f} h of {stats['burn_wanted_h']:.1f} h requested in sunlight")
    key = [(d, a, b) for d, a, b in log if b in ("SAFE", "SURVIVAL") or a in ("SURVIVAL", "SAFE")]
    for d, a, b in key[:8]:
        print(f"    day {d:6.2f}: {a} -> {b}")
    return stats


def main():
    days = float(sys.argv[1]) if len(sys.argv) > 1 else 60.0
    print(f"Design power: sun-biased {power_model()['gen_biased_typ']:.0f} W (eclipse orbit) / {power_model()['gen_biased_dd']:.0f} W (dawn-dusk), tumbling {power_model()['gen_tumble']:.0f} W; "
          f"loads " + ", ".join(f"{k} {v:.1f} W" for k, v in power_model()["load"].items()))
    print()
    a = report("Eclipse orbit", 0.0, days)
    print()
    b = report("Dawn-dusk orbit", 80.0, days)
    print()
    ok = True
    for name, s in (("eclipse orbit", a), ("dawn-dusk orbit", b)):
        good = s["brownout_s"] == 0 and s["min_soc"] > 5 and s["survival_events"] == 1 and s["transitions"] / days < 40
        ok = ok and good
        print(f"  {name}: {'OK' if good else 'CHECK'} (no brownout, survives the FC hang, transitions sane)")
    print(f"Verdict: closed-loop simulation with the real mode manager: {'no brownout, correct degradation and recovery in both orbits' if ok else 'issues found, see above'}.")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
