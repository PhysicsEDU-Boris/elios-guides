// ELIOS Insights: reads question_stats() and insights_summary() from Supabase (allow-listed login) and the published guides.
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

const state = { mlang: "en", tab: "overview", days: 30, filter: "all", rows: [], docs: {}, client: null };

function show(view) {
  for (const id of ["login", "sent", "denied", "app"]) $(id).hidden = id !== view;
  $("topbar").hidden = view !== "app";
}

function applyTheme(t) {
  document.documentElement.dataset.theme = t;
  $("theme").textContent = t === "dark" ? "Light mode" : "Dark mode";
  try { localStorage.setItem("elios-theme", t); } catch { /* private window: keep it for this visit only */ }
}

const num = n => Number(n || 0).toLocaleString("en");
const share = (a, b) => (b ? Math.round((a / b) * 100) : 0);
function card(id, title, sub, ...kids) {
  const e = $(id); e.replaceChildren(h("div", {}, h("h2", { class: "subhead" }, title), sub ? h("p", { class: "sub" }, sub) : null), ...kids.flat().filter(Boolean));
}
function rowbar(name, value, right, cls) {
  return h("div", { class: "rowbar" }, h("div", { class: "hd" }, h("span", { class: "n" }, name), h("span", { class: "v" }, right)),
    h("div", { class: "split" }, h("i", { class: cls || "ok", style: `width:${Math.max(0, Math.min(100, value))}%` })));
}
const waiting = (id, title, sub) => card(id, title, sub, chip("sun", "Waiting for the app to send this"), h("div", { class: "wait" }, h("div", { class: "big" }, "Not collected yet")));

function renderKpis(sum, topics) {
  const att = topics.reduce((t, c) => t + c.attempts, 0), bad = topics.reduce((t, c) => t + c.wrong, 0);
  const defs = [["green", "Active students", num(sum.students)], ["sky", "Quiz accuracy", att ? `${share(att - bad, att)}%` : "-"],
    ["sun", "7+ day streaks", num(sum.streaks.d7)], ["green", "Guides read", num(sum.stops.story)], ["coral", "Mini-lab runs", num(sum.stops.lab)], ["sky", "Scans", num(sum.scans.total)]];
  $("kpis").replaceChildren(...defs.map(([t, l, v]) => h("div", { class: `kpi ${t}` }, h("span", { class: "overline" }, l), h("div", { class: "num" }, v))));
}

function renderTopics(topics) {
  card("topics", "Right and wrong answers by topic", "First try on each guide question, grouped by physics topic",
    h("div", { style: "display:flex;gap:12px" }, chip("green", "Right"), chip("coral", "Wrong")),
    topics.length ? topics.map(c => {
      const ok = share(c.attempts - c.wrong, c.attempts);
      return h("div", { class: "rowbar" }, h("div", { class: "hd" }, h("span", { class: "n" }, c.name), h("span", { class: "v" }, `${ok}% right · ${100 - ok}% wrong · ${c.attempts} answers`)),
        h("div", { class: "split" }, h("i", { class: "ok", style: `width:${ok}%` }), h("i", { class: "bad", style: `width:${100 - ok}%` })));
    }) : h("p", { class: "muted" }, "No quiz answers in this period yet."));
}

function renderStreaks(sum) {
  const s = sum.streaks, tot = s.none + s.d1 + s.d2_3 + s.d4_6 + s.d7 || 1;
  const rows = [["No streak", s.none], ["1 day", s.d1], ["2–3 days", s.d2_3], ["4–6 days", s.d4_6], ["7+ days", s.d7]];
  card("streaks", "Streaks: how loyal are students", "Each student's longest run of guide days (a weekend gap does not break it)",
    rows.map(([n, v]) => rowbar(n, share(v, tot), `${v} students`, "ok")),
    h("div", { class: "note" }, `${share(s.d4_6 + s.d7, tot)}% of students kept a streak of 4 days or more.`));
}

