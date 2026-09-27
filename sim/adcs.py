"""ADCS sizing: disturbance torques, wheel and magnetorquer sizing, slew, burn torque and imaging smear.

Usage: python sim/adcs.py
Inertias come from the CAD model (mechanical/wollemi_cad.py, kg m^2). All disturbance models are first-order
worst-case estimates; a full simulation (flexible modes, wheel micro-vibration, sensor noise) is still to do.
"""
import math

MU = 3.986004418e14
RE = 6378.137e3
ALT = 700e3
R = RE + ALT
N = math.sqrt(MU / R ** 3)                     # orbital rate (rad/s)
V = math.sqrt(MU / R)

# inertia (kg m^2) about the principal axes: stowed and wings deployed (from the CAD mass properties)
I_STOWED = (0.190, 0.183, 0.114)
I_DEPLOYED = (0.191, 0.341, 0.272)

print(f"Orbit {ALT / 1e3:.0f} km: rate {N * 1e3:.3f} mrad/s, period {2 * math.pi / N / 60:.1f} min, speed {V / 1e3:.2f} km/s")
print()

# ---- disturbance torques (worst case, deployed configuration) ----
Ix, Iy, Iz = I_DEPLOYED
gg = 1.5 * N ** 2 * max(abs(Ix - Iz), abs(Iy - Iz), abs(Ix - Iy))          # 3/2 n^2 dI (sin 2*theta = 1)
print("Disturbance torques (N m), deployed configuration")
print(f"  gravity gradient          {gg:9.2e}")

rho = {"mean": 2e-14, "solar max": 1.0e-13}
A_AERO = 0.9          # m^2 projected area with both wings broadside
CD = 2.2
OFFSET_AERO = 0.05    # m, centre of pressure to centre of mass
for k, r_ in rho.items():
    f = 0.5 * r_ * V ** 2 * CD * A_AERO
    print(f"  aerodynamic ({k:9s})   {f * OFFSET_AERO:9.2e}   (force {f:.1e} N)")

P_SRP = 4.56e-6 * 1.3
A_SRP = 0.9
OFFSET_SRP = 0.10
srp = P_SRP * A_SRP * OFFSET_SRP
print(f"  solar radiation pressure  {srp:9.2e}")

M_RES = 0.1           # A m^2, residual magnetic dipole after compensation (requirement)
B = 3.0e-5            # T at 700 km
mag = M_RES * B
print(f"  residual magnetic ({M_RES} A m^2) {mag:9.2e}   <- dominant; the magnetometer cleanliness rules matter")

# thruster: 1.1 mN nominal, misalignment offset of the thrust line from the centre of mass
F_THR = 1.1e-3
for off_mm in (2, 5, 10):
    print(f"  electric thruster, {off_mm:2d} mm offset {F_THR * off_mm * 1e-3:9.2e}")
print()

# ---- momentum accumulation per orbit and desaturation ----
T_ORB = 2 * math.pi / N
sec = (gg + srp) * 0.2 * T_ORB
print(f"Secular momentum per orbit (20 % of worst gg+SRP, conservative): {sec * 1e3:.2f} mN m s; cyclic parts average out")
burn_h = 3600.0
for off_mm in (2, 5, 10):
    print(f"Burn, {off_mm:2d} mm offset: {F_THR * off_mm * 1e-3 * burn_h * 1e3:6.1f} mN m s accumulated per hour of thrusting "
          f"(needs continuous dumping or a gimbal)")

# ---- magnetorquer dumping ----
for dip in (0.5, 1.0, 2.0):
    T = dip * B
    print(f"Magnetorquer {dip:.1f} A m^2: torque up to {T * 1e6:6.1f} uN m (perpendicular to B only, about {T * 0.6 * 1e6:5.1f} uN m average)")
print()

