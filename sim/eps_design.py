"""First-order electrical design of the power system (strings, MPPT channels, battery pack, limits).

Usage: python sim/eps_design.py
Inputs are typical values for a triple-junction cell and a LiFePO4 26650 cell; replace with datasheet values.
"""
import math
import tomllib
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
cfg = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
geo = tomllib.load(open(os.path.join(ROOT, "configs", "12u_geometry.toml"), "rb"))

# ---- solar cell (typical 30 cm2 triple-junction, beginning of life, AM0, 28 C) ----
CELL_AREA_CM2 = 30.2
CELL_W, CELL_L = 40.0, 80.0          # mm
VMP, IMP, VOC, ISC = 2.41, 0.50, 2.70, 0.53
TC_VOC = -0.0062                     # V/K per cell
T_HOT, T_COLD = 80.0, -100.0         # C, eclipse exit cell temperature
TC_VMP = -0.0065
MPPT_VIN_MAX = 40.0                  # V, typical spacecraft-grade buck input limit
MPPT_VIN_MIN = 8.0
BUS_MIN, BUS_MAX = 5.0, 7.3          # V, 2S LiFePO4

panel_w, panel_l, panel_t = geo["wings"]["panel"]
cols = int((panel_w - 6) // CELL_W)
rows = int((panel_l - 6) // CELL_L)
cells_panel = cols * rows
print(f"Wing panel {panel_w:.0f} x {panel_l:.0f} mm carries {cols} x {rows} = {cells_panel} cells "
      f"({cells_panel * CELL_AREA_CM2 / (panel_w * panel_l / 100) * 100:.0f} % area coverage)")

series = 10
parallel = cells_panel // series
v_mp_hot = series * (VMP + TC_VMP * (T_HOT - 28))
v_oc_cold = series * (VOC + TC_VOC * (T_COLD - 28))
print(f"String: {series}s x {parallel}p per panel -> Vmp {series * VMP:.1f} V (hot {v_mp_hot:.1f} V), "
      f"Voc cold {v_oc_cold:.1f} V, Imp {parallel * IMP:.2f} A, Pmax {series * VMP * parallel * IMP:.1f} W")
assert v_oc_cold < MPPT_VIN_MAX, "cold Voc exceeds MPPT input limit"
assert v_mp_hot > MPPT_VIN_MIN, "hot Vmp below MPPT input minimum"
print(f"  cold Voc {v_oc_cold:.1f} V < {MPPT_VIN_MAX:.0f} V input limit: OK; hot Vmp {v_mp_hot:.1f} V > {MPPT_VIN_MIN:.0f} V: OK")

panels = geo["wings"]["count"] * geo["wings"]["panels_per_wing"]
p_panel = series * VMP * parallel * IMP
print(f"Wings: {panels} panels x {p_panel:.0f} W = {panels * p_panel:.0f} W peak (AM0, BOL, normal incidence)")

# ---- MPPT channels ----
print()
print("MPPT topology: one buck MPPT channel per panel (3 per wing); EPS-A takes wing A, EPS-B takes wing B;")
print("survival pack C has its own charger on a dedicated body string.")
i_bus_panel = p_panel * 0.95 / BUS_MIN
print(f"Per channel: {p_panel:.0f} W in, up to {i_bus_panel:.1f} A into a {BUS_MIN:.1f} V bus at 95 % efficiency")
print(f"Per EPS: 3 channels = {3 * p_panel:.0f} W peak, {3 * i_bus_panel:.1f} A at the lowest bus voltage")

# ---- battery pack ----
CELL_V, CELL_AH, CELL_G = 3.2, 3.3, 85.0          # 26650 LiFePO4
target_wh = 30.0
cells_s = 2
cells_p = math.ceil(target_wh / (cells_s * CELL_V * CELL_AH))
pack_wh = cells_s * cells_p * CELL_V * CELL_AH
pack_g = cells_s * cells_p * CELL_G
print()
print(f"Pack: {cells_s}S{cells_p}P 26650 LiFePO4 = {pack_wh:.0f} Wh, {cells_s * cells_p} cells, {pack_g:.0f} g cells only "
      f"(pack incl. BMS and holder about {pack_g + 100:.0f} g; config allows "
      f"{[m['mass_kg'] for m in cfg['module'] if m['name'].startswith('LiFePO4 pack A')][0] * 1000:.0f} g)")
print(f"Voltage range {cells_s * 2.5:.1f}-{cells_s * 3.65:.1f} V (bus limits {BUS_MIN}-{BUS_MAX} V)")
ch_max_a = 0.5 * cells_p * CELL_AH                # C/2
print(f"Charge limit C/2 = {ch_max_a:.1f} A = {ch_max_a * 6.4:.0f} W per pack, two packs {2 * ch_max_a * 6.4:.0f} W")

load = sum(m["power_w"] * m["duty"] for m in cfg["module"])
gen = 2 * 3 * p_panel
print()
print(f"Average load {load:.1f} W; peak wing power {gen:.0f} W; chargeable {2 * ch_max_a * 6.4:.0f} W -> "
      f"excess must be shed: MPPT channels back off (peak-power tracking is not required when loads + charge are lower).")
print(f"Eclipse energy at full loads (35 min): {load * 35 / 60:.1f} Wh of {2 * pack_wh * cfg['battery']['max_depth_of_discharge']:.0f} Wh usable (planning depth of discharge)")

# ---- burn mode ----
burn = sum(m['power_w'] * m['duty'] for m in cfg['module'] if m.get('burn_mode')) or 53.1  # burn-mode load, see budget.py scenario
print(f"Burn mode load {burn:.0f} W: wings supply up to {gen:.0f} W peak; needs sun-biased attitude (see docs/propulsion.md)")
print()
print("Survival string: 8 body cells (4s2p, ~9.6 V, 1.0 A) -> charger for pack C (3.2 V single cell, 1.5 Ah) and direct feed for")
print("the supervisor and beacon when pack C is dead (sun-only mode).")
