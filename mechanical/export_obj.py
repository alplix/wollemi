"""Export the real CAD assembly (mechanical/wollemi_cad.py) as a Wavefront OBJ + MTL, with parts grouped into
materials by category (solar cells, MLI foil, aluminium structure, module colours) -- for rendering in a real
path tracer (Blender/Cycles) instead of this project's own lightweight rasteriser, when a genuinely
photorealistic look is wanted (see mechanical/render_blender.py, which consumes this OBJ).

Usage: python mechanical/export_obj.py [deployed|stowed]
Writes mechanical/out/wollemi_12u_<config>.obj (+ .mtl).
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import wollemi_cad as wc  # noqa: E402

OUT = os.path.join(HERE, "out")

MATERIALS = {
    "solar_cell": (26, 20, 48),
    "mli_foil": (176, 140, 62),
    "aluminum": (150, 155, 165),
    "module": (200, 170, 90),
}


def material_for(part):
    name = part["name"]
    if name.startswith("Wing"):
        return "solar_cell"
    if name.startswith("Wall"):
        return "mli_foil"
    if part.get("kind") == "module":
        return "module"
    return "aluminum"


def write_obj(parts, path):
    mtl_path = path[:-4] + ".mtl"
    mtl_name = os.path.basename(mtl_path)
    lines = [f"mtllib {mtl_name}"]
    voff = 1
    used_mats = set()
    for i, p in enumerate(parts):
        mesh = wc.to_mesh(p["shape"])
        verts, tris = mesh
        mat = material_for(p)
        used_mats.add(mat)
        safe_name = "".join(c if c.isalnum() else "_" for c in p["name"])[:40]
        lines.append(f"o part_{i}_{safe_name}")
        lines.append(f"usemtl {mat}")
        for x, y, z in verts:
            lines.append(f"v {x:.4f} {y:.4f} {z:.4f}")
        for a, b, c in tris:
            lines.append(f"f {a + voff} {b + voff} {c + voff}")
        voff += len(verts)
    open(path, "w", encoding="utf-8").write("\n".join(lines) + "\n")

    mtl_lines = []
    for name, (r, g, b) in MATERIALS.items():
        if name not in used_mats:
            continue
        mtl_lines += [f"newmtl {name}", f"Kd {r / 255:.3f} {g / 255:.3f} {b / 255:.3f}", "Ka 0 0 0", "Ks 0.2 0.2 0.2", "Ns 20", ""]
    open(mtl_path, "w", encoding="utf-8").write("\n".join(mtl_lines))
    print(f"Wrote {path} ({len(parts)} parts) and {mtl_path}")


def main():
    cfg_name = sys.argv[1] if len(sys.argv) > 1 else "deployed"
    geo, cfg, pl = wc.load()
    placed = pl["placed"]
    frame, plume = wc.build_frame(geo, placed)
    mods = wc.build_modules(placed)
    wings = wc.build_wings(geo, cfg_name == "deployed")
    os.makedirs(OUT, exist_ok=True)
    write_obj(frame + mods + wings, os.path.join(OUT, f"wollemi_12u_{cfg_name}_textured.obj"))


if __name__ == "__main__":
    main()
