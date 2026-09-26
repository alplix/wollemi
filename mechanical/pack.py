"""Geometric packing of the 12U modules (numpy voxel grid).

Every module's bounding box is placed inside the column and deck range assigned in
configs/12u_layout.toml. Sizes are rounded up to the voxel size (built-in clearance). The
spine corner and the outer rail corner of every column are blocked.

Usage: python mechanical/pack.py [science.toml layout.toml geometry.toml]
Writes mechanical/out/placement.json (used by ginkgo_cad.py).
"""
import itertools
import json
import math
import os
import re
import sys
import tomllib

import numpy as np

SIGN = {1: (1, 1), 2: (-1, 1), 3: (-1, -1), 4: (1, -1)}      # ring order Q1..Q4 -> (sx, sy)


def parse_at(at):
    m = re.fullmatch(r"Q(\d)/(\d)(?:-(\d))?", at)
    if not m:
        return None
    d1 = int(m.group(2))
    return int(m.group(1)), d1, int(m.group(3) or d1)


def first_fit(occ, dims, zlo, zhi):
    """Best position for a dims-sized box: entirely free, maximum contact with walls/modules.

    Returns ((x, y, z), contact_fraction) or None. Ties broken toward lower z, y, x.
    """
    nx, ny, nz = occ.shape
    a, b, c = dims
    zhi = min(zhi, nz)
    if a > nx or b > ny or c > zhi - zlo:
        return None
    P = np.pad(occ.astype(np.int32), 1, constant_values=1)         # walls count as contact
    S = np.zeros((P.shape[0] + 1, P.shape[1] + 1, P.shape[2] + 1), dtype=np.int32)
    S[1:, 1:, 1:] = P.cumsum(0).cumsum(1).cumsum(2)

    def box_sum(x0, y0, z0, x1, y1, z1):
        return (S[x1, y1, z1] - S[x0, y1, z1] - S[x1, y0, z1] - S[x1, y1, z0]
                + S[x0, y0, z1] + S[x0, y1, z0] + S[x1, y0, z0] - S[x0, y0, z0])

    X, Y, Z = nx - a + 1, ny - b + 1, zhi - c + 1
    xs = np.arange(X)[:, None, None]
    ys = np.arange(Y)[None, :, None]
    zs = np.arange(Z)[None, None, :]
    px, py, pz = xs + 1, ys + 1, zs + 1                           # padded coordinates of the box origin
    free = box_sum(px, py, pz, px + a, py + b, pz + c) == 0
    free[:, :, :zlo] = False
    if not free.any():
        return None
    contact = (box_sum(px - 1, py, pz, px, py + b, pz + c) + box_sum(px + a, py, pz, px + a + 1, py + b, pz + c)
               + box_sum(px, py - 1, pz, px + a, py, pz + c) + box_sum(px, py + b, pz, px + a, py + b + 1, pz + c)
               + box_sum(px, py, pz - 1, px + a, py + b, pz) + box_sum(px, py, pz + c, px + a, py + b, pz + c + 1))
    area = 2 * (a * b + a * c + b * c)
    score = np.where(free, contact / area - 1e-4 * zs - 1e-6 * ys - 1e-7 * xs, -1e9)
    x, y, z = np.unravel_index(int(np.argmax(score)), score.shape)
    return (int(x), int(y), int(z)), float(contact[x, y, z] / area)


def disk_mask(d_vox):
    r = d_vox / 2.0
    c = (d_vox - 1) / 2.0
    yy, xx = np.mgrid[0:d_vox, 0:d_vox]
    return ((xx - c) ** 2 + (yy - c) ** 2) <= r * r


def cyl_fit(occ, d_vox, h_vox, zlo, zhi, top=False):
    """Lowest z where a vertical cylinder (disk footprint) fits; centre-most (u,v). Returns (u,v,z) of the bbox min."""
    from scipy.signal import correlate
    nx, ny, nz = occ.shape
    zhi = min(zhi, nz)
    m = disk_mask(d_vox).astype(np.float32)
    zs = range(zlo, zhi - h_vox + 1)
    for z in (reversed(zs) if top else zs):
        proj = occ[:, :, z:z + h_vox].any(axis=2).astype(np.float32)
        conf = correlate(proj, m, mode="valid")
        idx = np.argwhere(conf < 0.5)
        if len(idx):
            cu = (nx - d_vox) / 2.0
            k = int(np.argmin((idx[:, 0] - cu) ** 2 + (idx[:, 1] - cu) ** 2))
            return int(idx[k][0]), int(idx[k][1]), z
    return None


