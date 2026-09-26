"""Ginkgo 12U parametric CAD assembly (build123d / OpenCascade).

Usage: python mechanical/ginkgo_cad.py
Needs mechanical/out/placement.json (run pack.py first; this script runs it if missing).

Builds the frame (rails, walls, plates with windows, cross bulkheads, spine), every placed module,
the solar wings (stowed and deployed) and a few external features; verifies interference,
envelope/protrusion, thruster plume clearance; computes centre of mass and inertia; exports
STEP + STL (stowed, deployed, cutaway) and PNG renders into mechanical/out/.
"""
import json
import math
import os
import sys
import tomllib

from build123d import Align, Box, Compound, Cylinder, Pos, export_stl, export_step

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
OUT = os.path.join(HERE, "out")
MIN3 = (Align.MIN, Align.MIN, Align.MIN)
CTR = (Align.CENTER, Align.CENTER, Align.MIN)

COL_COLOR = {1: (90, 140, 240), 2: (240, 160, 75), 3: (85, 185, 105), 4: (215, 85, 80)}
FRAME_COLOR = (172, 178, 190)
WING_COLOR = (55, 90, 215)
EXT_COLOR = (230, 205, 80)
SIGN = {1: (1, 1), 2: (-1, 1), 3: (-1, -1), 4: (1, -1)}


def box(x0, y0, z0, x1, y1, z1):
    return Pos(x0, y0, z0) * Box(x1 - x0, y1 - y0, z1 - z0, align=MIN3)


def load():
    geo = tomllib.load(open(os.path.join(ROOT, "configs", "12u_geometry.toml"), "rb"))
    cfg = tomllib.load(open(os.path.join(ROOT, "configs", "12u_science.toml"), "rb"))
    pj = os.path.join(OUT, "placement.json")
    if not os.path.exists(pj):
        sys.path.insert(0, HERE)
        import pack
        os.chdir(ROOT)
        pack.build("configs/12u_science.toml", "configs/12u_layout.toml", "configs/12u_geometry.toml", quiet=True)
    return geo, cfg, json.load(open(pj))