function renderLearning(sum) {
  const days = sum.per_day, top = Math.max(1, ...days.map(d => d.story + d.physics + d.quiz + d.lab));
  const st = sum.stops, d = st.days || 1;
  card("learning", "Learning activity", "Guide reads, quiz and mini-lab per day",
    days.length ? h("div", { class: "bars" }, days.map(x => h("div", { class: "col1", attrs: { title: `${x.date}: story ${x.story}, physics ${x.physics}, quiz ${x.quiz}, mini-lab ${x.lab}` } },
      h("i", { class: "s", style: `height:${(x.quiz + x.lab) / top * 100}%` }), h("i", { class: "g", style: `height:${(x.story + x.physics) / top * 100}%` })))) : h("p", { class: "muted" }, "No guide activity in this period yet."),
    h("div", { style: "display:flex;gap:12px" }, chip("green", "Story and physics reads"), chip("sky", "Quiz and mini-lab")),
    h("div", { class: "mini" }, [["Story read", st.story], ["Physics read", st.physics], ["Guide quiz done", st.quiz], ["Mini-lab passed", st.lab]]
      .map(([n, v]) => h("div", {}, n, h("b", {}, `${share(v, d)}%`)))));
}

function renderScans(sum) {
  const s = sum.scans, labels = { recyclable: "Recyclable", organic: "Organic", residu: "Residue", b3: "B3 hazardous" }, total = Object.values(s.bins).reduce((a, b) => a + b, 0) || 1;
  card("scans", "Scan types", "What students use the camera for",
    h("div", { class: "three" }, [["sky", "Scan and quiz (phone)", s.phone_quiz], ["green", "Scan with robot (ELIOS 3)", s.robot], ["sun", "Scan to contribute", s.contribute]]
      .map(([t, l, v]) => h("div", { class: `kpi ${t}` }, h("span", { class: "overline" }, l), h("div", { class: "num" }, num(v))))),
    s.unknown_device ? h("p", { class: "sub" }, `${num(s.unknown_device)} older scans were saved before the device was recorded, so they are not counted above.`) : null,
    h("p", { class: "bold" }, "Bin info: where scanned items belong"),
    Object.entries(s.bins).sort((a, b) => b[1] - a[1]).map(([k, v]) => rowbar(labels[k] || k, share(v, total), `${share(v, total)}% · ${v}`, "ok")));
}

