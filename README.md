# elios-guides

Daily ELIOS Guide: a 4-page A4 PDF in English and Bahasa Indonesia about the physics behind one
real environmental news event, for students aged 12–15. The ELIOS app reads
[`manifest.json`](https://physicsedu-boris.github.io/elios-guides/manifest.json).

| When (Asia/Jakarta, every day) | Who | What |
|---|---|---|
| 03:00 | `daily-research.yml` (Gemini CLI) | research, calculations, fact-check, photos, validation → draft PR on `guide/<date>` |
| 05:00 | Existing Claude scheduled task ([prompt](automation/claude-figma-task.md)) | fills the Figma template, uploads photos, pushes `figma.json` |
| on `figma.json` push | `export.yml` → `publish.yml` | exports both PDFs/covers, validates again, preserves the public archive, deploys Pages |
| 08:00 | `daily-health.yml` | fails if today's issue is absent from the live catalogue |

Publication does not merge guide PRs or push to main. The `published` branch keeps public issue
files and the newest 365 catalogue entries. Old files remain available for saved links.
Research reads this published catalogue so issue numbers and recent-topic checks remain current.
Failed content checks, source checks or exports leave the previous live issue available.
A corrected export changes its asset revision, so the app downloads the new PDF while retaining
reading progress for that date. Schedule times are targets, not guaranteed delivery times.

## Setup / activation

- GitHub Actions enabled; repository workflow permissions must allow contents and PR writes.
- Secrets: `GEMINI_API_KEY` (own AI Studio project, sufficient model quota) and
  `FIGMA_TOKEN` (`file_content:read`, access to the template).
- Existing Claude/Figma task enabled **every day** at 05:00 Asia/Jakarta, with Figma write access
  and repository push access. This repository's prompt is not itself a scheduler.
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
For corrected Figma pages, run **export** manually with the date. Re-exporting the same date replaces
its catalogue entry and preserves every other issue. Failed research branches are retained for repair;
fix the branch rather than deleting a published issue. Never publish a `NEEDS FIX` issue by hand.

Rules for the writer: [GEMINI.md](GEMINI.md). Slot limits: [schema/limits.json](schema/limits.json).
Examples: [schema/example.en.json](schema/example.en.json), [schema/example.calc.py](schema/example.calc.py).

Checks: `pip install -r requirements.txt && python -m pytest -q`; `actionlint` for workflows.
