// Fills render/guide.html from one language file. Port of the old figma/fill.js: a text element's
// data-key is the JSON key it shows; empty values hide it. Returns problems for the caller to fail on.
async ({ content: C, images: IMG, mascot, latex, theme }) => {
  await Promise.all([...document.fonts].map(f => f.load())); // KaTeX fonts load lazily; measure with the real ones
  const THEME_BG = { water: 'linear-gradient(135deg,#CFFAFE,#67E8F9)', heat: 'linear-gradient(135deg,#FEF3C7,#FCA5A5)', air: 'linear-gradient(135deg,#E0F2FE,#A5B4FC)',
    energy: 'linear-gradient(135deg,#FEF9C3,#FBBF24)', waste: 'linear-gradient(135deg,#DCFCE7,#86EFAC)', storm: 'linear-gradient(135deg,#E2E8F0,#94A3B8)' };
  const pages = [...document.querySelectorAll('.page')];
  const $$ = (root, k) => [...root.querySelectorAll(`[data-key="${k}"]`)];
  const hide = e => { e.style.display = 'none'; };
  const missing = [];
  for (const [k, v] of Object.entries(C)) {
    if (k.startsWith('_')) continue;
    const hits = pages.flatMap(p => $$(p, k));
    for (const e of hits) { if (v === '' || v === null) hide(e); else e.textContent = String(v); }
    if (!hits.length) missing.push(k);
  }
  (C._per_page || []).forEach((m, i) => {
    for (const [k, v] of Object.entries(m || {})) $$(pages[i], k).forEach(e => { e.textContent = String(v); });
  });
  for (const [layer, pairs] of Object.entries(C._replace || {}))
    for (const p of pages) $$(p, layer).forEach(e => { for (const [a, b] of pairs) e.textContent = e.textContent.replace(a, b); });
  for (let i = 1; i <= 5; i++)
    if ((C[`legend.${i}.meaning`] ?? '') === '') pages[2].querySelectorAll(`[data-row="legend.${i}"]`).forEach(hide);
  const raw = [1, 2, 3].map(i => Number(C[`_graph.${i}.raw`]));
  if (raw.every(x => Number.isFinite(x) && x >= 0)) {
    const mx = Math.max(...raw) || 1; // bar width = raw / max x 170, at least 3 px
    raw.forEach((x, i) => { $$(pages[2], `graph.${i + 1}.bar`)[0].style.width = Math.max(3, Math.round(x / mx * 170)) + 'px'; });
  }
  document.getElementById('mascot').src = `assets/${mascot}.svg`;
  for (const [key, pi] of Object.entries({ 'cover.image': 0, 'story.image': 1, 'physics.diagram': 2 })) {
    const slot = pages[pi].querySelector(`[data-slot="${key}"]`);
    slot.querySelector('[data-hint]').remove();
    slot.style.border = 'none';
    if (IMG[key]) { const im = document.createElement('img'); im.src = IMG[key]; slot.append(im); continue; }
    if (key === 'physics.diagram') { hide(slot); continue; }
    if (key === 'cover.image' && latex) { // no photo: a cover made from this issue's own equation
      slot.style.background = THEME_BG[theme] || THEME_BG.water;
      const box = document.createElement('div');
      box.style.cssText = 'position:absolute;inset:0;display:flex;align-items:center;justify-content:center;padding:0 12px';
      const eqEl = document.createElement('span');
      box.append(eqEl); slot.append(box);
      katex.render(latex, eqEl, { throwOnError: true });
      eqEl.style.flex = 'none';
      eqEl.querySelector('.katex-html').style.whiteSpace = 'nowrap'; // KaTeX may break after "=", we shrink instead
      let size = 34;
      eqEl.style.fontSize = size + 'px';
      while (eqEl.getBoundingClientRect().width > 238 && size > 14) eqEl.style.fontSize = (--size) + 'px';
      $$(pages[0], 'cover.image_caption').forEach(e => { e.textContent = `${C['guide.lang'] === 'ID' ? 'Ilustrasi ELIOS' : 'ELIOS illustration'} · ${C['physics.equation_name']}`; });
      continue;
    }
    const { width: w, height: h } = slot.getBoundingClientRect(); // no photo and no formula (old issue): soft scene
    slot.insertAdjacentHTML('beforeend', `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg" style="position:absolute;inset:0"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#CFFAFE"/><stop offset="0.75" stop-color="#F1F5F9"/></linearGradient></defs><rect width="${w}" height="${h}" fill="url(#g)"/><circle cx="${w * 0.75}" cy="${h * 0.3}" r="${h * 0.13}" fill="#FBBF24" fill-opacity="0.8"/><ellipse cx="${w * 0.5}" cy="${h * 1.05}" rx="${w * 0.7}" ry="${h * 0.3}" fill="#4ADE80"/><ellipse cx="${w * 0.1}" cy="${h}" rx="${w * 0.3}" ry="${h * 0.22}" fill="#15803D"/></svg>`);
  }
  const eq = { ok: true };
  if (latex) { // typeset with KaTeX, shrink to the card width, never clip
    const el = $$(pages[2], 'physics.equation')[0];
    katex.render(latex, el, { throwOnError: true });
    let size = 24;
    el.style.fontSize = size + 'px';
    while (el.scrollWidth > el.clientWidth && size > 13) el.style.fontSize = (--size) + 'px';
    eq.ok = el.scrollWidth <= el.clientWidth;
  }
  const fit = pages.map((p, i) => { const b = p.querySelector('.body'); return { page: i + 1, used: b.scrollHeight, max: b.clientHeight, ok: b.scrollHeight <= b.clientHeight }; });
  const leftover = [...document.querySelectorAll('[data-key]')].filter(e => e.getClientRects().length && /[{}]/.test((e.querySelector('.katex-html') || e).textContent)).map(e => e.dataset.key);
  return { missing, fit, leftover, eq };
}
