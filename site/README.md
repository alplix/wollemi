# Wollemi project website (draft, English)

A single self-contained static page (`index.html` + `assets/img/`) introducing the mission, gallery renders and
deployment animation, in English, for eventual public release.

**Status: prepared, not published.** The repository is still private (`README.md`, `docs/licensing.md`); this
page is not deployed anywhere and GitHub Pages is not enabled. It sits in the repository so it is ready to
publish once the operator decides to open the design to the public.

## Regenerating the images

All images in `assets/img/` are copies of `mechanical/out/gallery/*`, from three generators, all built on
`mechanical/wollemi_cad.py` (the real parametric CAD model):

- `mechanical/render_gallery.py`: technical views, exploded view, three-view drawing, GIFs -- flat per-part
  colours, for engineering clarity.
- `mechanical/render_space.py`: quick "in orbit" illustrations using this project's own lightweight rasteriser,
  with a solar-cell grid and gold MLI foil texture painted on afterwards -- fast, no extra tools needed, but
  the shading is not physically simulated.
- `mechanical/render_blender.py` (needs a separate Blender install, see below): the same CAD geometry rendered
  by a real path tracer (Cycles) with proper PBR materials, a real NASA Earth photograph and simulated
  lighting -- the photorealistic `blender_*.jpg` images. This is the one to use when the goal is "look like a
  real satellite photo", not a technical or schematic illustration.

After changing the CAD model or the geometry configs, regenerate and re-copy:

```
python mechanical/pack.py
python mechanical/render_gallery.py
python mechanical/render_space.py
cp mechanical/out/gallery/*.png mechanical/out/gallery/*.gif site/assets/img/
```

To regenerate the photorealistic renders, a Blender install is needed (tested with Blender 5.2 LTS; a GPU with
Cycles/OptiX support renders in seconds, CPU-only still works but is slower):

```
python mechanical/export_obj.py deployed
python mechanical/export_obj.py stowed
"<path to blender.exe>" --background --factory-startup --python mechanical/render_blender.py -- deployed
"<path to blender.exe>" --background --factory-startup --python mechanical/render_blender.py -- stowed
python -c "from PIL import Image; [Image.open(f'mechanical/out/gallery/blender_{n}.png').convert('RGB').save(f'site/assets/img/blender_{n}.jpg', quality=90, optimize=True) for n in ('deployed','stowed')]"
```

Pass `-- deployed --fast` for a quick low-sample preview (a few seconds) while tuning the camera/Earth/sun
placement in `render_blender.py`, then drop `--fast` for the final 256-sample render.

## Viewing locally

Open `index.html` directly in a browser, or serve the folder so relative paths resolve the same way they would
on a real host:

```
python -m http.server 8000 --directory site
```

## Publishing later

When the operator decides to make the repository public: enable GitHub Pages for this `site/` directory (or copy
it to a `gh-pages` branch), review `docs/licensing.md` first, and see `docs/decisions/` for anything else that
should be resolved before the public link goes out.
