// ELIOS Question Insights: reads question_stats() from Supabase (allow-listed login) and the published guides.
const MIN_CONCEPT = 60; // answers per concept before the remedial guide picks it (same as scripts/weak_questions.py)
const LETTERS = ["a", "b", "c", "d"];

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

function h(tag, props = {}, ...kids) {
  const e = document.createElement(tag);
  Object.assign(e, props.props || {});
  if (props.class) e.className = props.class;
  if (props.style) e.style.cssText = props.style;
  e.append(...kids.flat().filter(k => k != null));
  return e; // text goes in as text nodes: guide content is never parsed as HTML
}

function pct(x) { return `${Math.round(x * 100)}%`; }

function renderConcepts(list) {
  return list.length ? list.map(c => h("div", { class: "card row" },
    h("div", {}, h("div", { class: "q" }, c.name), h("div", { class: "meta" }, `${c.attempts} answers on ${c.questions} question(s) `,
      h("span", { class: "pill" + (c.attempts >= MIN_CONCEPT ? " ready" : "") }, c.attempts >= MIN_CONCEPT ? "ready for a remedial guide" : `needs ${MIN_CONCEPT - c.attempts} more answers`))),
    h("div", { class: "rate" }, pct(c.rate), h("small", {}, "wrong")))) : [h("p", { class: "meta" }, "No concept has enough answers yet.")];
}

function renderQuestions(rows, docs) {
  const cards = [];
  for (const r of rows) {
    const en = docs[r.guide_date], q = en && questionOf(en, r.question_id);
    if (!q) continue;
    const counts = LETTERS.map(l => r[`chosen_${l}`]);
    cards.push(h("div", { class: "card" },
      h("div", { class: "row" },
        h("div", {}, h("div", { class: "q" }, q.text), h("div", { class: "meta" }, `${r.guide_date} · ${r.question_id} · ${conceptOf(en).name} · ${r.attempts} answers`)),
        h("div", { class: "rate" }, pct(Number(r.wrong_rate)), h("small", {}, "wrong"))),
      counts.some(n => n > 0)
        ? h("div", { class: "opts" }, LETTERS.map((l, i) => h("div", { class: `opt ${l === q.correct ? "ok" : "no"}${l === r.top_wrong ? " top" : ""}` },
          h("span", { class: "t", props: { title: q.options[i] } }, `${l.toUpperCase()}: ${q.options[i] ?? ""}`),
          h("div", { class: "track" }, h("div", { class: "fill", style: `width:${(counts[i] / r.attempts) * 100}%` })),
          h("span", {}, pct(counts[i] / r.attempts)))))
        // the backend does not store the chosen option yet: show the right answer only
        : h("div", { class: "meta", style: "margin-top:6px" }, `Right answer ${q.correct.toUpperCase()}: ${q.options[LETTERS.indexOf(q.correct)] ?? ""}. Which wrong option was chosen is not recorded yet.`)));
  }
  return cards.length ? cards : [h("p", { class: "meta" }, "No question has enough answers for this period.")];
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

async function refresh(client) {
  const $ = id => document.getElementById(id);
  $("msg").textContent = "Loading...";
  const { data, error } = await client.rpc("question_stats", { p_days: Number($("days").value), p_min: Number($("min").value) });
  if (error) { $("msg").textContent = error.code === "42501" ? "This email is not on the dashboard allow-list." : `Could not load: ${error.message}`; return; }
  const docs = await loadDocs(data);
  $("concepts").replaceChildren(...renderConcepts(groupConcepts(data, docs)));
  $("questions").replaceChildren(...renderQuestions(data, docs));
  $("msg").textContent = `${data.length} question(s) with at least ${$("min").value} answers.`;
}

async function start() {
  const cfg = window.ELIOS_CONFIG, $ = id => document.getElementById(id);
  const client = window.supabase.createClient(cfg.supabaseUrl, cfg.supabaseAnonKey);
  const { data: { session } } = await client.auth.getSession();
  $("login").hidden = !!session;
  $("app").hidden = !session;
  $("loginForm").onsubmit = async e => {
    e.preventDefault();
    const { error } = await client.auth.signInWithOtp({ email: $("email").value, options: { emailRedirectTo: location.href.split("#")[0] } });
    $("loginMsg").textContent = error ? `Could not send the link: ${error.message}` : "Check your email for the login link.";
  };
  $("logout").onclick = async () => { await client.auth.signOut(); location.reload(); };
  $("refresh").onclick = () => refresh(client);
  if (session) await refresh(client);
}

if (typeof window !== "undefined" && window.supabase && window.ELIOS_CONFIG) start();
