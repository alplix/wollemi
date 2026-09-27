"""Photorealistic 'in orbit' render via a real path tracer (Blender/Cycles), instead of this project's own
lightweight rasteriser (mechanical/render_space.py). Reads the OBJ mechanical/export_obj.py writes (the real
CAD geometry), builds proper PBR materials per part category, a starfield + NASA Blue Marble Earth + sun, and
renders with Cycles.

This file must be run INSIDE Blender's own Python (it imports bpy), not with the system python:

    python mechanical/export_obj.py deployed
    "<path to blender.exe>" --background --factory-startup --python mechanical/render_blender.py -- deployed

Materials are illustrative choices (solar-cell grid, gold/silver MLI foil, brushed aluminium, dark anodised
payload apertures), not a new analysis -- the geometry and layout are exactly what mechanical/wollemi_cad.py
builds. The Earth texture is NASA's public-domain Blue Marble (land_ocean_ice_cloud_2048.jpg,
https://visibleearth.nasa.gov/images/57735); the starfield is procedural.
"""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "out", "gallery")
ASSETS = os.path.join(HERE, "blender_assets")


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def import_obj(path):
    # forward_axis='Y', up_axis='Z' keeps the file's own axes unchanged on import: this OBJ (mechanical/export_obj.py)
    # is written directly from the CAD model's Z-up coordinates, not the OBJ-format convention (Y-up) Blender
    # otherwise assumes and silently rotates 90 degrees to match.
    try:
        bpy.ops.wm.obj_import(filepath=path, forward_axis="Y", up_axis="Z")
    except AttributeError:
        bpy.ops.import_scene.obj(filepath=path, axis_forward="Y", axis_up="Z")


def node(mat, tree_setup):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    tree_setup(nt)


def build_solar_cell_material(mat):
    def setup(nt):
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        checker = nt.nodes.new("ShaderNodeTexChecker")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        ramp = nt.nodes.new("ShaderNodeValToRGB")
        bump = nt.nodes.new("ShaderNodeBump")

        mapping.inputs["Scale"].default_value = (1 / 27.0, 1 / 27.0, 1 / 27.0)
        checker.inputs["Scale"].default_value = 1.0
        noise.inputs["Scale"].default_value = 400.0
        ramp.color_ramp.elements[0].color = (0.02, 0.015, 0.05, 1)
        ramp.color_ramp.elements[1].color = (0.06, 0.045, 0.12, 1)

        bsdf.inputs["Roughness"].default_value = 0.18
        bsdf.inputs["Metallic"].default_value = 0.15
        if "IOR" in bsdf.inputs:
            bsdf.inputs["IOR"].default_value = 1.5
        if "Specular IOR Level" in bsdf.inputs:
            bsdf.inputs["Specular IOR Level"].default_value = 0.6

        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], checker.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], noise.inputs["Vector"])
        nt.links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(checker.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = 0.25
        bump.inputs["Distance"].default_value = 0.4
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    node(mat, setup)


def build_mli_foil_material(mat):
    def setup(nt):
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        tex_coord = nt.nodes.new("ShaderNodeTexCoord")
        mapping = nt.nodes.new("ShaderNodeMapping")
        wrinkle = nt.nodes.new("ShaderNodeTexVoronoi")
        wrinkle2 = nt.nodes.new("ShaderNodeTexNoise")
        bump = nt.nodes.new("ShaderNodeBump")
        ramp = nt.nodes.new("ShaderNodeValToRGB")

        mapping.inputs["Scale"].default_value = (0.05, 0.05, 0.05)
        wrinkle.inputs["Scale"].default_value = 18.0
        wrinkle2.inputs["Scale"].default_value = 60.0
        ramp.color_ramp.elements[0].color = (0.55, 0.42, 0.14, 1)
        ramp.color_ramp.elements[1].color = (0.95, 0.82, 0.45, 1)

        bsdf.inputs["Metallic"].default_value = 0.9
        bsdf.inputs["Roughness"].default_value = 0.35

        nt.links.new(tex_coord.outputs["Object"], mapping.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], wrinkle.inputs["Vector"])
        nt.links.new(mapping.outputs["Vector"], wrinkle2.inputs["Vector"])
        nt.links.new(wrinkle.outputs["Distance"], ramp.inputs["Fac"])
        nt.links.new(ramp.outputs["Color"], bsdf.inputs["Base Color"])
        nt.links.new(wrinkle2.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = 0.35
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    node(mat, setup)


def build_aluminum_material(mat):
    def setup(nt):
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        noise = nt.nodes.new("ShaderNodeTexNoise")
        bump = nt.nodes.new("ShaderNodeBump")
        bsdf.inputs["Base Color"].default_value = (0.55, 0.56, 0.58, 1)
        bsdf.inputs["Metallic"].default_value = 1.0
        bsdf.inputs["Roughness"].default_value = 0.32
        noise.inputs["Scale"].default_value = 800.0
        nt.links.new(noise.outputs["Fac"], bump.inputs["Height"])
        bump.inputs["Strength"].default_value = 0.08
        nt.links.new(bump.outputs["Normal"], bsdf.inputs["Normal"])
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    node(mat, setup)


def build_module_material(mat):
    def setup(nt):
        out = nt.nodes.new("ShaderNodeOutputMaterial")
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        bsdf.inputs["Base Color"].default_value = (0.03, 0.03, 0.035, 1)
        bsdf.inputs["Metallic"].default_value = 0.6
        bsdf.inputs["Roughness"].default_value = 0.45
        nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    node(mat, setup)


MATERIAL_BUILDERS = {
    "solar_cell": build_solar_cell_material,
    "mli_foil": build_mli_foil_material,
    "aluminum": build_aluminum_material,
    "module": build_module_material,
}


def apply_materials():
    for mat in bpy.data.materials:
        builder = MATERIAL_BUILDERS.get(mat.name)
        if builder:
            builder(mat)


def add_starfield(strength=0.15):
    world = bpy.data.worlds.new("Space")
    bpy.context.scene.world = world
    world.use_nodes = True
    nt = world.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    bg = nt.nodes.new("ShaderNodeBackground")
    env = nt.nodes.new("ShaderNodeTexEnvironment")
    env.image = bpy.data.images.load(os.path.join(ASSETS, "starfield.jpg"))
    out = nt.nodes.new("ShaderNodeOutputWorld")
    bg.inputs["Strength"].default_value = strength
    nt.links.new(env.outputs["Color"], bg.inputs["Color"])
    nt.links.new(bg.outputs["Background"], out.inputs["Surface"])


def add_sun_aimed(shine_direction, side_offset_deg=32, strength=4.5):
    """A sun lamp whose light points roughly the way the camera is looking (so both the spacecraft's near
    face and Earth's near face are lit, not left as silhouettes), rotated `side_offset_deg` around the world
    Z axis off that direction for angled, more dramatic light instead of flat front lighting."""
    from mathutils import Vector, Matrix
    d = Vector(shine_direction).normalized()
    rot = Matrix.Rotation(math.radians(side_offset_deg), 4, "Z")
    d = (rot @ d.to_4d()).to_3d().normalized()
    bpy.ops.object.light_add(type="SUN", location=(0, 0, 0))
    sun = bpy.context.object
    sun.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    sun.data.energy = strength
    sun.data.angle = math.radians(0.55)
    return sun


def add_earth(location, radius):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=location, segments=96, ring_count=64)
    earth = bpy.context.object
    earth.name = "Earth"
    bpy.ops.object.shade_smooth()
    mat = bpy.data.materials.new("earth_mat")
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = bpy.data.images.load(os.path.join(ASSETS, "earth_bluemarble.jpg"))
    bsdf.inputs["Roughness"].default_value = 0.75
    if "Specular IOR Level" in bsdf.inputs:
        bsdf.inputs["Specular IOR Level"].default_value = 0.15
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    nt.links.new(bsdf.outputs["BSDF"], out.inputs["Surface"])
    earth.data.materials.append(mat)
    return earth


