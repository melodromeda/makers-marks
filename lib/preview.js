// Lightweight 3D previews for the gallery grid.
// Layers paintings: ~24 evenly spaced layers, shrunk to 160 px in the browser.
// Skin paintings: every Nth frame of the recording, full shape.
import * as THREE from './three.module.min.js';

const PREVIEW_LAYERS = 24;
const PREVIEW_PX = 160;
const bust = () => '?v=' + Date.now();

export async function buildPreview(entry) {
  const base = `paintings/${entry.id}/`;
  return entry.kind === 'layers' ? buildLayers(base) : buildSkin(base);
}

// ---------------- layers ----------------
const vert = `varying vec2 vUv; void main(){ vUv=uv; gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0); }`;
const frag = `
  uniform sampler2D map; uniform float opacity, threshold, softness; uniform int keyMode;
  varying vec2 vUv;
  void main(){
    vec4 c = texture2D(map, vUv);
    float a = c.a;
    if (keyMode == 1) { float l = max(c.r, max(c.g, c.b)); a *= smoothstep(threshold, threshold + softness, l); }
    if (keyMode == 2) a = 1.0;
    a *= opacity;
    if (a < 0.004) discard;
    gl_FragColor = vec4(c.rgb, a);
  }`;

function loadSmall(url) {
  return new Promise(res => {
    const img = new Image();
    img.onload = () => {
      const s = Math.min(1, PREVIEW_PX / Math.max(img.width, img.height));
      const c = document.createElement('canvas');
      c.width = Math.max(1, Math.round(img.width * s)); c.height = Math.max(1, Math.round(img.height * s));
      c.getContext('2d').drawImage(img, 0, 0, c.width, c.height);
      res(c);
    };
    img.onerror = () => res(null);
    img.src = url;
  });
}

async function buildLayers(base) {
  const m = await (await fetch(base + 'manifest.json' + bust())).json();
  const S = { depth: 1.2, key: 'luminance', threshold: 0.06, softness: 0.15, opacity: 0.35, blending: 'additive', reverse: false, ...m };
  const n = S.files.length;
  const k = Math.min(PREVIEW_LAYERS, n);
  const pick = Array.from({ length: k }, (_, i) => S.files[Math.round(i * (n - 1) / Math.max(1, k - 1))]);
  const canvases = await Promise.all(pick.map(f => loadSmall(base + f)));
  // fewer layers than the full painting: raise opacity so the overall density matches
  const opacity = Math.min(1, 1 - Math.pow(1 - S.opacity, n / k));
  const keyMode = { alpha: 0, luminance: 1, none: 2 }[S.key] ?? 1;
  const first = canvases.find(Boolean);
  const aspect = first ? first.width / first.height : 1;
  const w = aspect >= 1 ? 1 : aspect, h = aspect >= 1 ? 1 / aspect : 1;
  const geo = new THREE.PlaneGeometry(w, h);
  const group = new THREE.Group();
  canvases.forEach((c, i) => {
    if (!c) return;
    const tex = new THREE.CanvasTexture(c); tex.colorSpace = THREE.NoColorSpace;
    const mat = new THREE.ShaderMaterial({
      uniforms: { map: { value: tex }, opacity: { value: opacity }, threshold: { value: S.threshold }, softness: { value: S.softness }, keyMode: { value: keyMode } },
      vertexShader: vert, fragmentShader: frag, transparent: true, depthWrite: false, side: THREE.DoubleSide,
      blending: S.blending === 'normal' ? THREE.NormalBlending : THREE.AdditiveBlending
    });
    const mesh = new THREE.Mesh(geo, mat);
    const f = k > 1 ? i / (k - 1) : 0.5;
    mesh.position.z = (S.reverse ? f - 0.5 : 0.5 - f) * S.depth;
    group.add(mesh);
  });
  const radius = Math.hypot(w / 2, h / 2, S.depth / 2);
  return { object: group, radius, lit: false };
}

// ---------------- skin ----------------
async function buildSkin(base) {
  const H = await (await fetch(base + 'skin.json' + bust())).json();
  const buf = await (await fetch(base + 'skin.bin' + bust())).arrayBuffer();
  const { circles: C, points: P } = H;
  const pos = new Float32Array(buf, 0, H.frames * C * P * 3);
  const col = new Float32Array(buf, H.frames * C * P * 3 * 4, H.frames * C * 3);
  const every = Math.max(1, Math.ceil(H.frames / 90));
  const frames = []; for (let f = 0; f < H.frames; f += every) frames.push(f);
  const F = frames.length;
  const at = (f, c, p) => ((f * C + c) * P + p) * 3;

  const box = new THREE.Box3(), v = new THREE.Vector3();
  for (let i = 0; i < pos.length; i += 3) box.expandByPoint(v.set(pos[i], pos[i + 1], pos[i + 2]));
  const size = box.getSize(new THREE.Vector3());
  const span = Math.max(size.x, size.y, size.z) || 1;
  const depth = size.z < span * 0.05 ? span * 1.2 : 0;

  const group = new THREE.Group();
  const mat = new THREE.MeshStandardMaterial({ vertexColors: true, side: THREE.DoubleSide, roughness: 0.45, metalness: 0.1 });
  for (let c = 0; c < C; c++) {
    const vp = new Float32Array(F * P * 3), vc = new Float32Array(F * P * 3), centers = [];
    frames.forEach((f, fi) => {
      const z = F > 1 ? (fi / (F - 1) - 0.5) * depth : 0;
      let cx = 0, cy = 0, cz = 0;
      for (let p = 0; p < P; p++) {
        const s = at(f, c, p), d = (fi * P + p) * 3;
        vp[d] = pos[s]; vp[d + 1] = pos[s + 1]; vp[d + 2] = pos[s + 2] + z;
        const ci = (f * C + c) * 3; vc[d] = col[ci]; vc[d + 1] = col[ci + 1]; vc[d + 2] = col[ci + 2];
        cx += pos[s]; cy += pos[s + 1]; cz += pos[s + 2];
      }
      centers.push(new THREE.Vector3(cx / P, cy / P, cz / P));
    });
    const idx = [];
    for (let fi = 0; fi < F - 1; fi++) {
      if (centers[fi].distanceTo(centers[fi + 1]) > 0.25 * span * every) continue;
      for (let p = 0; p < P; p++) { const a = fi * P + p, b = fi * P + (p + 1) % P; idx.push(a, a + P, b, b, a + P, b + P); }
    }
    const g = new THREE.BufferGeometry();
    g.setAttribute('position', new THREE.BufferAttribute(vp, 3));
    g.setAttribute('color', new THREE.BufferAttribute(vc, 3));
    g.setIndex(idx); g.computeVertexNormals();
    group.add(new THREE.Mesh(g, mat));
  }
  const sph = new THREE.Box3().setFromObject(group).getBoundingSphere(new THREE.Sphere());
  group.children.forEach(m => m.position.sub(sph.center));
  return { object: group, radius: sph.radius, lit: true };
}
