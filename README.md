# elios-guides

Daily ELIOS Guide: a 4-page A4 PDF in English and Bahasa Indonesia about the physics behind one
real environmental news event, for students aged 12–15. The ELIOS app reads
[`manifest.json`](https://physicsedu-boris.github.io/elios-guides/manifest.json).

| When (Asia/Jakarta, every day) | Who | What |
|---|---|---|
| 03:00 | `daily-research.yml` (Gemini CLI) | research, calculations, fact-check, photos, validation → draft PR on `guide/<date>` |
| 05:00 and 17:00 | Existing Claude scheduled task ([prompt](automation/claude-figma-task.md)) | fills the Figma template (today, refills, rebuilds), uploads photos, swaps the cover mascot, pushes `figma.json` |
| on `figma.json` push | `export.yml` → `publish.yml` | exports both PDFs/covers, validates again, preserves the public archive, deploys Pages |
| on `en.json`/`id.json` push to `guide/<date>` | `resync.yml` | validates + fact-checks again, then marks a Figma refill or publishes app-only edits |
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

## Photo rules

`scripts/fetch_images.py` downloads the original file (Wikimedia `/thumb/` urls are turned into the
original upload; NASA/NOAA/USGS: the writer must give the largest rendition, up to 30 MB) and rejects:
long side under 1600 px (cover) / 1200 px (story), Laplacian variance under 120 on a 1024 px grey copy
(calibrated on `tests/fixtures/sharpness`: sharp 144–2945, blurry 13–88) and estimated JPEG quality
under 70. It never upscales. Kept photos are saved at most 2000 px, sRGB, quality 85, progressive; the
cover photo also as `photo.jpg` + `photo-800.jpg` (quality 82) for the app. On the last attempt a
failing photo becomes `null` (no blurry fallback). Figma gets the full-resolution file; the cover PNG is
exported at scale 2 and must be at least 1190×1684.

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
  that branch): `resync.yml` validates and fact-checks again, then writes `issues/<date>/resync.json`
  `{reason, content_sha, created}`. The next Claude run (05:00 or 17:00) refills the same wrapper frames,
  stores `content_sha` in `figma.json`, deletes `resync.json` and pushes; export + publish follow.
- **App-only fields** (`_quiz_explain`, `_quiz_pool`, `_lab_rubric`): no Figma; `resync.yml` publishes
  directly (new revision and `content_sha`, same date).
- **Writing rules** (`GEMINI.md`, `schema/limits.json`): apply from the next research run; nothing is
  re-published.
- **Figma template**: new issues use it automatically. To rebuild older issues, add their dates to
  [`automation/rebuild.txt`](automation/rebuild.txt) on main; the Claude task rebuilds them, re-publishes
  the same dates and clears the lines by PR.

## Setup / activation

- GitHub Actions enabled; repository workflow permissions must allow contents and PR writes.
- Secrets: `GEMINI_API_KEY` (own AI Studio project, sufficient model quota) and
  `FIGMA_TOKEN` (`file_content:read`, access to the template).
- Existing Claude/Figma task enabled **every day** at 05:00 **and 17:00** Asia/Jakarta, with Figma
  write access and repository push access. This repository's prompt is not itself a scheduler.
- Initialize `published` with `manifest.json` containing `{"updated":null,"guides":[]}` if absent.
  Do not replace an existing archive. The initial validated issue may also be published there.
- Pages → Build and deployment → Source: **GitHub Actions**. The `github-pages` environment must
  allow deployments from `guide/*` and the branch used for manual publishing.
- Enable GitHub Actions failure notifications for this repository in your GitHub account.
  Research, export, publish and the 08:00 health check report failures in Actions; no email key needed.
- Merge the automation PR through normal owner review before default-branch schedules can use it.
  ELIOS also needs the separate Daily Guide app release.

## Retry

For an already exported issue, run **publish** manually with its date (no Figma export needed).
For a failed research issue that has not reached Figma, run **daily-research** with its date and
**resume** enabled. It keeps the branch and repairs its files using the latest checks; filled issues
are rejected so their layouts and exports cannot be accidentally replaced by research.
For corrected Figma pages, run **export** manually with the date. Re-exporting the same date replaces
its catalogue entry and preserves every other issue. Failed research branches are retained for repair;
fix the branch rather than deleting a published issue. Never publish a `NEEDS FIX` issue by hand.

Rules for the writer: [GEMINI.md](GEMINI.md). Slot limits: [schema/limits.json](schema/limits.json).
Examples: [schema/example.en.json](schema/example.en.json), [schema/example.calc.py](schema/example.calc.py).

Dry run: run **daily-research** manually with `dry_run` on (and a test date). It writes to
`guide/dry-run-<date>` with a "DRY RUN" draft PR; nothing goes to Figma, export or Pages.

Checks: `pip install -r requirements.txt && python -m pytest -q`; `actionlint` for workflows.
