// ELIOS Question Insights: reads question_stats() from Supabase (allow-listed login) and the published guides.
// Guide text is always inserted as text, never as HTML.
const MIN_CONCEPT = 60; // answers per concept before the remedial guide picks it (same as scripts/weak_questions.py)
const LETTERS = ["a", "b", "c", "d"];
const QUIZ = { a: "--q-red", b: "--q-blue", c: "--q-yellow", d: "--q-green" };

function conceptOf(en) {
  return { key: en._formula || en["physics.equation"] || "?", name: en["physics.equation_name"] || en["physics.equation"] || "?" };
}

// Question text, options and correct letter for p1-p3 (printed) or pool-N (0-based retry pool), the app's ids;
// null when it cannot be found.
function questionOf(en, qid) {
  try {
    const printed = /^p([1-3])$/.exec(qid);
    if (printed) {
      const n = printed[1];
      return { text: en[`quiz.${n}.question`], options: LETTERS.map(l => en[`quiz.${n}.${l}`]), correct: String(en._answers[n]).toLowerCase() };
    }
    const q = en._quiz_pool[Number(/^pool-(\d{1,2})$/.exec(qid)[1])];
    return { text: q.question, options: q.options, correct: LETTERS[q.answer] };
  } catch { return null; }
}

function groupConcepts(rows, docs) {
  const g = {};
  for (const r of rows) {
    const en = docs[r.guide_date];
    if (!en || !questionOf(en, r.question_id)) continue;
    const c = conceptOf(en);
    const x = (g[c.key] ||= { name: c.name, attempts: 0, wrong: 0, questions: 0 });
    x.attempts += r.attempts; x.wrong += r.wrong; x.questions += 1;
  }
  return Object.values(g).map(x => ({ ...x, rate: x.wrong / x.attempts })).sort((a, b) => b.rate - a.rate);
}

const $ = id => document.getElementById(id);
function h(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  Object.assign(e, props.props || {});
  if (props.class) e.className = props.class;
  if (props.style) e.style.cssText = props.style;
  for (const [k, v] of Object.entries(props.attrs || {})) e.setAttribute(k, v);
  e.append(...kids.flat().filter(k => k != null));
  return e;
}
const img = (src, w) => h("img", { attrs: { src: `assets/${src}.svg`, alt: "" }, style: w ? `width:${w}px` : "" });
const pct = x => `${Math.round(x * 100)}%`;
const tone = rate => (rate >= 0.6 ? "coral" : rate >= 0.3 ? "sun" : "green");
const toneLabel = rate => (rate >= 0.6 ? "Tough" : rate >= 0.3 ? "Tricky" : "Easy");
const qLabel = qid => (/^p(\d)$/.exec(qid) ? qid.toUpperCase() : `R${qid.replace(/\D/g, "")}`);
const chip = (t, label) => h("span", { class: `chip ${t}` }, label);
function blob(parent, x, y, size, color, opacity) {
  parent.append(h("span", { class: "blob", style: `left:${x}px;top:${y}px;width:${size}px;height:${size}px;background:var(${color});opacity:${opacity}` }));
}

// remedial days are the even date ordinals (Python's date.toordinal; 1970-01-01 is 719163)
const ordinal = d => Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 86400000) + 719163;
function nextRemedialDays(n, from = new Date()) {
  const out = [];
  for (let i = 0; out.length < n; i++) { const d = new Date(from.getFullYear(), from.getMonth(), from.getDate() + i); if (ordinal(d) % 2 === 0) out.push(d); }
  return out;
}

const state = { days: 30, filter: "all", rows: [], docs: {}, client: null };

function show(view) {
  for (const id of ["login", "sent", "denied", "app"]) $(id).hidden = id !== view;
  $("topbar").hidden = view !== "app";
}

function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  $("theme").textContent = t === "dark" ? "Light mode" : "Dark mode";
  try { localStorage.setItem("elios-theme", t); } catch { /* private window: keep it for this visit only */ }
}

