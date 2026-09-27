"""Hero shots: the real CAD model composited over a procedurally generated space backdrop (starfield, Earth limb,
sun glare) -- an illustrative "in orbit" look for outreach use, not a new analysis. The spacecraft geometry and
pose are exactly what mechanical/wollemi_cad.py builds; the backdrop behind it, and the solar-cell-grid /
MLI-foil surface materials applied to the wing and wall faces (apply_materials, in place of the flat colours
used in the technical renders), are artwork for a more recognisably satellite-like look, not a new analysis.

Usage: python mechanical/render_space.py
Writes to mechanical/out/gallery/space_*.png
"""
import math
import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wollemi_cad as wc  # noqa: E402

OUT = os.path.join(HERE, "out", "gallery")


def render_rgba(named, az, el, size, zoom=1.0):
    """A close copy of wollemi_cad.render()'s rasteriser, but returns an RGBA array (alpha=0 wherever no
    triangle was drawn), a per-pixel part-id buffer and a per-pixel interpolated world-position buffer,
    instead of writing a filled-background PNG -- so the result can be composited over a separate backdrop
    and post-processed with per-part materials (solar cell grid, MLI foil). Kept as a near-duplicate of
    wollemi_cad.render() rather than changing that shared function's signature/behaviour.

    `named` items are (mesh, color, alpha, name) -- like wollemi_cad's (mesh, color, alpha) tuples plus a
    part name, so callers can tell which pixels belong to (for example) a part whose name starts with "Wing"."""
    S = 2
    W, H = size[0] * S, size[1] * S
    ca, sa = math.cos(math.radians(az)), math.sin(math.radians(az))
    ce, se = math.cos(math.radians(el)), math.sin(math.radians(el))

    V, T, C, IDS = [], [], [], []
    pid_name = {0: ""}
    off = 0
    for pid, item in enumerate(named):
        mesh, color = item[0], item[1]
        name = item[3] if len(item) > 3 else ""
        pid_name[pid + 1] = name
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
    dz = V[:, 2] * se - yr * ce
    sc = min(W * 0.80 / (sx.max() - sx.min()), H * 0.78 / (sy.max() - sy.min())) * zoom
    px = (sx - (sx.max() + sx.min()) / 2) * sc + W / 2
    py = (sy - (sy.max() + sy.min()) / 2) * sc + H / 2

    a, b, c = V[T[:, 0]], V[T[:, 1]], V[T[:, 2]]
    n = np.cross(b - a, c - a)
    n /= np.maximum(np.linalg.norm(n, axis=1, keepdims=True), 1e-12)
    cam = np.array([sa * ce, -ca * ce, se])
    cam = cam / np.linalg.norm(cam)
    flip = (n @ cam) < 0
    n[flip] *= -1
    L = np.array([0.5, -0.55, 0.55])
    L /= np.linalg.norm(L)
    light = 0.12 + 0.55 * np.clip(n @ L, 0, 1) + 0.18 * np.clip(n @ cam, 0, 1)
    col = np.clip(C * light[:, None], 0, 255)

    zbuf = np.full((H, W), -1e18)
    idb = np.zeros((H, W), dtype=np.int32)
    img = np.zeros((H, W, 3), dtype=np.float64)
    wpos = np.zeros((H, W, 3), dtype=np.float64)
    hit = np.zeros((H, W), dtype=bool)
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
        wp = l0[..., None] * V[i0] + l1[..., None] * V[i1] + l2[..., None] * V[i2]
        wpos[ymin:ymax + 1, xmin:xmax + 1][upd] = wp[upd]
        hit[ymin:ymax + 1, xmin:xmax + 1] |= upd

    edge = np.zeros((H, W), dtype=bool)
    edge[:, :-1] |= idb[:, :-1] != idb[:, 1:]
    edge[:-1, :] |= idb[:-1, :] != idb[1:, :]
    zc = np.where(zbuf > -1e17, zbuf, np.nan)
    gz = np.abs(np.diff(zc, axis=1, prepend=zc[:, :1])) + np.abs(np.diff(zc, axis=0, prepend=zc[:1, :]))
    edge |= np.nan_to_num(gz, nan=0) > 6.0
    img[edge & hit] *= 0.35

    alpha = np.where(hit, 255, 0).astype(np.uint8)
    rgba = np.dstack([np.clip(img, 0, 255).astype(np.uint8), alpha])
    out = Image.fromarray(rgba, mode="RGBA").resize(size, Image.LANCZOS)
    # idb/wpos: nearest-neighbour downsample to the output grid (categorical id + UV-ish data; no need for the
    # supersampled anti-aliasing quality the colour image gets above)
    idb_small = idb[::S, ::S][:size[1], :size[0]]
    wpos_small = wpos[::S, ::S][:size[1], :size[0]]
    return out, idb_small, wpos_small, pid_name


