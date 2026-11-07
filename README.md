# elios-guides

Daily ELIOS Guide (4-page A4 PDF, English + Bahasa Indonesia) on the physics behind one real
environmental news event, for students aged 12–15. Published with GitHub Pages; the ELIOS app reads
[`manifest.json`](https://physicsedu-boris.github.io/elios-guides/manifest.json).

| When (WIB, Mon–Fri) | Who | What |
|---|---|---|
| 03:00 | `daily-research.yml` (Gemini CLI) | research → `issues/<date>/en.json`, `id.json`, `calc.py` → calc → fact-check → photos → `validate.py` → draft PR on `guide/<date>` |
| 05:00 | Claude scheduled task ([prompt](automation/claude-figma-task.md)) | fills the Figma template with [`figma/fill.js`](figma/fill.js), uploads photos, pushes `figma.json` |
| on `figma.json` push | `export.yml` | Figma REST export → PDF + cover PNG → `manifest.json` → PR ready |
| when you merge the PR | GitHub Pages | publishes |

Rules for the writer: [GEMINI.md](GEMINI.md). Slot limits: [schema/limits.json](schema/limits.json).
Example issue: [schema/example.en.json](schema/example.en.json) + [schema/example.calc.py](schema/example.calc.py).

Secrets: `GEMINI_API_KEY` (own AI Studio project), `FIGMA_TOKEN` (`file_content:read`).

Local checks: `pip install -r requirements.txt && python -m pytest -q`