function renderHero(concepts, totals) {
  const hero = $("hero"); hero.replaceChildren();
  blob(hero, -120, -140, 200, "--sky", 0.5); blob(hero, 740, 150, 170, "--sun", 0.55); blob(hero, 610, -90, 120, "--green", 0.4);
  const top = concepts[0];
  const ready = top && top.attempts >= MIN_CONCEPT;
  const sub = top
    ? `${pct(top.rate)} of answers were wrong. ` + (ready ? "A remedial guide is ready for the next remedial day." : `${MIN_CONCEPT - top.attempts} more answers unlock a remedial guide.`)
    : `${pct(totals.wrong / totals.attempts)} of the first-try answers were wrong.`;
  const fillPct = top ? Math.min(1, top.attempts / MIN_CONCEPT) : 0;
  hero.append(
    h("div", { class: "text" },
      h("div", { class: "overline" }, "Mission control"),
      h("h2", { class: "headline" }, top ? `${top.name} is the toughest topic right now` : "Here is how students are doing"),
      h("p", { class: "tx2" }, sub),
      top ? h("div", { class: "xp" }, h("div", { class: "track" }, h("div", { class: "fill", style: `width:${fillPct * 100}%` })),
        h("span", {}, `${Math.min(top.attempts, MIN_CONCEPT)} / ${MIN_CONCEPT} answers${ready ? ": unlocked!" : ""}`)) : null,
      h("div", { class: "actions" },
        h("button", { class: "btn", props: { type: "button", onclick: () => $("qhead").scrollIntoView() } }, "See the questions"),
        h("button", { class: "btn secondary", props: { type: "button", onclick: () => { $("how").hidden = !$("how").hidden; } } }, "How it works"))),
    h("div", { class: "mascot" }, h("div", { class: "bubble" }, "Let’s fix this together!"), img("bulb")));
}

function renderTiles(concepts, totals, count) {
  const top = concepts[0];
  const defs = [["sky", "Answers", totals.attempts.toLocaleString("en"), "first tries only", "quest"],
    ["green", "Questions", String(count), "with enough answers", "medal"],
    ["sun", "Right first try", pct(1 - totals.wrong / totals.attempts), "of all answers", "flame"],
    ["coral", "Toughest", top ? pct(top.rate) : "-", top ? `wrong: ${top.name}` : "no concept yet", "mascot-binb"]];
  $("tiles").replaceChildren(...defs.map(([t, label, num, cap, icon]) => h("div", { class: `tile ${t}` },
    h("div", { class: "top" }, h("span", { class: "overline" }, label), img(icon)), h("div", { class: "num" }, num), h("div", { class: "cap" }, cap))));
}

function renderFilters(rows) {
  const counts = { all: rows.length, Tough: 0, Tricky: 0, Easy: 0 };
  for (const r of rows) counts[toneLabel(Number(r.wrong_rate))]++;
  const defs = [["all", "All", "ink"], ["Tough", "Tough", "coral"], ["Tricky", "Tricky", "sun"], ["Easy", "Easy", "green"]];
  $("filters").replaceChildren(...defs.map(([key, label, t]) => h("button", { class: `chip ${t}`, attrs: { "aria-pressed": String(state.filter === key) },
    props: { type: "button", onclick: () => { state.filter = key; renderFilters(rows); renderQuestions(); } } }, `${label} ${counts[key]}`)));
}

const chevron = () => { const s = document.createElementNS("http://www.w3.org/2000/svg", "svg"); s.setAttribute("width", "16"); s.setAttribute("height", "16"); s.setAttribute("viewBox", "0 0 16 16");
  const p = document.createElementNS("http://www.w3.org/2000/svg", "path"); p.setAttribute("d", "M3 6l5 5 5-5"); p.setAttribute("fill", "none"); p.setAttribute("stroke", "currentColor");
  p.setAttribute("stroke-width", "2"); p.setAttribute("stroke-linecap", "round"); p.setAttribute("stroke-linejoin", "round"); s.append(p); return s; };