def starfield(size, n_stars=900, seed=7, glow=True):
    rng = np.random.default_rng(seed)
    W, H = size
    img = np.zeros((H, W, 3), dtype=np.float64)
    xs = rng.integers(0, W, n_stars)
    ys = rng.integers(0, H, n_stars)
    b = rng.random(n_stars) ** 2.2
    for x, y, bb in zip(xs, ys, b):
        v = 70 + 185 * bb
        img[y, x] = (v, v, v * 0.98 + 6)
        if bb > 0.85:
            for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                xx, yy = x + dx, y + dy
                if 0 <= xx < W and 0 <= yy < H:
                    img[yy, xx] = np.maximum(img[yy, xx], (v * 0.35, v * 0.35, v * 0.34))
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    if glow:
        blurred = im.filter(ImageFilter.GaussianBlur(1.1))
        im = Image.blend(im, blurred, 0.35)
    return im


def deep_space_background(size, sun_xy=None):
    """A near-black gradient with a faint galactic haze band, no Earth -- for a wide, lonely deep-space shot."""
    W, H = size
    yy, xx = np.mgrid[0:H, 0:W]
    band = np.exp(-((yy - H * 0.42) ** 2) / (2 * (H * 0.30) ** 2))
    diag = (xx / W + yy / H) / 2
    base = 3 + 5 * diag
    haze = 10 * band
    img = np.stack([base + haze * 0.9, base + haze * 0.85, base + haze * 1.05], axis=-1)
    im = Image.fromarray(np.clip(img, 0, 255).astype(np.uint8))
    im = Image.alpha_composite(im.convert("RGBA"), starfield(size, 1400, seed=3).convert("RGBA"))
    if sun_xy:
        im = add_sun_glare(im, sun_xy, radius=26, brightness=1.0)
    return im


