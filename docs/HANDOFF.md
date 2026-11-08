# Daily guides — 9 November 2026 (G4-P app feed)
- Branch: feat/g4-app-feed → PR to main (owner review; no merge, no push to main/published).
- Decision 0002: manifest v2 (additive; `xp` stays 60, split in `xp_parts`), photo checks, fact check, edit sync.
- Example v2 entry for 2026-11-08: docs/manifest-v2-example.json (NASA ISS075-E-188830 as photo).
- Tests: python -m pytest -q; actionlint. New tests break-checked against main.
- New workflow resync.yml (edits on guide/<date>); health check also fails on resync.json older than 24 h.
- Owner: set the Claude/Figma task to 05:00 AND 17:00 WIB; optional repo variable FACTCHECK_MODEL.
- Owner: after merge, re-run research for an issue to get a v2 entry; issue #01 needs _theme etc. to republish.
- No new secrets. GEMINI_API_KEY / FIGMA_TOKEN unchanged (Actions secrets only).
- Known limits: fact check matches numbers, not meaning; bot-blocked pages confirm nothing.