function renderQuestions() {
  const cards = [];
  const rows = [...state.rows].sort((a, b) => Number(b.wrong_rate) - Number(a.wrong_rate));
  for (const r of rows) {
    const rate = Number(r.wrong_rate);
    if (state.filter !== "all" && toneLabel(rate) !== state.filter) continue;
    const en = state.docs[r.guide_date], q = en && questionOf(en, r.question_id);
    if (!q) continue;
    const counts = LETTERS.map(l => r[`chosen_${l}`]);
    const hasChoices = counts.some(n => n > 0);
    const topWrong = r.top_wrong && r.top_wrong !== q.correct ? r.top_wrong : null;
    const body = h("div", { class: "body" },
      hasChoices
        ? h("div", { class: "opts" }, LETTERS.map((l, i) => h("div", { class: `opt ${l === q.correct ? "ok" : "no"}${l === r.top_wrong ? " top" : ""}` },
          h("span", { class: "tile-l", style: `background:var(${QUIZ[l]});${l === "c" ? "color:#0f172a" : ""}` }, l.toUpperCase()),
          h("span", { class: "t", attrs: { title: q.options[i] ?? "" } }, `${l.toUpperCase()}: ${q.options[i] ?? ""}`),
          l === q.correct ? h("span", { class: "tag" }, "Right") : (l === r.top_wrong ? h("span", { class: "tag" }, "Top wrong") : null),
          h("span", { class: "bar" }, h("i", { style: `width:${(counts[i] / r.attempts) * 100}%` })),
          h("span", { class: "p" }, pct(counts[i] / r.attempts)))))
        // the backend does not store the chosen option yet: show the right answer only
        : h("div", { class: "rightonly" }, img("bulb", 32), h("span", {}, `Right answer ${q.correct.toUpperCase()}: ${q.options[LETTERS.indexOf(q.correct)] ?? ""}. Which wrong option was chosen is not recorded yet.`)),
      topWrong ? h("div", { class: "tip" }, img("bulb"), h("span", {}, `Buddy tip: most students who missed this picked ${topWrong.toUpperCase()}: ${q.options[LETTERS.indexOf(topWrong)] ?? ""}. Look at what that answer gets wrong.`)) : null);
    const open = cards.length === 0;
    const card = h("div", { class: "qcard", attrs: { "data-open": String(open) } },
      h("div", { class: "header", props: { onclick: () => { card.dataset.open = String(card.dataset.open !== "true"); } } },
        Object.assign(chip("ink", qLabel(r.question_id)), { className: "chip ink qchip" }),
        h("div", { class: "titles" }, h("div", { class: "bold" }, q.text), h("div", { class: "small muted" }, `${r.guide_date} · ${r.question_id} · ${conceptOf(en).name} · ${r.attempts} answers`)),
        Object.assign(chip(tone(rate), toneLabel(rate)), { className: `chip ${tone(rate)} dchip` }),
        h("div", { class: `rate ${tone(rate)}` }, pct(rate), h("small", {}, "answered wrong")),
        h("span", { class: "chev" }, chevron())), body);
    cards.push(card);
  }
  $("questions").replaceChildren(...(cards.length ? cards : [h("p", { class: "muted" }, "No question has enough answers for this period.")]));
}

function renderConcepts(concepts) {
  $("concepts").replaceChildren(...(concepts.length ? concepts.slice(0, 5).map(c => {
    const ready = c.attempts >= MIN_CONCEPT;
    return h("div", { class: `concept${ready ? " ready" : ""}` },
      h("div", { class: "head" }, img(ready ? "flame" : "bulb"),
        h("div", { class: "t" }, h("div", { class: "bold" }, c.name), h("div", { class: "small muted" }, `${c.attempts} answers on ${c.questions} question(s)`)),
        h("div", { class: `rate ${tone(c.rate)}` }, pct(c.rate))),
      h("div", { class: "prog" }, h("div", { class: "track" }, h("div", { class: "fill", style: `width:${Math.min(1, c.attempts / MIN_CONCEPT) * 100}%` })), h("span", {}, `${Math.min(c.attempts, MIN_CONCEPT)} / ${MIN_CONCEPT}`)),
      ready ? chip("green", "Ready for a remedial guide") : chip("sky", `Needs ${MIN_CONCEPT - c.attempts} more answers`));
  }) : [h("p", { class: "muted" }, "No concept has enough answers yet.")]));
}

