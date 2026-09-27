// Interactive 3D viewer for the Wollemi CAD model (site/assets/model/*.obj + .mtl -- real
// output of mechanical/export_obj.py, the same parametric model the mass/interference checks run
// against, not a stand-in). Drag to orbit, scroll/pinch to zoom, toggle deployed/stowed.
// Pinned to a pre-import-map three.js release: these examples/jsm files import three.module.js by
// relative path rather than the bare "three" specifier newer releases use, so this works as plain
// CDN <script type="module"> imports with no import-map (and no inline script, which the CSP disallows).
import * as THREE from "https://cdn.jsdelivr.net/npm/three@0.118.3/build/three.module.js";
import { OrbitControls } from "https://cdn.jsdelivr.net/npm/three@0.118.3/examples/jsm/controls/OrbitControls.js";
import { MTLLoader } from "https://cdn.jsdelivr.net/npm/three@0.118.3/examples/jsm/loaders/MTLLoader.js";
import { OBJLoader } from "https://cdn.jsdelivr.net/npm/three@0.118.3/examples/jsm/loaders/OBJLoader.js";

function initViewer(mount) {
  const width = () => mount.clientWidth;
  const height = () => mount.clientHeight;

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(40, width() / height(), 1, 5000);
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true });
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.setSize(width(), height());
  mount.appendChild(renderer.domElement);

  scene.add(new THREE.AmbientLight(0xffffff, 0.55));
  const key = new THREE.DirectionalLight(0xffffff, 1.4);
  key.position.set(400, 600, 500);
  scene.add(key);
  const rim = new THREE.DirectionalLight(0x8aa0ff, 0.6);
  rim.position.set(-500, -200, -300);
  scene.add(rim);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.08;
  controls.autoRotate = true;
  controls.autoRotateSpeed = 1.4;
  controls.minDistance = 100;
  controls.maxDistance = 3000;
  controls.enableZoom = false; // off until the visitor actually clicks in, so an idle mouse-wheel over the
  // canvas still scrolls the page instead of zooming the model (OrbitControls otherwise captures every
  // wheel event that lands on the canvas, even ones meant for the page).

  let current = null;

  function frame(object) {
    const box = new THREE.Box3().setFromObject(object);
    const size = box.getSize(new THREE.Vector3());
    const center = box.getCenter(new THREE.Vector3());
    object.position.sub(center);
    const radius = Math.max(size.x, size.y, size.z) * 0.62;
    camera.position.set(radius * 1.3, radius * 0.9, radius * 1.5);
    controls.target.set(0, 0, 0);
    controls.update();
  }

  function load(base) {
    new MTLLoader().load(`assets/model/${base}.mtl`, (materials) => {
      materials.preload();
      new OBJLoader().setMaterials(materials).load(`assets/model/${base}.obj`, (obj) => {
        if (current) scene.remove(current);
        // export_obj.py's OBJ has no vn (vertex normal) data, and this three.js version's OBJLoader
        // doesn't compute normals when they're missing -- without this the lit material has nothing to
        // shade against and every face renders flat black regardless of the lights in the scene.
        obj.traverse((child) => { if (child.isMesh) child.geometry.computeVertexNormals(); });
        // export_obj.py writes Z-up, X/Y in mm centred on the spine -- rotate so Z (long axis) reads as up on screen.
        obj.rotation.x = -Math.PI / 2.4;
        obj.rotation.z = Math.PI / 6;
        scene.add(obj);
        current = obj;
        frame(obj);
        mount.classList.add("ready");
      });
    });
  }

  function onResize() {
    camera.aspect = width() / height();
    camera.updateProjectionMatrix();
    renderer.setSize(width(), height());
  }
  window.addEventListener("resize", onResize);

  (function animate() {
    requestAnimationFrame(animate);
    controls.update();
    renderer.render(scene, camera);
  })();

  return { load, activate: () => { controls.autoRotate = false; controls.enableZoom = true; } };
}

document.querySelectorAll("[data-wollemi-viewer]").forEach((mount) => {
  const viewer = initViewer(mount);
  let state = mount.getAttribute("data-initial") || "deployed";
  viewer.load(state === "stowed" ? "wollemi_stowed" : "wollemi_deployed");
  mount.addEventListener("pointerdown", () => viewer.activate(), { once: true });

  const toggle = document.querySelector(`[data-wollemi-toggle="${mount.id}"]`);
  if (toggle) {
    toggle.addEventListener("click", (e) => {
      const btn = e.target.closest("button[data-state]");
      if (!btn) return;
      state = btn.getAttribute("data-state");
      toggle.querySelectorAll("button").forEach((b) => b.classList.toggle("on", b === btn));
      viewer.load(state === "stowed" ? "wollemi_stowed" : "wollemi_deployed");
    });
  }
});

// Scroll-reveal: fade/slide sections and figures into place the first time they cross the viewport.
// Pure CSS-transition based (no animation library); .reveal starts hidden via CSS, .in class runs it.
const revealTargets = document.querySelectorAll(".reveal");
if ("IntersectionObserver" in window && revealTargets.length) {
  const io = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (entry.isIntersecting) {
        entry.target.classList.add("in");
        io.unobserve(entry.target);
      }
    });
  }, { threshold: 0.12, rootMargin: "0px 0px -40px 0px" });
  revealTargets.forEach((el) => io.observe(el));
} else {
  revealTargets.forEach((el) => el.classList.add("in"));
}

// Count-up stat numbers once their badge scrolls into view.
const counters = document.querySelectorAll("[data-count]");
if ("IntersectionObserver" in window && counters.length) {
  const io2 = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      io2.unobserve(entry.target);
      const el = entry.target;
      const target = parseFloat(el.getAttribute("data-count"));
      const suffix = el.getAttribute("data-suffix") || "";
      const decimals = el.getAttribute("data-decimals") ? parseInt(el.getAttribute("data-decimals"), 10) : 0;
      const start = performance.now();
      const dur = 1200;
      function tick(now) {
        const p = Math.min(1, (now - start) / dur);
        const eased = 1 - Math.pow(1 - p, 3);
        el.textContent = (target * eased).toFixed(decimals) + suffix;
        if (p < 1) requestAnimationFrame(tick);
      }
      requestAnimationFrame(tick);
    });
  }, { threshold: 0.4 });
  counters.forEach((el) => io2.observe(el));
}