def build_frame(geo, placed):
    fr = geo["frame"]
    ox, oy, oz = fr["outer"]
    hx, hy = ox / 2, oy / 2
    w, r, cr = fr["wall"], fr["rail"], fr["cross"]
    parts = []

    def add(name, shape, color=FRAME_COLOR, kind="frame"):
        shape.label = name
        parts.append({"name": name, "shape": shape, "color": color, "kind": kind})

    for sx in (1, -1):
        for sy in (1, -1):
            add(f"Rail {sx:+d}{sy:+d}", box(sx * hx - (r if sx > 0 else 0) if False else min(sx * hx, sx * (hx - r)),
                                          min(sy * hy, sy * (hy - r)), 0,
                                          max(sx * hx, sx * (hx - r)), max(sy * hy, sy * (hy - r)), oz))
    # side walls between the rails
    add("Wall +X", box(hx - w, -hy + r, w, hx, hy - r, oz - w))
    add("Wall -X", box(-hx, -hy + r, w, -hx + w, hy - r, oz - w))
    add("Wall +Y", box(-hx + r, hy - w, w, hx - r, hy, oz - w))
    add("Wall -Y", box(-hx + r, -hy, w, hx - r, -hy + w, oz - w))

    # nadir / zenith plates with corner cut-outs for the rails and windows
    def plate(z0, z1, name, cuts):
        p = box(-hx + r, -hy + r, z0, hx - r, hy - r, z1)
        for sx in (1, -1):
            p = p + box(min(sx * (hx - r), sx * hx), -hy + r, z0, max(sx * (hx - r), sx * hx), hy - r, z1) if False else p
        p = p + box(-hx, -hy + r, z0, hx, hy - r, z1) + box(-hx + r, -hy, z0, hx - r, hy, z1)
        for c in cuts:
            p = p - c
        add(name, p)

    by_name = {m["name"]: m for m in placed}

    def find(prefix):
        return next((m for m in placed if m["name"].startswith(prefix)), None)

    nadir_cuts, zenith_cuts, feats = [], [], []
    tel = find("Payload E: telescope")
    if tel:
        cx, cy = (tel["min"][0] + tel["max"][0]) / 2, (tel["min"][1] + tel["max"][1]) / 2
        nadir_cuts.append(Pos(cx, cy, -1) * Cylinder(45.0, w + 2, align=CTR))
    for pre, s in (("Payload F: wide-field", 34), ("Payload G: thermal IR", 26), ("EO: lightning", 20)):
        m = find(pre)
        if m:
            cx, cy = (m["min"][0] + m["max"][0]) / 2, (m["min"][1] + m["max"][1]) / 2
            nadir_cuts.append(box(cx - s / 2, cy - s / 2, -1, cx + s / 2, cy + s / 2, w + 1))
    st = find("Bus: star tracker")
    if st:
        cx, cy = (st["min"][0] + st["max"][0]) / 2, (st["min"][1] + st["max"][1]) / 2
        zenith_cuts.append(box(cx - 22, cy - 22, oz - w - 1, cx + 22, cy + 22, oz + 1))
    if find("Payload H: dual-frequency GNSS"):
        cx, cy = -70.0, -70.0                     # GNSS patch (40 x 40), cabled to its receiver
        feats.append(("GNSS patch antenna", box(cx - 20, cy - 20, oz, cx + 20, cy + 20, oz + 4)))
    bm = find("SCI: deployable magnetometer boom")
    if bm:
        cx, cy = (bm["min"][0] + bm["max"][0]) / 2, (bm["min"][1] + bm["max"][1]) / 2
        zenith_cuts.append(box(cx - 16, cy - 16, oz - w - 1, cx + 16, cy + 16, oz + 1))
    if find("S-band transceiver (TX)"):
        cx, cy = 60.0, -60.0                      # S-band patch (60 x 60)
        feats.append(("S-band patch antenna", box(cx - 30, cy - 30, oz, cx + 30, cy + 30, oz + 4)))
    plate(0, w, "Nadir plate", nadir_cuts)
    plate(oz - w, oz, "Zenith plate", zenith_cuts)
    for nme, shp in feats:
        add(nme, shp, EXT_COLOR, "external")

    # cross bulkheads and spine (bulkheads are cut where the spine tube passes)
    ih = hx - w
    zi0, zi1 = w, oz - w
    sp = fr["spine"]
    spine_outer = box(-sp / 2, -sp / 2, zi0, sp / 2, sp / 2, zi1)
    spine_inner = box(-sp / 2 + 2, -sp / 2 + 2, zi0 - 1, sp / 2 - 2, sp / 2 - 2, zi1 + 1)
    add("Spine tube", spine_outer - spine_inner)
    add("Bulkhead X", box(-cr / 2, -ih, zi0, cr / 2, ih, zi1) - spine_outer)
    add("Bulkhead Y+", box(cr / 2, -cr / 2, zi0, ih, cr / 2, zi1) - spine_outer)
    add("Bulkhead Y-", box(-ih, -cr / 2, zi0, -cr / 2, cr / 2, zi1) - spine_outer)

    # thruster nozzle through the trailing (-X) wall
    prop = find("Bus: micro-propulsion")
    plume = None
    if prop:
        cy = (prop["min"][1] + prop["max"][1]) / 2
        cz = (prop["min"][2] + prop["max"][2]) / 2
        cx = (prop["min"][0] + prop["max"][0]) / 2
        nozzle = Pos(-hx + w, cy, cz) * (Cylinder(11, hx - w + cx if False else (cx - (-hx + w)) * 1.0, align=CTR) * 1) if False else None
        noz_len = abs(prop["min"][0] - (-hx + 0.5))
        n = Pos(prop["min"][0], cy, cz) * (Cylinder(9.0, noz_len, align=(Align.CENTER, Align.CENTER, Align.MIN)).rotate(
            __import__("build123d").Axis.Y, -90))
        add("Thruster nozzle", n, EXT_COLOR, "external")
        plume = (-hx, cy, cz)
        # wall hole for the nozzle
        for p in parts:
            if p["name"] == "Wall -X":
                p["shape"] = p["shape"] - (Pos(-hx + w / 2, cy, cz) * (Cylinder(11.0, w + 2, align=CTR).rotate(
                    __import__("build123d").Axis.Y, 90)))
                p["shape"].label = "Wall -X"
    return parts, plume