function renderCalendar(concepts) {
  const ready = concepts.filter(c => c.attempts >= MIN_CONCEPT);
  const days = nextRemedialDays(3);
  $("calendar").replaceChildren(h("div", { class: "subhead" }, "Remedial calendar"), h("div", { class: "small muted" }, "Every second day is a remedial day."),
    ...days.map((d, i) => h("div", { class: "day" },
      h("div", { class: `badge${ready[i] ? " on" : ""}` }, h("span", { class: "overline" }, d.toLocaleString("en", { month: "short" })), h("b", {}, String(d.getDate()))),
      h("div", { class: "t" }, ready[i] ? ready[i].name : "Next concept"),
      ready[i] ? chip("green", "Planned") : chip(i === ready.length ? "sky" : "neutral", i === ready.length ? "Waiting for data" : "Not set"))));
}

async function loadDocs(rows) {
  const base = window.ELIOS_CONFIG.pages;
  const manifest = await (await fetch(base + "manifest.json")).json();
  const dates = [...new Set(rows.map(r => r.guide_date))];
  const docs = {};
  await Promise.all(dates.map(async d => {
    const g = manifest.guides.find(x => x.date === d);
    if (!g) return;
    try { docs[d] = await (await fetch(base + g.content.en)).json(); } catch { /* guide not readable: its rows are skipped */ }
  }));
  return docs;
}

const minValue = () => Number($("empty").hidden ? $("min").value : $("min2").value) || 20;

async function refresh() {
  const client = state.client;
  $("msg").textContent = "Loading...";
  const { data, error } = await client.rpc("question_stats", { p_days: state.days, p_min: minValue() });
  if (error) {
    if (error.code === "42501") { show("denied"); return; }
    $("msg").textContent = `Could not load: ${error.message}`; return;
  }
  show("app");
  state.rows = data; state.docs = await loadDocs(data);
  const usable = data.filter(r => state.docs[r.guide_date] && questionOf(state.docs[r.guide_date], r.question_id));
  $("msg").textContent = `${data.length} question(s) with at least ${minValue()} answers.`;
  const empty = usable.length === 0;
  $("empty").hidden = !empty; $("content").hidden = empty;
  if (empty) return;
  const concepts = groupConcepts(data, state.docs);
  const totals = usable.reduce((t, r) => ({ attempts: t.attempts + r.attempts, wrong: t.wrong + r.wrong }), { attempts: 0, wrong: 0 });
  renderHero(concepts, totals); renderTiles(concepts, totals, usable.length); renderFilters(usable); renderQuestions(); renderConcepts(concepts); renderCalendar(concepts);
}

async function start() {
  const cfg = window.ELIOS_CONFIG;
  let saved = null; try { saved = localStorage.getItem("elios-theme"); } catch { /* ignore */ }
  applyTheme(saved || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light"));
  $("theme").onclick = () => applyTheme(document.documentElement.dataset.theme === "dark" ? "light" : "dark");
  for (const id of ["login", "sent", "denied"]) { const s = $(id); blob(s, -120, -140, 420, "--sky", 0.35); blob(s, 1100, 640, 460, "--sun", 0.45); blob(s, 1180, -160, 300, "--green", 0.35); blob(s, -80, 640, 260, "--coral", 0.25); }
  const client = state.client = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
  const logout = async () => { await client.auth.signOut(); location.reload(); };
  $("user").onclick = logout; $("deniedBack").onclick = logout; $("again").onclick = () => show("login");
  $("loginForm").onsubmit = async e => {
    e.preventDefault();
    const email = $("email").value;
    const { error } = await client.auth.signInWithOtp({ email, options: { emailRedirectTo: location.href.split("#")[0] } });
    if (error) { $("loginMsg").textContent = `Could not send the link: ${error.message}`; return; }
    $("sentTo").textContent = email; show("sent");
  };
  for (const b of $("period").querySelectorAll("button")) b.onclick = () => {
    state.days = Number(b.dataset.days);
    for (const x of $("period").querySelectorAll("button")) x.setAttribute("aria-pressed", String(x === b));
    refresh();
  };
  for (const id of ["min", "min2"]) $(id).onchange = e => { $("min").value = $("min2").value = e.target.value; refresh(); };
  $("refresh").onclick = refresh;
  const { data: { session } } = await client.auth.getSession();
  if (!session) { show("login"); return; }
  const who = (session.user && session.user.email) || "there";
  $("avatar").textContent = who[0].toUpperCase(); $("hello").textContent = `Hi, ${who.split("@")[0]}`;
  show("app");
  await refresh();
}

if (typeof window !== "undefined" && window.supabase && window.ELIOS_CONFIG) start();
