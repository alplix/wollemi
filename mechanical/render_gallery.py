"""Extra visualisation gallery: more exterior/interior static views, an exploded assembly view, a three-view
orthographic drawing sheet, and two GIF animations (360 deg spin, deploy sequence). Uses the same CAD model,
rasteriser and colour scheme as mechanical/wollemi_cad.py so nothing here can silently drift from the real
placement/geometry.

Usage: python mechanical/render_gallery.py     (run mechanical/pack.py first so placement.json is current)
Writes to mechanical/out/gallery/.

Note on the deployment animation: the wing hinge/accordion mechanism is not modelled anywhere in this project
(mechanical/README.md lists it as still to design), so the in-between frames are a straight-line interpolation
of each panel's stowed and deployed footprints, staggered so the root panel of each wing moves first -- a
schematic illustration of the deployment sequence, not a validated mechanism simulation.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wollemi_cad as wc  # noqa: E402
from build123d import Pos  # noqa: E402

OUT = os.path.join(HERE, "out", "gallery")


def meshes(parts, hide=()):
    out = []
    for p in parts:
        if any(p["name"].startswith(h) for h in hide):
            continue
        out.append((wc.to_mesh(p["shape"]), p["color"], 1.0))
    return out


def explode(parts, radial=2.2, z_scale=0.9, z0=170.25):
    """Return NEW parts (shapes translated) pushed outward from the spine and spread in Z, for an exploded view."""
    out = []
    for p in parts:
        b = p["shape"].bounding_box()
        cx = (b.min.X + b.max.X) / 2
        cy = (b.min.Y + b.max.Y) / 2
        cz = (b.min.Z + b.max.Z) / 2
        dx, dy = cx * (radial - 1), cy * (radial - 1)
        dz = (cz - z0) * (z_scale - 1)
        q = dict(p)
        q["shape"] = Pos(dx, dy, dz) * p["shape"]
        out.append(q)
    return out


def lerp(a, b, t):
    return a + (b - a) * t


def build_wings_frac(geo, frac_by_panel):
    """Straight-line interpolation between wollemi_cad.build_wings(geo, False) and (geo, True) footprints,
    per panel (see module docstring: this is a schematic illustration, not a mechanism simulation)."""
    fr = geo["frame"]
    wg = geo["wings"]
    ox, oy, oz = fr["outer"]
    hx, hy = ox / 2, oy / 2
    pw, pl, pt = wg["panel"]
    n = wg["panels_per_wing"]
    parts = []
    for sgn in (1, -1):
        for k in range(n):
            t = frac_by_panel(sgn, k)
            ya, yb = sorted((sgn * (hy + k * pt), sgn * (hy + (k + 1) * pt)))
            xa_st, xb_st = -hx, hx
            y0 = sgn * (hy + wg["standoff"])
            xa_dp, xb_dp = sorted((sgn * (hx + k * pw), sgn * (hx + (k + 1) * pw)))
            ya_dp, yb_dp = sorted((y0, y0 + sgn * pt))
            x0, x1 = lerp(xa_st, xa_dp, t), lerp(xb_st, xb_dp, t)
            y0_, y1_ = lerp(ya, ya_dp, t), lerp(yb, yb_dp, t)
            shp = wc.box(min(x0, x1), min(y0_, y1_), 0, max(x0, x1), max(y0_, y1_), pl)
            name = f"Wing {'A' if sgn > 0 else 'B'} panel {k + 1}"
            shp.label = name
            parts.append({"name": name, "shape": shp, "color": wc.WING_COLOR, "kind": "wing"})
    return parts


def save_gif(frames_rgb, path, duration_ms=70, loop=0):
    from PIL import Image
    imgs = [Image.fromarray(f) for f in frames_rgb]
    imgs[0].save(path, save_all=True, append_images=imgs[1:], duration=duration_ms, loop=loop, optimize=True)


def render_to_array(named, az, el, size, title=""):
    """Like wc.render() but returns an RGB array instead of writing straight to disk (for GIF assembly)."""
    import numpy as np
    from PIL import Image
    tmp = os.path.join(OUT, "_frame_tmp.png")
    wc.render(named, tmp, az=az, el=el, size=size, title=title)
    arr = np.array(Image.open(tmp).convert("RGB"))
    return arr


def make_three_view_sheet(geo):
    """Compose the front/side/top renders into one engineering-drawing-style sheet with a title block and the
    real envelope dimensions from configs/12u_geometry.toml (via geo['frame']['outer'])."""
    from PIL import Image, ImageDraw, ImageFont
    ox, oy, oz = geo["frame"]["outer"]
    imgs = {k: Image.open(os.path.join(OUT, f"{k}.png")) for k in ("ext_front", "ext_side", "ext_top")}
    pad, cell_w, cell_h = 40, 620, 460
    W = pad * 4 + cell_w * 2
    H = pad * 3 + cell_h * 2 + 120
    sheet = Image.new("RGB", (W, H), (15, 20, 32))
    d = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.load_default(size=26)
        small = ImageFont.load_default(size=17)
    except Exception:
        font = small = ImageFont.load_default()
    d.text((pad, 16), "Wollemi 12U -- three-view engineering drawing (schematic, from the real CAD model)", fill=(225, 232, 245), font=font)
    positions = {"ext_front": (pad, 90), "ext_side": (pad * 2 + cell_w, 90), "ext_top": (pad, pad + cell_h + 90)}
    for k, (x, y) in positions.items():
        im = imgs[k].resize((cell_w, cell_h))
        sheet.paste(im, (x, y))
        d.rectangle([x, y, x + cell_w, y + cell_h], outline=(90, 100, 120), width=2)
    info_x, info_y = pad * 2 + cell_w, pad + cell_h + 90
    lines = [
        f"Envelope: {ox:.1f} x {oy:.1f} x {oz:.1f} mm (12U CDS envelope)",
        "Grid: 2 x 2 x 3 cells around a 40 mm central spine",
        "Columns: Q1 telescope, Q2 attitude/ballast,",
        "  Q3 compute/comms, Q4 energy/rad science",
        "Wings: 2 x 3 double-sided panels",
        "  (not shown here; see ext_iso_deployed.png)",
        "All dimensions from configs/12u_geometry.toml,",
        "  the single source of truth; regenerate this sheet",
        "  with mechanical/render_gallery.py after any change.",
        "Analysis-level design; no hardware exists.",
    ]
    yy = info_y + 10
    for ln in lines:
        d.text((info_x + 10, yy), ln, fill=(190, 200, 215), font=small)
        yy += 28
    d.rectangle([info_x, info_y, info_x + cell_w, info_y + cell_h], outline=(90, 100, 120), width=2)
    sheet.save(os.path.join(OUT, "three_view_drawing.png"))


def main():
    os.makedirs(OUT, exist_ok=True)
    geo, cfg, pl = wc.load()
    placed = pl["placed"]
    frame, plume = wc.build_frame(geo, placed)
    mods = wc.build_modules(placed)
    wings_st = wc.build_wings(geo, False)
    wings_dp = wc.build_wings(geo, True)

    HD = (1800, 1300)

    print("Static renders...")
    render_jobs = [
        (meshes(frame + mods + wings_dp), "ext_iso_deployed.png", 40, 26, "Wollemi 12U -- deployed, isometric"),
        (meshes(frame + mods + wings_dp), "ext_iso_deployed_far.png", 120, 18, "Wollemi 12U -- deployed, aft-quarter view"),
        (meshes(frame + mods + wings_st), "ext_iso_stowed.png", 40, 26, "Wollemi 12U -- stowed (launch configuration)"),
        (meshes(frame + mods), "ext_front.png", 0, 0, "Wollemi 12U -- front elevation (+X face), body only"),
        (meshes(frame + mods), "ext_side.png", 90, 0, "Wollemi 12U -- side elevation (+Y face), body only"),
        (meshes(frame + mods), "ext_top.png", 0, 89, "Wollemi 12U -- top view (+Z / zenith), body only"),
        (meshes(frame + mods, hide=("Wall", "Nadir plate", "Zenith plate")), "interior.png", 42, 24, "Wollemi 12U -- interior, walls hidden"),
        (meshes(frame + mods, hide=("Wall +X", "Wall +Y", "Zenith plate")), "cutaway.png", 48, 20, "Wollemi 12U -- cutaway (2 walls + zenith plate removed)"),
        (meshes(frame + mods + wings_st), "ext_nadir.png", 35, -55, "Wollemi 12U -- nadir (Earth-facing) view, stowed"),
    ]
    for named, fname, az, el, title in render_jobs:
        wc.render(named, os.path.join(OUT, fname), az=az, el=el, size=HD, title=title)
        print("  wrote", fname)

    print("Three-view drawing sheet...")
    make_three_view_sheet(geo)

    print("Exploded view...")
    ex_frame = explode(frame, radial=1.15, z_scale=1.0)
    ex_mods = explode(mods, radial=2.3, z_scale=1.7)
    wc.render(meshes(ex_frame, hide=("Wall", "Nadir plate", "Zenith plate")) + meshes(ex_mods),
              os.path.join(OUT, "exploded.png"), az=42, el=22, size=HD,
              title="Wollemi 12U -- exploded view (schematic; not a real assembly sequence)")

    print("360 deg spin GIF (deployed)...")
    frames = []
    N = 48
    for i in range(N):
        az = 360.0 * i / N
        frames.append(render_to_array(meshes(frame + mods + wings_dp), az, 22, (700, 520)))
    save_gif(frames, os.path.join(OUT, "spin_deployed.gif"), duration_ms=65)
    print("  wrote spin_deployed.gif")

    print("Deployment sequence GIF (schematic)...")
    frames = []
    N = 30
    HOLD = 8
    for i in range(N):
        frac = i / (N - 1)

        def frac_by_panel(sgn, k, frac=frac):
            # stagger so the root panel (k=0, nearest the body) starts first, tip panel (k=2) last
            t0 = k * 0.28
            t1 = t0 + 0.55
            if frac <= t0:
                return 0.0
            if frac >= t1:
                return 1.0
            return (frac - t0) / (t1 - t0)

        wings_f = build_wings_frac(geo, frac_by_panel)
        az = 40 + 20 * frac
        frames.append(render_to_array(meshes(frame + mods + wings_f), az, 24, (700, 520),
                                       title=f"Deploying wings -- {int(frac * 100)}% (schematic)"))
    for _ in range(HOLD):
        frames.append(frames[-1])
    frames_back = list(reversed(frames))
    save_gif(frames + frames_back, os.path.join(OUT, "deploy_sequence.gif"), duration_ms=90)
    print("  wrote deploy_sequence.gif")

    tmp = os.path.join(OUT, "_frame_tmp.png")
    if os.path.exists(tmp):
        os.remove(tmp)
    print("\nDone. Files in", OUT)


if __name__ == "__main__":
    main()