def build_wings(geo, deployed):
    fr = geo["frame"]
    wg = geo["wings"]
    ox, oy, oz = fr["outer"]
    hx, hy = ox / 2, oy / 2
    pw, pl, pt = wg["panel"]
    n = wg["panels_per_wing"]
    parts = []
    for sgn in (1, -1):                       # wing A on +Y (extends +X), wing B on -Y (extends -X)
        for k in range(n):
            if deployed:
                y0 = sgn * (hy + wg["standoff"])
                xa = sgn * (hx + k * pw)
                xb = sgn * (hx + (k + 1) * pw)
                shp = box(min(xa, xb), min(y0, y0 + sgn * pt), 0, max(xa, xb), max(y0, y0 + sgn * pt), pl)
            else:
                ya = sgn * (hy + k * pt)
                yb = sgn * (hy + (k + 1) * pt)
                shp = box(-hx, min(ya, yb), 0, hx, max(ya, yb), pl)
            name = f"Wing {'A' if sgn > 0 else 'B'} panel {k + 1}"
            shp.label = name
            parts.append({"name": name, "shape": shp, "color": WING_COLOR, "kind": "wing"})
    return parts


def build_modules(placed):
    parts = []
    for m in placed:
        x0, y0, z0 = m["min"]
        x1, y1, z1 = m["max"]
        if m["shape"] == "cyl":
            d = x1 - x0
            shp = Pos((x0 + x1) / 2, (y0 + y1) / 2, z0) * Cylinder(d / 2, z1 - z0, align=CTR)
        else:
            shp = box(x0, y0, z0, x1, y1, z1)
            if m.get("notched"):
                sx, sy = SIGN[m["col"]]
                cx = sx * 1.5
                cy = sy * 1.5
                nch = 20.0
                nx0, nx1 = sorted((cx, cx + sx * nch))
                ny0, ny1 = sorted((cy, cy + sy * nch))
                shp = shp - box(nx0, ny0, z0 - 1, nx1, ny1, z1 + 1)
        shp.label = m["name"][:60]
        parts.append({"name": m["name"], "shape": shp, "color": COL_COLOR[m["col"]], "kind": "module", "meta": m})
    return parts


def interference(frame_parts, module_parts):
    """Pairwise boolean intersection volumes (with bounding-box prefilter)."""
    issues = []

    def bb(p):
        b = p["shape"].bounding_box()
        return (b.min.X, b.min.Y, b.min.Z, b.max.X, b.max.Y, b.max.Z)

    def overlap(a, b, tol=0.01):
        return all(a[i] < b[i + 3] - tol and b[i] < a[i + 3] - tol for i in range(3))

    boxes = [(p, bb(p)) for p in module_parts]
    frame_boxes = [(p, bb(p)) for p in frame_parts if p["kind"] == "frame"]
    checks = 0
    for i, (a, ba) in enumerate(boxes):
        for b, bb_ in boxes[i + 1:]:
            if overlap(ba, bb_):
                checks += 1
                vol = (a["shape"] & b["shape"]).volume
                if vol > 1.0:
                    issues.append((a["name"][:40], b["name"][:40], vol))
        for f, bf in frame_boxes:
            if overlap(ba, bf):
                checks += 1
                vol = (a["shape"] & f["shape"]).volume
                if vol > 1.0:
                    issues.append((a["name"][:40], f["name"], vol))
    return issues, checks


