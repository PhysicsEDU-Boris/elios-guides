# Changelog

## Unreleased — 16 November 2026 (remedial guides)

- Supabase schema for anonymous quiz-answer events and `question_stats()`; the event contract for the app is in `docs/answer-events.md`.
- `scripts/weak_questions.py` builds a brief from the weakest concept every second day; GEMINI.md has a Remedial mode; `_remedial` is validated and recorded in the manifest (`remedial`).

## Unreleased — 16 November 2026 (repeat protection)

- `scripts/repeats.py`: an issue is rejected when its main source article was already used in the last 60 issues, when two sources are shared, or when its words overlap 40% with one. Manifest entries gain `sources` and `terms`; older entries are backfilled in the research workflow.

## Unreleased — 16 November 2026 (cover fallback)

- `cover.image` may be null: Wikimedia Commons archive photo first (`scripts/find_images.py`), then a generated ELIOS cover from the equation. Replaces the rule that a missing cover photo blocks publication.
- Renderer waits for KaTeX fonts before measuring, so equations are fitted with the real font.

## Unreleased — 16 November 2026 (formula bank)

- `schema/formulas.json`: 46 curated formulas (core and stretch) with LaTeX; the writer picks one by `_formula` instead of inventing an equation.
- The PDF typesets equations with KaTeX (fractions, roots, exponents, logarithms); the equation limit is 40 characters and legend symbols 4.
- `validate.py` checks the id, exact text and symbols, avoids repeats (30 issues) and back-to-back stretch formulas; manifest entries record `formula`.

## Unreleased — 16 November 2026 (no Figma)

- PDFs and covers are rendered from `en.json`/`id.json` by `scripts/render_guide.py` (Chromium, `render/`), right after research passes. No Figma file, token, scheduled Claude task, `figma.json`, `resync.json` or `rebuild.txt`.
- Edits to printed text re-render and publish through `resync.yml`; the 08:00 stale-refill check is gone.
- Fact-check fallback chain: Gemini, alternate Gemini model, then optional Groq and OpenRouter (OpenAI-compatible).

## Unreleased — 9 November 2026 (G4 app feed, decision 0002)

- Manifest v2 (additive): `schema`, `theme`, `photo`, `content_sha`, `xp_parts`, `pages`; `revision` now covers JSON and photos.
- Content for the app: `_theme`, `_quiz_explain`, `_quiz_pool` (at least 4), Indonesian `_lab_rubric`; validated.
- Photo quality: originals only, minimum size, sharpness and JPEG-quality checks, no upscaling, `photo.jpg` + `photo-800.jpg`; cover PNG at least 1190×1684.
- Fact check: numbers must be in a source or computed by calc.py; uncited or off-topic sources fail the issue.
- Auto-sync of owner edits (`resync.yml`, `resync.json`, `rebuild.txt`), second Claude/Figma run at 17:00, mascot by theme.
- Stale `resync.json` fails the 08:00 health check; research has a `dry_run` input.

## Unreleased — 8 November 2026

- Research runs seven days a week and uses the deployed catalogue for numbering and topic history.
- Validated bilingual exports publish automatically through GitHub Pages, without merging guide PRs.
- Preserve the published archive; check facts, source links, four-page PDFs and PNG covers before deployment.
- Give corrected assets a revision so apps can refresh cached PDFs without resetting reading position.
- Check for a missing daily publication at 08:00 Asia/Jakarta.
