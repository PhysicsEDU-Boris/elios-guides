// ELIOS Guides fill script. Run with the Figma use_figma tool on file pBZAnlSJnLGB5Je0tCth12.
// Replace __CONTENT__ with the parsed en.json or id.json object. Idempotent: an issue frame with the
// same name is replaced.
const CONTENT = __CONTENT__;
const LANG = CONTENT['guide.lang'];
const PAGE_ID = '23:170';
const TEMPLATES = ['24:170', '25:221', '26:230', '27:248'];
const page = await figma.getNodeByIdAsync(PAGE_ID);
await figma.setCurrentPageAsync(page);
for (const st of ['Regular', 'Medium', 'SemiBold', 'Bold', 'Black']) await figma.loadFontAsync({ family: 'Google Sans Flex', style: st });
for (const st of ['Regular', 'Medium', 'SemiBold']) await figma.loadFontAsync({ family: 'Google Sans Code', style: st });

const name = `Issue ${CONTENT._issue} · ${LANG} · ${CONTENT._slug}`;
for (const old of page.children.filter(n => n.name === name)) old.remove();
const issues = page.children.filter(n => n.name.startsWith('Issue '));
const Y = issues.length ? Math.max(...issues.map(n => n.y + n.height)) + 108 : 1000;

const wrap = figma.createAutoLayout('HORIZONTAL');
wrap.name = name; wrap.itemSpacing = 48; wrap.fills = []; wrap.x = 0; wrap.y = Y;
const pages = [];
for (const id of TEMPLATES) {
  const comp = await figma.getNodeByIdAsync(id);
  const inst = comp.createInstance();
  wrap.appendChild(inst);
  const f = inst.detachInstance();
  f.name = `${LANG} / ${comp.name.replace('Template / ', '')}`;
  pages.push(f);
}
const byName = (p, k) => p.findAll(n => n.type === 'TEXT' && n.name === k);

const missing = [];
for (const [k, v] of Object.entries(CONTENT)) {
  if (k.startsWith('_')) continue;
  let hit = 0;
  for (const p of pages) for (const t of byName(p, k)) {
    if (v === '' || v === null) t.visible = false; else t.characters = String(v);
    hit++;
  }
  if (!hit) missing.push(k);
}
(CONTENT._per_page || []).forEach((m, i) => {
  for (const [k, v] of Object.entries(m || {})) for (const t of byName(pages[i], k)) t.characters = String(v);
});
for (const [layer, pairs] of Object.entries(CONTENT._replace || {})) {
  for (const p of pages) for (const t of byName(p, layer)) for (const [a, b] of pairs) t.characters = t.characters.replace(a, b);
}
// hide empty legend rows
for (let i = 1; i <= 5; i++) {
  if ((CONTENT[`legend.${i}.meaning`] ?? '') === '') {
    const row = pages[2].findOne(n => n.name === `Legend row ${i}`);
    if (row) row.visible = false;
  }
}
// graph bars: width = raw / max × 170, min 3
const raw = [1, 2, 3].map(i => Number(CONTENT[`_graph.${i}.raw`]));
if (raw.every(x => Number.isFinite(x) && x >= 0)) {
  const mx = Math.max(...raw) || 1;
  raw.forEach((x, i) => pages[2].findOne(n => n.name === `graph.${i + 1}.bar`).resize(Math.max(3, Math.round(x / mx * 170)), 12));
}
pages[3].findOne(n => n.name === 'xp.fill').resize(6, 8);

// image slots
const imgs = CONTENT._images || {};
const slots = {};
for (const [pi, key] of [[0, 'cover.image'], [1, 'story.image'], [2, 'physics.diagram']]) {
  const fr = pages[pi].findOne(n => n.name === key);
  if (imgs[key]) { slots[key] = fr.id; continue; }       // the Claude task uploads the photo here
  if (key === 'physics.diagram') { fr.visible = false; continue; }
  // no licensed photo: soft placeholder scene, hint hidden
  fr.findOne(n => n.name === 'image.hint').visible = false;
  fr.strokes = []; fr.clipsContent = true;
  const w = Math.round(fr.width), h = Math.round(fr.height);
  const svg = `<svg width="${w}" height="${h}" viewBox="0 0 ${w} ${h}" xmlns="http://www.w3.org/2000/svg"><defs><linearGradient id="g" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#CFFAFE"/><stop offset="0.75" stop-color="#F1F5F9"/></linearGradient></defs><rect width="${w}" height="${h}" fill="url(#g)"/><circle cx="${w * 0.75}" cy="${h * 0.3}" r="${h * 0.13}" fill="#FBBF24" fill-opacity="0.8"/><ellipse cx="${w * 0.5}" cy="${h * 1.05}" rx="${w * 0.7}" ry="${h * 0.3}" fill="#4ADE80"/><ellipse cx="${w * 0.1}" cy="${h}" rx="${w * 0.3}" ry="${h * 0.22}" fill="#15803D"/></svg>`;
  const s = figma.createNodeFromSvg(svg);
  s.name = 'placeholder illustration';
  fr.appendChild(s); s.layoutPositioning = 'ABSOLUTE'; s.x = 0; s.y = 0;
}

// checks
const fit = pages.map(p => {
  const b = p.findOne(n => n.name === 'Body');
  const kids = b.children.filter(c => c.visible);
  const sum = kids.reduce((a, c) => a + c.height, 0) + b.itemSpacing * (kids.length - 1);
  return { page: p.name, used: Math.round(sum), max: Math.round(b.height), ok: sum <= b.height };
});
const leftover = pages.flatMap(p => p.findAll(n => n.type === 'TEXT' && n.visible && /[{}]/.test(n.characters)).map(t => p.name + ' › ' + t.name));
return { wrapper: wrap.id, pages: pages.map(p => p.id), slots, missing, fit, leftover };
