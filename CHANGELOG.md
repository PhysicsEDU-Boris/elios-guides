# Changelog

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