# ---- slew ----
print("Rest-to-rest slew (bang-bang) required torque and momentum, worst axis of the deployed vehicle")
for theta_deg, t_s in ((30, 60), (60, 90), (90, 120), (90, 300)):
    th = math.radians(theta_deg)
    a = 4 * th / t_s ** 2
    w = 2 * th / t_s
    imax = max(I_DEPLOYED)
    print(f"  {theta_deg:3d} deg in {t_s:3d} s: torque {imax * a * 1e3:6.3f} mN m, momentum {imax * w * 1e3:6.2f} mN m s, rate {w * 1e3:5.1f} mrad/s")
print()

# ---- wheels ----
WHEEL_H, WHEEL_T = 30e-3, 3e-3       # candidate: 30 mN m s momentum, 3 mN m torque each
print(f"Candidate wheels: 3 x (momentum {WHEEL_H * 1e3:.0f} mN m s, torque {WHEEL_T * 1e3:.0f} mN m)")
print(f"  90 deg in 120 s needs {max(I_DEPLOYED) * 4 * math.radians(90) / 120 ** 2 * 1e3:.2f} mN m and "
      f"{max(I_DEPLOYED) * 2 * math.radians(90) / 120 * 1e3:.1f} mN m s -> margin torque x{WHEEL_T / (max(I_DEPLOYED) * 4 * math.radians(90) / 120 ** 2):.0f}, "
      f"momentum x{WHEEL_H / (max(I_DEPLOYED) * 2 * math.radians(90) / 120):.1f}")
print(f"  a 5 mm thrust offset saturates one wheel in {WHEEL_H / (F_THR * 5e-3) / 60:.0f} min of continuous thrust "
      f"without dumping; magnetorquer torque ({1.0 * B * 0.6 * 1e6:.0f} uN m) exceeds the burn disturbance ({F_THR * 5e-3 * 1e6:.1f} uN m): dumping is feasible")
print()

# ---- telescope imaging ----
F_LEN = 0.45                           # m, focal length of the 85 mm f/5.3 Cassegrain
PIX = 3.45e-6
ifov = PIX / F_LEN
gsd = ALT * ifov
line_rate = V * (RE / R) / gsd         # ground speed / GSD
t_exp = 1.0 / line_rate
print(f"Telescope: IFOV {ifov * 1e6:.2f} urad, ground sample {gsd:.1f} m, ground speed {V * RE / R / 1e3:.2f} km/s, "
      f"line time {t_exp * 1e3:.2f} ms")
print(f"  smear budget 0.3 pixel over a 1 ms exposure: rate error <= {0.3 * ifov / 1e-3 * 1e3:.2f} mrad/s (nadir tracking rate is {N * 1e3:.2f} mrad/s)")
print(f"  jitter budget: rms angle <= {0.3 * ifov * 1e6:.1f} urad = {math.degrees(0.3 * ifov) * 3600:.2f} arcsec above ~1 kHz")
# rigid-body jitter from wheel disturbance torque at frequency f
for td_uNm, f in ((100, 100), (100, 300), (30, 30)):
    th = td_uNm * 1e-6 / (min(I_STOWED) * (2 * math.pi * f) ** 2)
    print(f"  rigid-body jitter from {td_uNm} uN m wheel disturbance at {f} Hz: {th * 1e6:8.4f} urad rms-equivalent (well below the budget)")
print("  the real risk is structural resonances and gyro/star-tracker noise, not rigid-body wheel torque:")
print("  keep the wheels on isolators and fly a fine-pointing test of the telescope tube modes (see verification plan).")
print()

# ---- knowledge ----
ST_ERR_ARCSEC = 5.0
err = math.radians(ST_ERR_ARCSEC / 3600) * ALT
print(f"Star tracker {ST_ERR_ARCSEC} arcsec (1 sigma): {err:.0f} m on the ground at nadir; image registration removes it, "
      f"direct geolocation of a 5 m pixel needs ~{math.degrees(ifov) * 3600:.1f} arcsec")
print()
print("Verdict: wheel capacity (30 mN m s, 3 mN m) is ample for slews; the dominant issues are residual magnetic torque,")
print("thruster misalignment during burns (needs continuous magnetorquer dumping and CoM control) and telescope vibration modes.")