def mass_props(placed, cfg, wings_deployed, geo):
    """Centre of mass and inertia (kg m^2) about the CoM; every module is a homogeneous box."""
    fr = geo["frame"]
    ox, oy, oz = fr["outer"]
    body = []   # (m, cx, cy, cz, dx, dy, dz)
    placed_mass = 0.0
    for m in placed:
        dx, dy, dz = m["max"][0] - m["min"][0], m["max"][1] - m["min"][1], m["max"][2] - m["min"][2]
        body.append((m["mass_kg"], (m["min"][0] + m["max"][0]) / 2, (m["min"][1] + m["max"][1]) / 2,
                     (m["min"][2] + m["max"][2]) / 2, dx, dy, dz))
        placed_mass += m["mass_kg"]
    names = {m["name"] for m in placed}
    rest = [m for m in cfg["module"] if m["name"] not in names]
    wing_mass = 0.0
    for m in rest:
        if m["name"].startswith("Solar panels + wings"):
            wing_mass += m["mass_kg"]
        elif m["name"].startswith("Structure"):
            body.append((m["mass_kg"], 0.0, 0.0, oz / 2, ox, oy, oz))
        elif m["name"].startswith("Harness"):
            body.append((m["mass_kg"], 0.0, 0.0, oz / 2, fr["spine"], fr["spine"], oz))
        else:   # skin-mounted items: treat as distributed around the body centre
            body.append((m["mass_kg"], 0.0, 0.0, oz / 2, ox, oy, oz))
    wg = geo["wings"]
    pw, pl, pt = wg["panel"]
    hx, hy = ox / 2, oy / 2
    # body cells are part of the 1.1 kg: 40 % body skin, 60 % wing panels
    body.append((wing_mass * 0.4, 0.0, 0.0, oz / 2, ox, oy, oz))
    each = wing_mass * 0.6 / (2 * wg["panels_per_wing"])
    for sgn in (1, -1):
        for k in range(wg["panels_per_wing"]):
            if wings_deployed:
                body.append((each, sgn * (hx + (k + 0.5) * pw), sgn * (hy + wg["standoff"]), oz / 2, pw, pt, pl))
            else:
                body.append((each, 0.0, sgn * (hy + (k + 0.5) * pt), oz / 2, ox, pt, pl))
    M = sum(b[0] for b in body)
    cx = sum(b[0] * b[1] for b in body) / M
    cy = sum(b[0] * b[2] for b in body) / M
    cz = sum(b[0] * b[3] for b in body) / M
    I = [0.0, 0.0, 0.0]
    for m, x, y, z, dx, dy, dz in body:
        x, y, z, dx, dy, dz = [t / 1000.0 for t in (x - cx, y - cy, z - cz, dx, dy, dz)]
        I[0] += m * ((dy * dy + dz * dz) / 12 + y * y + z * z)
        I[1] += m * ((dx * dx + dz * dz) / 12 + x * x + z * z)
        I[2] += m * ((dx * dx + dy * dy) / 12 + x * x + y * y)
    return M, (cx - 0.0, cy - 0.0, cz - oz / 2), I


def plume_check(plume, geo, half_angle_deg):
    if not plume:
        return None
    fr = geo["frame"]
    hy = fr["outer"][1] / 2
    px, py, pz = plume                       # nozzle exit on the -X face, exhaust toward -X
    wg = geo["wings"]
    pw, pl, pt = wg["panel"]
    hx = fr["outer"][0] / 2
    yplane = -(hy + wg["standoff"])          # wing B plane (extends toward -X)
    t = math.tan(math.radians(half_angle_deg))
    # plume edge reaches the wing plane at distance d from the exit
    d = (py - yplane) / t if py > yplane else None
    x_hit = px - d if d else None
    wing_end = -(hx + wg["panels_per_wing"] * pw)
    if d is None:
        return "no impingement"
    hit = x_hit >= wing_end            # x_hit is negative; wing spans px .. wing_end
    return f"plume edge meets wing B plane at x = {x_hit:.0f} mm (wing ends at {wing_end:.0f} mm): " \
           + ("IMPINGES on wing B" if hit else "clear")