def add_earth_limb(im, size, center, radius):
    """A simplified procedural Earth limb: a shaded sphere with a soft blue atmospheric rim, no photographic
    texture (this is illustration, not a map)."""
    W, H = size
    cx, cy = center
    yy, xx = np.mgrid[0:H, 0:W].astype(np.float64)
    d = np.sqrt((xx - cx) ** 2 + (yy - cy) ** 2)
    inside = d <= radius
    nx = (xx - cx) / radius
    ny = (yy - cy) / radius
    nz = np.sqrt(np.clip(1 - nx ** 2 - ny ** 2, 0, 1))
    light = np.array([-0.55, -0.35, 0.75])
    light = light / np.linalg.norm(light)
    shade = np.clip(nx * light[0] + ny * light[1] + nz * light[2], 0, 1)
    ocean = np.array([18, 55, 110])
    land = np.array([70, 110, 60])
    rng = np.random.default_rng(11)
    blotches = rng.random((H, W))
    blotch_im = Image.fromarray((blotches * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(radius * 0.10, 6)))
    blotches = np.asarray(blotch_im, dtype=np.float64) / 255.0
    fine = rng.random((H, W))
    fine_im = Image.fromarray((fine * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(max(radius * 0.02, 2)))
    fine = np.asarray(fine_im, dtype=np.float64) / 255.0
    mix = (0.75 * blotches + 0.25 * fine) > 0.53
    base = np.where(mix[..., None], land, ocean)
    cloud = (rng.random((H, W)) > 0.90).astype(np.float64)
    cloud_img = Image.fromarray((cloud * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(6))
    cloud = np.asarray(cloud_img, dtype=np.float64) / 255.0
    rgb = base * (0.25 + 0.9 * shade[..., None]) * (1 - 0.5 * cloud[..., None]) + 255 * 0.5 * cloud[..., None] * shade[..., None]
    a = np.where(inside, 255, 0).astype(np.uint8)
    earth = np.dstack([np.clip(rgb, 0, 255), a]).astype(np.uint8)
    earth_im = Image.fromarray(earth, mode="RGBA")

    rim = np.clip((radius + 10 - d) / 14, 0, 1) * np.clip((d - radius + 4) / 14, 0, 1)
    rim_col = np.zeros((H, W, 4), dtype=np.uint8)
    rim_col[..., 0] = 90
    rim_col[..., 1] = 150
    rim_col[..., 2] = 255
    rim_col[..., 3] = np.clip(rim * 160, 0, 255).astype(np.uint8)
    rim_im = Image.fromarray(rim_col, mode="RGBA").filter(ImageFilter.GaussianBlur(3))

    out = im.convert("RGBA")
    out = Image.alpha_composite(out, rim_im)
    out = Image.alpha_composite(out, earth_im)
    return out


def add_sun_glare(im, xy, radius=60, brightness=1.0):
    W, H = im.size
    layer = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    x, y = xy
    for rr, alpha in ((radius * 6, int(28 * brightness)), (radius * 3.2, int(55 * brightness)),
                      (radius * 1.6, int(110 * brightness)), (radius, int(255 * brightness))):
        d.ellipse([x - rr, y - rr, x + rr, y + rr], fill=(255, 250, 235, alpha))
    layer = layer.filter(ImageFilter.GaussianBlur(radius * 0.18))
    d2 = ImageDraw.Draw(layer)
    for ang in (0, 45, 90, 135):
        ln = radius * 5
        dx, dy = math.cos(math.radians(ang)) * ln, math.sin(math.radians(ang)) * ln
        d2.line([x - dx, y - dy, x + dx, y + dy], fill=(255, 250, 235, int(30 * brightness)), width=2)
    d2.ellipse([x - radius, y - radius, x + radius, y + radius], fill=(255, 255, 250, 255))
    return Image.alpha_composite(im.convert("RGBA"), layer)


def part_mask(idb, pid_name, prefix):
    ids = [pid for pid, name in pid_name.items() if pid and name.startswith(prefix)]
    if not ids:
        return np.zeros(idb.shape, dtype=bool)
    return np.isin(idb, ids)


def apply_solar_cells(craft, idb, wpos, pid_name):
    """Overlay a solar-cell grid on wing pixels: real triple-junction CubeSat cells are dark blue-violet, laid
    out in a regular grid with a visible seam and a slight per-cell brightness/tint variation, not a flat colour."""
    mask = part_mask(idb, pid_name, "Wing")
    if not mask.any():
        return craft
    arr = np.array(craft).astype(np.float64)
    x, z = wpos[..., 0], wpos[..., 2]
    cell = 27.0  # mm, close to a real triple-junction cell pitch
    fx = (x / cell) % 1.0
    fz = (z / cell) % 1.0
    seam = (np.minimum(fx, 1 - fx) < 0.045) | (np.minimum(fz, 1 - fz) < 0.045)
    rng = np.random.default_rng(3)
    cell_id = (np.floor(x / cell) * 1000 + np.floor(z / cell)).astype(np.int64)
    uniq, inv = np.unique(cell_id[mask], return_inverse=True)
    tint = rng.uniform(0.85, 1.08, size=len(uniq))
    cell_tint = np.ones(idb.shape, dtype=np.float64)
    cell_tint[mask] = tint[inv]
    cell_rgb = np.array([26, 20, 48])  # dark blue-violet, typical of triple-junction cells under a coverglass
    base = arr[..., :3]
    lum = base.mean(axis=-1, keepdims=True) / 255.0
    shaded_cell = cell_rgb[None, None, :] * (0.55 + 0.65 * lum) * cell_tint[..., None]
    specular = np.clip((lum[..., 0] - 0.55) * 1.8, 0, 1) ** 2
    shaded_cell = shaded_cell + specular[..., None] * np.array([40, 42, 60])[None, None, :]
    out_rgb = np.where(mask[..., None], shaded_cell, base)
    out_rgb = np.where((mask & seam)[..., None], out_rgb * 0.35, out_rgb)
    arr[..., :3] = np.clip(out_rgb, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode=craft.mode)


def apply_mli_foil(craft, idb, wpos, pid_name, hit):
    """Overlay a gold/silver multi-layer-insulation crinkle texture on the structural wall/frame pixels --
    the iconic blanket look, in place of a flat metallic grey."""
    mask = part_mask(idb, pid_name, "Wall")
    if not mask.any():
        return craft
    H, W = idb.shape
    rng = np.random.default_rng(5)
    noise = rng.random((H, W))
    fine = np.asarray(Image.fromarray((noise * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(1.4)), dtype=np.float64) / 255.0
    creases = rng.random((H, W))
    creases = np.asarray(Image.fromarray((creases * 255).astype(np.uint8)).filter(ImageFilter.GaussianBlur(0.6)), dtype=np.float64) / 255.0
    wrinkle = 0.65 + 0.55 * fine + 0.35 * (creases - 0.5)
    gold = np.array([176, 140, 62])
    arr = np.array(craft).astype(np.float64)
    base = arr[..., :3]
    lum = base.mean(axis=-1, keepdims=True) / 255.0
    shaded = gold[None, None, :] * (0.35 + 0.9 * lum[..., 0])[..., None] * wrinkle[..., None]
    hi = np.clip((wrinkle - 1.15), 0, None) * 260
    shaded = shaded + hi[..., None] * np.array([1.0, 0.95, 0.75])[None, None, :]
    out_rgb = np.where(mask[..., None], shaded, base)
    arr[..., :3] = np.clip(out_rgb, 0, 255)
    return Image.fromarray(arr.astype(np.uint8), mode=craft.mode)


def apply_materials(craft, idb, wpos, pid_name, hit):
    craft = apply_solar_cells(craft, idb, wpos, pid_name)
    craft = apply_mli_foil(craft, idb, wpos, pid_name, hit)
    return craft


def caption(im, text):
    d = ImageDraw.Draw(im)
    try:
        font = ImageFont.load_default(size=24)
        small = ImageFont.load_default(size=15)
    except Exception:
        font = small = ImageFont.load_default()
    d.text((26, 20), text, fill=(235, 240, 250), font=font)
    d.text((26, 52), "Illustration: real CAD geometry, artistic space backdrop (not a photograph)", fill=(160, 170, 190), font=small)
    return im


def main():
    os.makedirs(OUT, exist_ok=True)
    geo, cfg, pl = wc.load()
    placed = pl["placed"]
    frame, plume = wc.build_frame(geo, placed)
    mods = wc.build_modules(placed)
    wings_dp = wc.build_wings(geo, True)

    def meshes(parts):
        return [(wc.to_mesh(p["shape"]), p["color"], 1.0, p["name"]) for p in parts]

    size = (1920, 1280)
    ship = meshes(frame + mods + wings_dp)

    print("Earth-limb hero shot...")
    craft, idb, wpos, pid_name = render_rgba(ship, az=52, el=18, size=size, zoom=1.35)
    craft = apply_materials(craft, idb, wpos, pid_name, idb > 0)
    bg = deep_space_background(size)
    bg = add_earth_limb(bg, size, center=(size[0] * 0.14, size[1] * 1.02), radius=size[1] * 0.62)
    bg = add_sun_glare(bg, (size[0] * 0.92, size[1] * 0.12), radius=34, brightness=0.9)
    scene = Image.alpha_composite(bg, craft).convert("RGB")
    caption(scene, "Wollemi 12U in orbit -- dawn-dusk sun-synchronous, ~700 km").save(os.path.join(OUT, "space_earth_limb.png"))

    print("Deep-space wide shot...")
    craft2, idb2, wpos2, pid_name2 = render_rgba(ship, az=-35, el=12, size=size, zoom=1.05)
    craft2 = apply_materials(craft2, idb2, wpos2, pid_name2, idb2 > 0)
    bg2 = deep_space_background(size, sun_xy=(size[0] * 0.20, size[1] * 0.24))
    scene2 = Image.alpha_composite(bg2, craft2).convert("RGB")
    caption(scene2, "Wollemi 12U, deployed").save(os.path.join(OUT, "space_deep_field.png"))

    print("Stowed, sunlit approach...")
    ship_st = meshes(frame + mods + wc.build_wings(geo, False))
    craft3, idb3, wpos3, pid_name3 = render_rgba(ship_st, az=32, el=16, size=size, zoom=0.85)
    craft3 = apply_materials(craft3, idb3, wpos3, pid_name3, idb3 > 0)
    bg3 = deep_space_background(size)
    bg3 = add_sun_glare(bg3, (size[0] * 0.80, size[1] * 0.24), radius=55, brightness=1.1)
    scene3 = Image.alpha_composite(bg3, craft3).convert("RGB")
    caption(scene3, "Wollemi 12U, stowed -- pre-deployment").save(os.path.join(OUT, "space_stowed_sunlit.png"))

    print("Done ->", OUT)


if __name__ == "__main__":
    main()