def build(cfg_path, lay_path, geo_path, quiet=False):
    cfg = tomllib.load(open(cfg_path, "rb"))
    lay = tomllib.load(open(lay_path, "rb"))
    geo = tomllib.load(open(geo_path, "rb"))
    fr = geo["frame"]
    v = fr["voxel"]
    ox, oy, oz = fr["outer"]
    inner = (ox - 2 * fr["wall"] - fr["cross"]) / 2
    inner_z = oz - 2 * fr["wall"]
    n = int(inner // v)
    nz = int(inner_z // v)
    deck_h = nz / 3
    sp = math.ceil((fr["spine"] / 2 - fr["cross"] / 2) / v)          # spine corner (inner corner)
    rl = math.ceil((fr["rail"] - fr["wall"]) / v)                    # rail corner (outer corner)

    grids = {}
    for q in SIGN:
        g = np.zeros((n, n, nz), dtype=bool)
        g[:sp, :sp, :] = True                    # u,v small = near the spine
        g[n - rl:, n - rl:, :] = True            # u,v large = outer corner (rail)
        grids[q] = g

    # keepout volumes (world coordinates) blocked in every column they touch
    for ko in geo.get("keepout", []):
        (kx0, ky0, kz0), (kx1, ky1, kz1) = ko["min"], ko["max"]
        for q, (sx, sy) in SIGN.items():
            idx = np.arange(n)
            xa = sx * (fr["cross"] / 2 + idx * v)
            xb = sx * (fr["cross"] / 2 + (idx + 1) * v)
            ya = sy * (fr["cross"] / 2 + idx * v)
            yb = sy * (fr["cross"] / 2 + (idx + 1) * v)
            xm = (np.minimum(xa, xb) < kx1) & (np.maximum(xa, xb) > kx0)
            ym = (np.minimum(ya, yb) < ky1) & (np.maximum(ya, yb) > ky0)
            zk = np.arange(nz)
            zm = (fr["wall"] + zk * v < kz1) & (fr["wall"] + (zk + 1) * v > kz0)
            grids[q][np.ix_(xm, ym, zm)] = True

    special = []
    jobs, unboxed = [], []
    for m in cfg["module"]:
        hit = next((p for p in lay["place"] if m["name"].startswith(p["match"])), None)
        loc = parse_at(hit["at"]) if hit else None
        box = next((b for b in geo["box"] if m["name"].startswith(b["match"])), None)
        if box and box.get("special") == "propulsion_bay":
            ko = geo["keepout"][0]
            sx_, sy_, sz_ = box["size"]
            zc = (ko["min"][2] + ko["max"][2]) / 2
            special.append({"name": m["name"], "col": 0, "tier": m.get("tier", "core"), "mass_kg": m["mass_kg"],
                            "shape": "cylx", "size": [sx_, sy_, sz_], "notched": False,
                            "min": [-fr["outer"][0] / 2 + fr["wall"] + 0.5, -sy_ / 2, zc - sz_ / 2],
                            "max": [-fr["outer"][0] / 2 + fr["wall"] + 0.5 + sx_, sy_ / 2, zc + sz_ / 2],
                            "true_volume_cm3": sx_ * sy_ * sz_ / 1000})
            continue
        if loc is None:
            continue
        box = next((b for b in geo["box"] if m["name"].startswith(b["match"])), None)
        if not box:
            unboxed.append(m["name"])
            continue
        jobs.append((m, box, loc, hit))
    jobs.sort(key=lambda j: (0 if j[1].get("end") else 1, -(j[1]["size"][0] * j[1]["size"][1] * j[1]["size"][2])))

    placed, failed, relocated = [], [], []
    for m, box, (q, d1, d2), hit in jobs:
        zlo, zhi = int(round((d1 - 1) * deck_h)), int(round(d2 * deck_h))
        sz = box["size"]
        cyl = box.get("shape") == "cyl"
        slack = math.ceil(box.get("slack_mm", 20) / v)   # allowed gap to the end plate (default 20 mm)
        if box.get("end") == "nadir":
            zlo, zhi = 0, math.ceil(sz[2] / v) + slack
        elif box.get("end") == "zenith":
            zlo, zhi = nz - math.ceil(sz[2] / v) - slack, nz
        result = None
        for attempt, (a, b_) in enumerate(((zlo, zhi),) if box.get("end") else ((zlo, zhi), (0, nz))):
            if attempt == 1 and (zlo, zhi) == (0, nz):
                break
            if cyl:
                d_vox = math.ceil((min(sz[0], sz[1]) - 5) / v)
                h_vox = math.ceil(sz[2] / v)
                pos = cyl_fit(grids[q], d_vox, h_vox, a, b_, top=box.get("align") == "top")
                if pos:
                    dims, o = (d_vox, d_vox, h_vox), tuple(sz)
                    result = (dims, pos, o)
                    break
            elif box.get("notched"):
                a_, b2, c_ = (math.ceil(sz[0] / v), math.ceil(sz[1] / v), math.ceil(sz[2] / v))
                keep = np.ones((a_, b2), dtype=bool)
                keep[:sp, :sp] = False                     # card's own notch clears the spine
                res = None
                for z in range(a, min(b_, nz) - c_ + 1):
                    if a_ > n or b2 > n:
                        break
                    sub = grids[q][0:a_, 0:b2, z:z + c_]
                    if not (sub & keep[:, :, None]).any():
                        res = ((a_, b2, c_), (0, 0, z), tuple(sz), keep)
                        break
                if res:
                    result = res[:3]
                    notch_keep = res[3]
                    break
            else:
                orients = ([tuple(sz)] if box.get("fixed") else
                           ([(sz[0], sz[1], sz[2]), (sz[1], sz[0], sz[2])] if not box.get("tilt")
                            else sorted(set(itertools.permutations(sz)))))
                best = None
                for o in orients:
                    dims = tuple(math.ceil(s_ / v) for s_ in o)
                    r_ = first_fit(grids[q], dims, a, b_)
                    if r_ and (best is None or r_[1] > best[3]):
                        best = (dims, r_[0], o, r_[1])
                if best:
                    result = best[:3]
                    break
            if attempt == 0:
                continue
        if not result:
            failed.append((m["name"], q, d1, d2, sz))
            continue
        dims, pos, o = result
        if not (zlo <= pos[2] and pos[2] + dims[2] <= zhi + 1):
            relocated.append((m["name"], q, d1, d2))
        if cyl:
            mask = disk_mask(dims[0])
            sub = grids[q][pos[0]:pos[0] + dims[0], pos[1]:pos[1] + dims[1], pos[2]:pos[2] + dims[2]]
            sub |= mask[:, :, None]
        elif box.get("notched"):
            grids[q][0:dims[0], 0:dims[1], pos[2]:pos[2] + dims[2]] |= notch_keep[:, :, None]
        else:
            grids[q][pos[0]:pos[0] + dims[0], pos[1]:pos[1] + dims[1], pos[2]:pos[2] + dims[2]] = True
        sx, sy = SIGN[q]
        u0 = fr["cross"] / 2 + pos[0] * v
        v0 = fr["cross"] / 2 + pos[1] * v
        xa, xb = sorted((sx * u0, sx * (u0 + dims[0] * v)))
        ya, yb = sorted((sy * v0, sy * (v0 + dims[1] * v)))
        za = fr["wall"] + pos[2] * v
        placed.append({
            "name": m["name"], "col": q, "tier": m.get("tier", "core"),
            "mass_kg": m["mass_kg"], "shape": box.get("shape", "box"),
            "size": list(o), "min": [xa, ya, za], "max": [xb, yb, za + dims[2] * v],
            "notched": bool(box.get("notched")),
            "true_volume_cm3": o[0] * o[1] * o[2] / 1000,
        })

    placed = special + placed
    occ_tot = sum(int(g.sum()) for g in grids.values())
    blocked_static = 4 * (sp * sp + rl * rl) * nz
    mod_vox = occ_tot - blocked_static
    all_vox = 4 * (n * n * nz) - blocked_static
    if not quiet:
        print(f"== Geometric packing: column interior {inner:.1f} x {inner:.1f} x {inner_z:.1f} mm, voxel {v} mm ==")
        for q in SIGN:
            g = grids[q]
            stat = (sp * sp + rl * rl) * nz
            print(f"Q{q}: {(int(g.sum()) - stat) / (g.size - stat) * 100:5.1f} % of usable column volume occupied "
                  f"({sum(1 for p in placed if p['col'] == q)} modules)")
        print(f"Whole interior: {mod_vox / all_vox * 100:.1f} % occupied (after rounding sizes up to {v} mm)")
        for n_ in unboxed:
            print(f"[no box defined] {n_}")
        if failed:
            print("-- DID NOT FIT (volume may fit, geometry does not) --")
            for nm, q, d1, d2, sz in failed:
                print(f"  Q{q} decks {d1}-{d2}: {nm[:64]} size {sz}")
        else:
            print("All modules placed.")
        if relocated:
            print("-- Relocated to another deck of the same column (layout file needs updating) --")
            for nm, q, d1, d2 in relocated:
                print(f"  Q{q} (planned decks {d1}-{d2}): {nm[:70]}")
    out = os.path.join(os.path.dirname(os.path.abspath(__file__)), "out")
    os.makedirs(out, exist_ok=True)
    json.dump({"placed": placed, "failed": [f[0] for f in failed], "relocated": [r[0] for r in relocated], "inner": inner, "inner_z": inner_z},
              open(os.path.join(out, "placement.json"), "w"), indent=1)
    return placed, failed


if __name__ == "__main__":
    a = sys.argv[1:4] or ["configs/12u_science.toml", "configs/12u_layout.toml", "configs/12u_geometry.toml"]
    build(*a)