function renderRobot(sum) {
  const r = sum.scans.robot_first, n = r.right + r.wrong;
  card("robot", "Robot scan: first question", "First quiz question after an ELIOS 3 scan",
    chip("sun", "Not the exact bin question yet"),
    n ? h("div", { class: "two" }, [["green", "Right", r.right], ["coral", "Wrong", r.wrong]].map(([t, l, v]) => h("div", { class: `kpi ${t}` }, h("span", { class: "overline" }, l), h("div", { class: "num" }, `${share(v, n)}%`)))) : h("p", { class: "muted" }, "No robot scans with a quiz yet."),
    h("p", { class: "sub" }, "The app does not mark which question is the “which bin?” one, so this is the first question of each robot scan. Exact bin right/wrong needs a small app update."));
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

const minValue = () => Number($("min").value) || 20;

function setTab(tab) {
  state.tab = tab;
  for (const b of $("tabs").querySelectorAll("button")) b.setAttribute("aria-pressed", String(b.dataset.tab === tab));
  for (const e of document.querySelectorAll("[data-tabs]")) e.classList.toggle("hidden-tab", !e.dataset.tabs.split(" ").includes(tab));
}

async function refresh() {
  const client = state.client;
  $("msg").textContent = "Loading...";
  const [qs, all, sm] = await Promise.all([client.rpc("question_stats", { p_days: state.days, p_min: minValue() }),
    client.rpc("question_stats", { p_days: state.days, p_min: 1 }), client.rpc("insights_summary", { p_days: state.days })]);
  const error = qs.error || all.error || sm.error;
  if (error) {
    if (error.code === "42501") { show("denied"); return; }
    $("msg").textContent = `Could not load: ${error.message}`; return;
  }
  show("app");
  state.rows = qs.data; state.docs = await loadDocs(all.data);
  const usable = qs.data.filter(r => state.docs[r.guide_date] && questionOf(state.docs[r.guide_date], r.question_id));
  $("msg").textContent = `Last ${state.days} days · ${sm.data.students} student(s) active.`;
  const topics = groupConcepts(all.data, state.docs), concepts = groupConcepts(qs.data, state.docs);
  renderKpis(sm.data, topics); renderTopics(topics); renderStreaks(sm.data); renderLearning(sm.data);
  waiting("clovers", "Clovers earned", "Learning clovers per student"); waiting("videos", "Videos watched", "Watched vs started");
  renderScans(sm.data); renderRobot(sm.data);
  renderFilters(usable); renderQuestions(); renderConcepts(concepts); renderCalendar(concepts);
  setTab(state.tab);
  renderMagazines();
}

// ---- Magazines tab: published issues, their content, and how students did ----
const dayLabel = iso => new Date(`${iso}T00:00:00Z`).toLocaleDateString("en", { weekday: "short", day: "numeric", timeZone: "UTC" });
// issues without a photo use their generated cover
const thumb = g => (g.photo ? g.photo.thumb : g.cover.en);
const safeUrl = u => (/^https?:\/\//.test(u) ? u : null);
function healthRow(guides) {
  const have = new Map(guides.map(g => [g.date, g]));
  const dates = guides.map(g => g.date).sort(), today = new Date().toISOString().slice(0, 10), cells = [];
  let missing = 0;
  for (let d = new Date(`${dates[0]}T00:00:00Z`); d.toISOString().slice(0, 10) <= today; d.setUTCDate(d.getUTCDate() + 1)) {
    const iso = d.toISOString().slice(0, 10), g = have.get(iso), pending = !g && iso === today;
    if (!g && !pending) missing++;
    cells.push(h("div", { class: `hday ${g ? "ok" : "none"}` }, h("span", {}, dayLabel(iso)), h("b", {}, g ? `#${g.issue}` : pending ? "Today" : "None")));
  }
  $("mhealth").replaceChildren(h("div", { class: "hhead" }, h("h2", { class: "subhead" }, "Publishing health"), chip(missing ? "sun" : "green", missing ? `${missing} day(s) without a magazine` : "A magazine every day")), h("div", { class: "hdays" }, cells));
}
function progressRow(label, n, total, cls) {
  const p = share(n, total);
  return h("div", { class: "rowbar" }, h("div", { class: "hd" }, h("span", { class: "n" }, label), h("span", { class: "v" }, `${p}% · ${n}`)), h("div", { class: "split" }, h("i", { class: cls, style: `width:${p}%` })));
}
async function renderDetail(g) {
  const base = window.ELIOS_CONFIG.pages, st = state.mstats.get(g.date) || { started: 0, story: 0, physics: 0, quiz: 0, lab: 0 };
  let en = null;
  try { en = await (await fetch(base + (g.content[state.mlang] || g.content.en))).json(); } catch { /* content not readable */ }
  const t = k => (en && en[k]) || "";
  const sec = (title, tone, ...kids) => h("div", { class: `msec ${tone}` }, h("span", { class: "overline" }, title), ...kids.filter(Boolean));
  const legend = [1, 2, 3, 4, 5].filter(i => t(`legend.${i}.symbol`)).map(i => `${t(`legend.${i}.symbol`)} ${t(`legend.${i}.meaning`)} (${t(`legend.${i}.unit`)})`).join(" · ");
  const quiz = [1, 2, 3].filter(i => t(`quiz.${i}.question`)).map(i => {
    const right = String(en._answers[i]).toLowerCase();
    return h("div", { class: "mq" }, h("b", {}, `${i}. ${t(`quiz.${i}.question`)}`), ...LETTERS.map(l => h("div", { class: l === right ? "mo ok" : "mo" }, `${l.toUpperCase()}: ${t(`quiz.${i}.${l}`)}${l === right ? "  ✓" : ""}`)));
  });
  const steps = [1, 2, 3, 4].map(i => t(`lab.step_${i}`)).filter(Boolean);
  const srcs = ((en && en._sources) || []).map(x => { const u = safeUrl(x.url); return h("div", {}, `[${x.n}] ${x.publisher}: ${x.title} `, u ? h("a", { attrs: { href: u, target: "_blank", rel: "noopener noreferrer" } }, "link") : null); });
  const qrows = state.mq.filter(r => r.guide_date === g.date && /^p[1-3]$/.test(r.question_id)).sort((a, b) => a.question_id.localeCompare(b.question_id));
  const pdf = safeUrl(base + (g.pdf[state.mlang] || g.pdf.en));
  $("mdetail").replaceChildren(
    h("div", { class: "mhead" }, h("img", { class: "mcover", attrs: { src: base + thumb(g), alt: "" } }),
      h("div", { class: "mtitle" }, h("span", { class: "overline" }, `Issue ${g.issue} · ${g.date} · ${g.topic.en}`), h("h2", { class: "headline" }, g.title[state.mlang] || g.title.en),
        h("p", { class: "small muted" }, [t("cover.subject"), t("cover.read_time"), t("cover.level"), t("cover.xp_total")].filter(Boolean).join(" · ")),
        pdf ? h("a", { class: "btn secondary", attrs: { href: pdf, target: "_blank", rel: "noopener noreferrer" } }, "Open PDF") : null),
      h("div", { class: "seg" }, ["en", "id"].map(l => h("button", { attrs: { "aria-pressed": String(state.mlang === l) }, props: { type: "button", onclick: () => { state.mlang = l; renderDetail(g); } } }, l.toUpperCase())))),
    h("div", { class: "mcols" },
      h("div", { class: "mcontent" },
        en ? [sec("Story", "raised", h("b", {}, t("story.title")), h("p", {}, t("story.lead")), h("p", { class: "tx2" }, t("story.body_1")), h("p", { class: "tx2" }, t("story.body_2"))),
          sec("Physics", "sky", h("b", {}, `${t("physics.equation")}  ·  ${t("physics.equation_name")}`), h("p", { class: "tx2" }, legend), h("p", { class: "tx2" }, t("physics.body_1"))),
          sec("Quiz · 3 questions", "green", quiz), sec("Mini-lab", "sun", h("b", {}, t("lab.title")), steps.map(x => h("div", {}, `• ${x}`)), h("p", { class: "tx2" }, t("lab.question"))),
          sec("Sources", "raised", srcs)] : h("p", { class: "muted" }, "This magazine's content could not be loaded.")),
      h("div", { class: "mstats" }, h("h3", { class: "subhead" }, "How students did"),
        st.started ? [progressRow("Started", st.started, st.started, "s"), progressRow("Story read", st.story, st.started, "ok"), progressRow("Physics read", st.physics, st.started, "ok"),
          progressRow("Quiz done", st.quiz, st.started, "ok"), progressRow("Mini-lab passed", st.lab, st.started, "ok")] : chip("sun", "Published but untouched: nobody has started it"),
        qrows.length ? [h("p", { class: "bold" }, "Quiz: right vs wrong (first try)"), qrows.map(r => { const ok = share(r.attempts - r.wrong, r.attempts);
          return h("div", { class: "rowbar" }, h("div", { class: "hd" }, h("span", { class: "n" }, qLabel(r.question_id)), h("span", { class: "v" }, `${ok}% right · ${r.attempts} answers`)),
            h("div", { class: "split" }, h("i", { class: "ok", style: `width:${ok}%` }), h("i", { class: "bad", style: `width:${100 - ok}%` }))); })] : null)));
}
async function renderMagazines() {
  const base = window.ELIOS_CONFIG.pages, client = state.client;
  try { state.manifest ||= await (await fetch(base + "manifest.json")).json(); } catch { $("mlist").textContent = "The published list could not be loaded."; return; }
  const [ms, qs] = await Promise.all([client.rpc("magazine_stats", { p_days: 365 }), client.rpc("question_stats", { p_days: 365, p_min: 1 })]);
  state.mstats = new Map((ms.data || []).map(r => [r.guide_date, r])); state.mq = qs.data || [];
  const guides = [...state.manifest.guides].sort((a, b) => b.date.localeCompare(a.date));
  healthRow(guides);
  state.msel ||= guides[0].date;
  const draw = () => {
    $("mlist").replaceChildren(h("h2", { class: "subhead" }, "Published magazines"), ...guides.map(g => {
      const n = (state.mstats.get(g.date) || {}).started || 0;
      return h("div", { class: `mrow${g.date === state.msel ? " sel" : ""}`, props: { onclick: () => { state.msel = g.date; draw(); renderDetail(g); } } },
        h("img", { attrs: { src: base + thumb(g), alt: "" } }),
        h("div", { class: "mt" }, h("span", { class: "overline" }, `#${g.issue} · ${g.date}`), h("b", {}, g.title.en), h("span", { class: "small tx2" }, g.topic.en)),
        chip(n ? "green" : "sun", n ? `${n} started` : "Untouched"));
    }));
  };
  draw(); await renderDetail(guides.find(g => g.date === state.msel) || guides[0]);
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
  $("min").onchange = refresh;
  for (const b of $("tabs").querySelectorAll("button")) b.onclick = () => setTab(b.dataset.tab);
  const { data: { session } } = await client.auth.getSession();
  if (!session) { show("login"); return; }
  const who = (session.user && session.user.email) || "there";
  $("avatar").textContent = who[0].toUpperCase(); $("hello").textContent = `Hi, ${who.split("@")[0]}`;
  show("app");
  await refresh();
}

if (typeof window !== "undefined" && window.supabase && window.ELIOS_CONFIG) start();