def to_mesh(shape, tol=0.7):
    verts, tris = shape.tessellate(tol, 0.5)
    return [(v.X, v.Y, v.Z) for v in verts], tris


def render(named, path, az=38, el=28, size=(1800, 1300), title="", zoom=1.0):
    """Orthographic z-buffer rasteriser (numpy) with flat shading, part outlines and supersampling."""
    import numpy as np
    from PIL import Image, ImageDraw, ImageFont
    S = 2
    W, H = size[0] * S, size[1] * S
    ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))

    V, T, C, IDS = [], [], [], []
    off = 0
    for pid, (mesh, color, _) in enumerate(named):
        verts, tris = mesh
        V.append(np.asarray(verts, dtype=np.float64))
        T.append(np.asarray(tris, dtype=np.int64) + off)
        C.append(np.tile(np.asarray(color, dtype=np.float64), (len(tris), 1)))
        IDS.append(np.full(len(tris), pid + 1, dtype=np.int32))
        off += len(verts)
    V = np.vstack(V)
    T = np.vstack(T)
    C = np.vstack(C)
    IDS = np.concatenate(IDS)

    xr = V[:, 0] * ca - V[:, 1] * sa
    yr = V[:, 0] * sa + V[:, 1] * ca
    sx = xr
    sy = -(V[:, 2] * ce + yr * se)
    dz = V[:, 2] * se - yr * ce                    # bigger = nearer to the camera
    sc = min(W * 0.90 / (sx.max() - sx.min()), H * 0.88 / (sy.max() - sy.min())) * zoom
    px = (sx - (sx.max() + sx.min()) / 2) * sc + W / 2
    py = (sy - (sy.max() + sy.min()) / 2) * sc + H / 2 + 14 * S

    # face normals and flat light
    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    view = np.array([-sa * ce * -1 * 0 + (-(-sa) * ce) * 0, 0, 0])
    # world-space direction to the camera
    to_cam = np.array([sa * ce * -1 * -1 * 0, 0, 0])
    to_cam = np.array([-(-sa) * 0, 0, 0])
    cam = np.array([sa * -ce * -1, -ca * ce * -1, se])
    cam = np.array([-sa * ce * -1, ca * ce * -1, se])
    # camera looks along +yr; direction from scene to camera in world coordinates:
    cam = np.array([sa * ce, -ca * ce, se])
    cam = cam / np.linalg.norm(cam)
    flip = (n @ cam) < 0
    n[flip] *= -1
    L = np.array([0.55, -0.35, 0.75])
    L /= np.linalg.norm(L)
    light = 0.30 + 0.45 * np.clip(n @ L, 0, 1) + 0.30 * np.clip(n @ cam, 0, 1)
    col = np.clip(C * light[:, None], 0, 255)

    zbuf = np.full((H, W), -1e18)
    idb = np.zeros((H, W), dtype=np.int32)
    img = np.zeros((H, W, 3), dtype=np.float64)
    img[:] = np.array([15, 20, 32]) + np.linspace(0, 14, H)[:, None, None]
    for i in range(len(T)):
        i0, i1, i2 = T[i]
        x0, y0, x1, y1, x2, y2 = px[i0], py[i0], px[i1], py[i1], px[i2], py[i2]
        xmin, xmax = int(max(0, math.floor(min(x0, x1, x2)))), int(min(W - 1, math.ceil(max(x0, x1, x2))))
        ymin, ymax = int(max(0, math.floor(min(y0, y1, y2)))), int(min(H - 1, math.ceil(max(y0, y1, y2))))
        if xmin > xmax or ymin > ymax:
            continue
        det = (y1 - y2) * (x0 - x2) + (x2 - x1) * (y0 - y2)
        if abs(det) < 1e-9:
            continue
        gx, gy = np.meshgrid(np.arange(xmin, xmax + 1) + 0.5, np.arange(ymin, ymax + 1) + 0.5)
        l0 = ((y1 - y2) * (gx - x2) + (x2 - x1) * (gy - y2)) / det
        l1 = ((y2 - y0) * (gx - x2) + (x0 - x2) * (gy - y2)) / det
        l2 = 1 - l0 - l1
        inside = (l0 >= -1e-6) & (l1 >= -1e-6) & (l2 >= -1e-6)
        if not inside.any():
            continue
        z = l0 * dz[i0] + l1 * dz[i1] + l2 * dz[i2]
        sub = zbuf[ymin:ymax + 1, xmin:xmax + 1]
        upd = inside & (z > sub)
        if not upd.any():
            continue
        sub[upd] = z[upd]
        idb[ymin:ymax + 1, xmin:xmax + 1][upd] = IDS[i]
        img[ymin:ymax + 1, xmin:xmax + 1][upd] = col[i]

    # part outlines and depth discontinuities
    edge = np.zeros((H, W), dtype=bool)
    edge[:, :-1] |= idb[:, :-1] != idb[:, 1:]
    edge[:-1, :] |= idb[:-1, :] != idb[1:, :]
    zc = np.where(zbuf > -1e17, zbuf, np.nan)
    gz = np.abs(np.diff(zc, axis=1, prepend=zc[:, :1])) + np.abs(np.diff(zc, axis=0, prepend=zc[:1, :]))
    edge |= np.nan_to_num(gz, nan=0) > 6.0
    img[edge] *= 0.30
    out = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8)).resize(size, Image.LANCZOS)
    d = ImageDraw.Draw(out)
    try:
        font = ImageFont.load_default(size=22)
    except Exception:
        font = ImageFont.load_default()
    d.text((24, 18), title, fill=(210, 220, 235), font=font)
    out.save(path)