def look_at(obj, target):
    direction = (target - obj.location)
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_camera(location, target):
    bpy.ops.object.camera_add(location=location)
    cam = bpy.context.object
    from mathutils import Vector
    look_at(cam, Vector(target))
    cam.data.lens = 85
    cam.data.clip_start = 1.0
    cam.data.clip_end = 1_000_000.0  # default (1000) is far shorter than this scene's mm scale -- everything was being clipped away
    cam.data.dof.use_dof = False
    bpy.context.scene.camera = cam
    return cam


def configure_render(out_path, samples=256, resolution=(1920, 1280), use_gpu=True):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    scene.cycles.samples = samples
    scene.cycles.use_denoising = True
    scene.render.resolution_x = resolution[0]
    scene.render.resolution_y = resolution[1]
    scene.render.film_transparent = False
    scene.render.filepath = out_path
    try:
        scene.view_settings.view_transform = "AgX"
    except TypeError:
        scene.view_settings.view_transform = "Standard"
    if use_gpu:
        try:
            prefs = bpy.context.preferences.addons["cycles"].preferences
            prefs.compute_device_type = "OPTIX"
            prefs.get_devices()
            for d in prefs.devices:
                d.use = True
            scene.cycles.device = "GPU"
        except Exception as e:
            print("GPU setup failed, falling back to CPU:", e)
            scene.cycles.device = "CPU"


def main():
    argv = sys.argv
    args = argv[argv.index("--") + 1:] if "--" in argv else ["deployed"]
    cfg_name = args[0]
    obj_path = os.path.join(HERE, "out", f"wollemi_12u_{cfg_name}_textured.obj")

    fast = "--fast" in args
    clear_scene()
    import_obj(obj_path)
    apply_materials()

    # Artistic scale, not literal orbital geometry (like render_space.py's illustration): Earth is placed close
    # and small enough to frame reliably next to the ~340 mm spacecraft body, the same trade-off a wide-angle
    # "beauty shot" lens makes in real spacecraft photography.
    cam_dist = 2400 if cfg_name == "deployed" else 1600
    cam_loc = (cam_dist * 0.75, -cam_dist * 1.05, cam_dist * 0.55)
    cam_target = (0, 0, 170)
    cam = setup_camera(location=cam_loc, target=cam_target)
    cam.data.lens = 28

    from mathutils import Vector
    view_dir = (Vector(cam_target) - Vector(cam_loc)).normalized()
    world_up = Vector((0, 0, 1))
    cam_right = view_dir.cross(world_up).normalized()
    cam_up = cam_right.cross(view_dir).normalized()
    # Earth in the lower-left of frame, well off the direct camera-to-spacecraft axis (composing it there,
    # rather than along the view axis, is what avoids it looking like it is overlapping/behind the spacecraft).
    earth_center = (Vector(cam_target) + view_dir * 9000 - cam_right * 4500 - cam_up * 3200)
    add_earth(location=tuple(earth_center), radius=5200)
    add_starfield()
    add_sun_aimed(view_dir, side_offset_deg=30, strength=4.5)

    os.makedirs(OUT, exist_ok=True)
    out_path = os.path.join(OUT, f"blender_{cfg_name}.png")
    if fast:
        configure_render(out_path, samples=24, resolution=(800, 533))
    else:
        configure_render(out_path, samples=256, resolution=(1920, 1280))
    bpy.ops.render.render(write_still=True)
    print("Wrote", out_path)


if __name__ == "__main__":
    main()
