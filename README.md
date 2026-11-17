# elios-guides

Daily ELIOS Guide: a 4-page A4 PDF in English and Bahasa Indonesia about the physics behind one
real environmental news event, for students aged 12–15. The ELIOS app reads
[`manifest.json`](https://physicsedu-boris.github.io/elios-guides/manifest.json).

| When (Asia/Jakarta, every day) | Who | What |
|---|---|---|
| 03:00 | `daily-research.yml` (Gemini CLI) | research, calculations, fact-check (Gemini, then Groq/OpenRouter fallback), photos, validation → draft PR on `guide/<date>` |
| right after research passes | `export.yml` → `publish.yml` | renders both PDFs and covers from the JSON ([render/](render/)), validates again, preserves the public archive, deploys Pages |
| on `en.json`/`id.json` push to `guide/<date>` | `resync.yml` | validates + fact-checks again, then re-renders and publishes (printed text) or publishes app-only edits |
| 08:00 | `daily-health.yml` | fails if today's issue is absent from the live catalogue or a `resync.json` is older than 24 h |

Publication does not merge guide PRs or push to main. The `published` branch keeps public issue
files and the newest 365 catalogue entries. Old files remain available for saved links.
Research reads this published catalogue so issue numbers and recent-topic checks remain current.
Failed content checks, source checks or exports leave the previous live issue available.
A corrected export changes its asset revision, so the app downloads the new PDF while retaining
reading progress for that date. Schedule times are targets, not guaranteed delivery times.

## Manifest v2

Each catalogue entry keeps every v1 field unchanged and adds:

| Field | Value |
|---|---|
| `schema` | `2` |
| `theme` | `water` · `heat` · `air` · `energy` · `waste` · `storm` (from `_theme`, validated) |
| `photo` | `{src, thumb, w, h, caption{en,id}, credit, license, source_url}` or `null` (app shows the topic illustration) |
| `content_sha` | `{en, id}`: sha256 of the published `en.json` / `id.json` |
| `xp_parts` | `{"story":10,"physics":20,"quiz":10,"lab":20}`; v1 `xp` stays the int total (60) |
| `pages` | page count of the exported PDF (4) |

`revision` is the sha256 over every published file of the issue (JSON, PDFs, cover PNGs, photos), so any
edit gives a new revision; the date and issue number never change. Example for 2026-11-08:
[docs/manifest-v2-example.json](docs/manifest-v2-example.json).

## Remedial guides (every second day)

The app backend already stores each student's first quiz attempt per question in Supabase (`guide_progress.quiz.first.answers`: `p1`-`p3`, right or wrong). [supabase/schema.sql](supabase/schema.sql) adds `question_stats()` over that data (no student identifiers) and the dashboard allow-list; nothing new is collected from students. The chosen option is not stored yet, so the most common wrong answer stays empty until the backend also saves `answers[].choice`.
On every second day (even date ordinal; 16 Nov 2026 is one)
`scripts/weak_questions.py` reads `question_stats()` with the service key, groups questions by the concept
(formula) of their guide, and writes `.gemini/remedial-brief.json`: the concept students miss most, its three
hardest questions, the right answer and the most common wrong answer. A concept needs 60 answers (30 per
question) and is not repeated within 14 days. The writer then follows the "Remedial mode" section of
[GEMINI.md](GEMINI.md): a real recent event that shows the concept, the misconception explained, three new
quiz questions, and `_remedial` in both files (the manifest entry keeps it). Without the secrets, without
enough answers or if Supabase is unreachable, the day stays a normal news guide. One issue per date is kept,
so a remedial guide takes the place of that day's news guide.

The private dashboard for these statistics is in [dashboard/](dashboard/README.md) (Vercel, Supabase email login).

Setup: run `supabase/schema.sql` in the existing ELIOS Supabase project (SQL editor), add your email to `dashboard_users`, then set the
Actions secrets `SUPABASE_URL` and `SUPABASE_SERVICE_KEY` (service key: never in the app or the dashboard).

## Repeat protection

`scripts/repeats.py` compares a new issue with the last 60 catalogue entries, offline and without a model:
its first source article was already the main source of one, two or more sources are shared, or the
title, topic, slug, place and keywords share at least 40% of their words (plural-insensitive). Manifest
entries store `sources` and `terms` (additive); `backfill_repeats.py` fills them for older entries from
their `en.json` on `published` (a local copy; the branch is never changed). Replaying the real
catalogue flags exactly one issue, 2026-11-09, which reused the NASA Goosenecks article of 2026-11-08.
The word check alone scored that pair only 19%, so the source check is the main safeguard. Not caught:
the same event reported from entirely different sources in different words.

## Formula bank

The key equation comes from [`schema/formulas.json`](schema/formulas.json): 46 formulas (21 core for SMP,
25 stretch for SMA and above) across the six themes. Each has an `id`, `level`, `themes`, `text`
(Unicode, shown in the app), `latex` (typeset in the PDF by the bundled KaTeX in `render/katex/`) and up
to five `symbols` with a meaning and unit hint. The writer sets `_formula` to an id in both files;
`validate.py` requires the same id, the exact `text` and the bank's legend symbols, rejects an id used in
the last 30 issues, and rejects a stretch formula right after another stretch one. The manifest entry
records `formula` (additive). To add a formula, append an entry; `tests/test_formulas.py` and the render
test check the limits and that it typesets and fits the equation card.

## Photo rules

`scripts/fetch_images.py` downloads the original file (Wikimedia `/thumb/` urls are turned into the
original upload; NASA/NOAA/USGS: the writer must give the largest rendition, up to 30 MB) and rejects:
long side under 1600 px (cover) / 1200 px (story), Laplacian variance under 120 on a 1024 px grey copy
(calibrated on `tests/fixtures/sharpness`: sharp 144–2945, blurry 13–88) and estimated JPEG quality
under 70. It never upscales. Kept photos are saved at most 2000 px, sRGB, quality 85, progressive; the
cover photo also as `photo.jpg` + `photo-800.jpg` (quality 82) for the app. A failed optional story photo
may become `null`. A failed or missing cover photo is replaced, in order, by a Wikimedia Commons archive
photo ([`find_images.py`](scripts/find_images.py): CC0, public domain, CC BY or CC BY-SA, same size and
sharpness checks, captioned "Archive photo · place"), then by an ELIOS cover drawn from the issue's own
equation on a theme gradient. The app card shows its topic illustration when `photo` is `null`. News-site
photos are never used (copyrighted). The renderer embeds the full-resolution file; the cover PNG is
rendered at scale 2 and must be at least 1190×1684.

## Fact check

`scripts/check_sources.py` (run by `validate.py --check-sources` and before publishing) opens every
source and fails the issue as **NEEDS FIX** when a source is missing, never cited with `[n]`, or
off-topic (its article text names fewer than 2 topic keywords from `_slug`, `cover.place`, `_keywords`),
or when a number in `stat.N.value`, `story.*` or `cover.*` is in no source page and is not a value
`calc.py` computes (literal inputs in `calc.py` need a source too). A failing issue is not published;
the previous one stays live. The independent fact-check uses one structured Gemini API request
with bounded, fetched article text, rather than a CLI tool loop. It defaults to
`gemini-3.5-flash-lite` and retries with `gemini-3.1-flash-lite` if the first report is incomplete.
Set the repository variable `FACTCHECK_MODEL` to change the primary model. Research and repair
still use Gemini CLI. After a repair, the old
`check.json` is discarded and an independent Flash-Lite pass checks the repaired files again.
A missing or failing new report blocks publication; the earlier report is never reused.

## Edits after publication

- **Printed text** (`en.json`/`id.json` on `guide/<date>`, directly or by merging a correction PR into
  that branch): `resync.yml` validates and fact-checks again, then runs `export.yml` to re-render both
  PDFs and covers and publish (new revision, same date). A fixed `NEEDS FIX` branch is rendered the same way.
- **App-only fields** (`_quiz_explain`, `_quiz_pool`, `_lab_rubric`): `resync.yml` publishes
  directly (new revision and `content_sha`, same date); the PDFs are not rendered again.
- **Writing rules** (`GEMINI.md`, `schema/limits.json`): apply from the next research run; nothing is
  re-published.
- **Layout** (`render/guide.html`, `render/base.css`, `render/fill.js`): each text element carries a
  `data-key` equal to the JSON key it shows. A template change applies to new issues; to rebuild an older
  one, run **export** with its date.

## Setup / activation

- GitHub Actions enabled; repository workflow permissions must allow contents and PR writes.
- Secret: `GEMINI_API_KEY` (own AI Studio project, sufficient model quota). Optional fact-check
  fallbacks: variables `FALLBACK_BASE_URL`/`FALLBACK_MODEL` + secret `FALLBACK_API_KEY` (e.g. Groq), and the
  same with `FALLBACK2_` (e.g. OpenRouter); each runs only when the one before left no `check.json`.
  Research and both repairs also fall back to `scripts/research_fallback.py` when Gemini fails: it uses
  `RESEARCH_BASE_URL`/`RESEARCH_MODEL`/`RESEARCH_API_KEY` (default: the `FALLBACK2_*` OpenRouter settings; its web plugin does the search). Test it with `daily-research` input `force_fallback`.
- Rendering needs no token: GitHub Actions installs Chromium (`python -m playwright install chromium`).
- Initialize `published` with `manifest.json` containing `{"updated":null,"guides":[]}` if absent.
  Do not replace an existing archive. The initial validated issue may also be published there.
- Pages → Build and deployment → Source: **GitHub Actions**. The `github-pages` environment must
  allow deployments from `guide/*` and the branch used for manual publishing.
- Enable GitHub Actions failure notifications for this repository in your GitHub account.
  Research, export, publish and the 08:00 health check report failures in Actions; no email key needed.
- Merge the automation PR through normal owner review before default-branch schedules can use it.
  ELIOS also needs the separate Daily Guide app release.

## Retry

For an already exported issue, run **publish** manually with its date (no render needed).
For a failed research issue that has not been exported, run **daily-research** with its date and
**resume** enabled. It keeps the branch and repairs its files using the latest checks; exported issues
are rejected so their PDFs cannot be accidentally replaced by research.
To render an issue again, run **export** manually with the date. Re-exporting the same date replaces
its catalogue entry and preserves every other issue. Failed research branches are retained for repair;
fix the branch rather than deleting a published issue. Never publish a `NEEDS FIX` issue by hand.

Rules for the writer: [GEMINI.md](GEMINI.md). Slot limits: [schema/limits.json](schema/limits.json).
Examples: [schema/example.en.json](schema/example.en.json), [schema/example.calc.py](schema/example.calc.py).

Dry run: run **daily-research** manually with `dry_run` on (and a test date). It writes to
`guide/dry-run-<date>` with a "DRY RUN" draft PR; nothing is rendered, exported or sent to Pages.

Checks: `pip install -r requirements.txt && python -m pytest -q`; `actionlint` for workflows.