def main():
    os.makedirs(OUT, exist_ok=True)
    geo, cfg, pl = load()
    placed = pl["placed"]
    print(f"Modules placed: {len(placed)}; failed: {len(pl['failed'])}; relocated: {len(pl.get('relocated', []))}")

    frame, plume = build_frame(geo, placed)
    mods = build_modules(placed)
    wings_st = build_wings(geo, False)
    wings_dp = build_wings(geo, True)

    print("\n== Interference check (boolean intersections) ==")
    issues, checks = interference(frame, mods)
    print(f"{checks} overlapping bounding-box pairs tested with exact booleans; {len(issues)} interferences")
    for a, b, v in issues[:15]:
        print(f"  {a} <-> {b}: {v:.0f} mm3")

    fr = geo["frame"]
    wg = geo["wings"]
    ox, oy, oz = fr["outer"]
    ext_parts = [p for p in frame if p["kind"] == "external"]
    ext_overlaps = 0
    for a_i, a_ in enumerate(ext_parts):
        for b_ in ext_parts[a_i + 1:]:
            if (a_["shape"] & b_["shape"]).volume > 1.0:
                ext_overlaps += 1
                print(f"  external overlap: {a_['name']} <-> {b_['name']}")
    print(f"External features overlap check: {ext_overlaps} overlaps")
    print("\n== Envelope and protrusion ==")
    stack = wg["panels_per_wing"] * wg["panel"][2]
    lim = fr["protrusion_limit"]
    print(f"Stowed wing stack thickness {stack:.2f} mm vs allowed protrusion {lim:.2f} mm "
          f"-> {'OK' if stack <= lim + 1e-9 else 'FAIL'}")
    ext = [p for p in frame if p["kind"] == "external"]
    for p in ext:
        b = p["shape"].bounding_box()
        prot = max(b.max.Z - oz, 0, -b.min.X - ox / 2, b.max.X - ox / 2)
        print(f"External {p['name']}: protrusion {prot:.1f} mm -> {'OK' if prot <= lim else 'CHECK'}")
    print(f"Deployed span (x): {2 * (ox / 2 + wg['panels_per_wing'] * wg['panel'][0]):.0f} mm, "
          f"wing area per wing {wg['panels_per_wing'] * wg['panel'][0] * wg['panel'][1] / 1e6:.3f} m2")

    print("\n== Thruster plume vs wings (15 deg half-angle) ==")
    print(plume_check(plume, geo, 15.0))

    print("\n== Mass properties (module boxes, uniform density) ==")
    for dep, lab in ((False, "stowed"), (True, "deployed")):
        M, (cx, cy, cz), I = mass_props(placed, cfg, dep, geo)
        print(f"{lab:9s} mass {M:.2f} kg, CoM offset ({cx:+.1f}, {cy:+.1f}, {cz:+.1f}) mm, "
              f"I = ({I[0]:.3f}, {I[1]:.3f}, {I[2]:.3f}) kg m2")

    def comp(parts, name):
        c = Compound(children=[p["shape"] for p in parts], label=name)
        return c

    # colours for STEP
    from build123d import Color
    for p in frame + mods + wings_st + wings_dp:
        r, g, b = p["color"]
        p["shape"].color = Color(r / 255, g / 255, b / 255)

    # a shape can belong to only one compound: build, export, then release before the next assembly
    for tag, wings in (("stowed", wings_st), ("deployed", wings_dp)):
        assy = comp(frame + mods + wings, f"Ginkgo 12U {tag}")
        export_step(assy, os.path.join(OUT, f"ginkgo_12u_{tag}.step"))
        export_stl(assy, os.path.join(OUT, f"ginkgo_12u_{tag}.stl"))
        for p in frame + mods + wings:
            p["shape"].parent = None
        assy = None
    print("\nExported STEP and STL (stowed, deployed) to mechanical/out/")

    def meshes(parts, hide=()):
        out = []
        for p in parts:
            if any(p["name"].startswith(h) for h in hide):
                continue
            out.append((to_mesh(p["shape"]), p["color"], 1.0))
        return out

    render(meshes(frame + mods + wings_st), os.path.join(OUT, "render_stowed.png"),
           title="Ginkgo 12U: stowed (launch configuration)")
    render(meshes(frame + mods + wings_dp), os.path.join(OUT, "render_deployed.png"), az=30, el=24,
           title="Ginkgo 12U: wings deployed")
    render(meshes(frame + mods, hide=("Wall", "Nadir plate", "Zenith plate")), os.path.join(OUT, "render_interior.png"),
           az=35, el=26, title="Ginkgo 12U: interior (walls hidden; Q1 blue, Q2 orange, Q3 green, Q4 red)")
    render(meshes(frame + mods, hide=("Wall +X", "Wall +Y", "Zenith plate")), os.path.join(OUT, "render_cutaway.png"),
           az=215, el=28, title="Ginkgo 12U: cutaway from the trailing side")
    render(meshes(frame + mods + wings_st), os.path.join(OUT, "render_nadir.png"), az=35, el=-50,
           title="Ginkgo 12U: nadir end (telescope aperture, camera windows), wings stowed")
    print("Rendered PNG views to mechanical/out/")

    # bill of materials
    import csv
    with open(os.path.join(OUT, "bom_geometry.csv"), "w", newline="") as f:
        wr = csv.writer(f)
        wr.writerow(["module", "column", "mass_kg", "dx", "dy", "dz", "x_min", "y_min", "z_min", "x_max", "y_max", "z_max"])
        for m in placed:
            dx, dy, dz = (m["max"][i] - m["min"][i] for i in range(3))
            wr.writerow([m["name"], f"Q{m['col']}", m["mass_kg"], round(dx, 1), round(dy, 1), round(dz, 1),
                         *[round(v, 1) for v in m["min"]], *[round(v, 1) for v in m["max"]]])
    print("Wrote bom_geometry.csv")


if __name__ == "__main__":
    main()
