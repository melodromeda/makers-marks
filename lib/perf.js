// Keeps the 3D smooth on any machine: watches the frame rate and lowers the
// render resolution when frames get slow (big desktop screens, integrated GPUs).
// If it is already at the lowest resolution and still slow, it calls onStruggle().
// Add ?fps to any page address to see the frame rate and current resolution.
export function autoQuality(renderer, opts = {}) {
  const max = opts.max ?? Math.min(devicePixelRatio || 1, 1.5);
  const min = opts.min ?? 0.5;
  let scale = max, ceiling = max, last = 0, acc = 0, n = 0, good = 0, start = 0;
  renderer.setPixelRatio(scale);
  let hud = null;
  if (new URLSearchParams(location.search).has('fps')) {
    hud = document.createElement('div');
    hud.style.cssText = 'position:fixed;right:8px;top:8px;z-index:99;font:12px ui-monospace,monospace;color:#9f9;background:#000a;padding:4px 6px;pointer-events:none';
    document.body.appendChild(hud);
  }
  const set = s => { scale = s; renderer.setPixelRatio(s); };
  return function tick(now) {
    if (!start) start = now;
    if (now - start < (opts.warmup ?? 1500)) { last = now; return; }   // first frames upload textures: don't judge them
    if (last) { const dt = now - last; if (dt < 4000) { acc += dt; n++; } }   // ignore tab switches
    last = now;
    if (n < 40 && !(n >= 4 && acc > 800)) return;      // decide fast when frames are very slow
    const avg = acc / n; acc = 0; n = 0;
    if (hud) hud.textContent = `${Math.round(1000 / avg)} fps · res ${scale.toFixed(2)}${opts.info ? ' · ' + opts.info() : ''}`;
    if (avg > 24) {                       // slower than ~40 fps
      good = 0;
      if (scale > min + 0.01) { ceiling = Math.min(ceiling, scale * 0.95); set(Math.max(min, scale * Math.min(0.8, Math.max(0.5, Math.sqrt(20 / avg))))); }
      else if (opts.onStruggle) opts.onStruggle();
    } else if (avg < 19 && ++good >= 3 && scale < ceiling - 0.01) {
      good = 0; set(Math.min(ceiling, scale * 1.15));
    }
  };
}
