# 0002 — App feed: manifest v2, photo quality, fact check, edit sync

Accepted, 9 November 2026. Owner approved the Figma "G4 · Daily Guides (app)" design (task G4-P).

**Manifest v2 is additive.** Every v1 field keeps its name and type, so the released app keeps working.
v1 already uses `xp` as the int total, so the per-stop split is `xp_parts` (not an `xp` object).
`photo` is `null` rather than a weak picture; the app then draws the topic illustration. `revision`
hashes every published file so the app refreshes on any edit, while `date`/`issue` never change.

**Photos.** Blur came from thumbnails (1280 px) and soft originals. Thresholds: cover ≥1600 px, story
≥1200 px, Laplacian variance ≥120 on a 1024 px grey copy, JPEG quality ≥70. The threshold sits between
5 blurry samples (13–88) and 5 sharp ones (144–2945). Issue #01: the cover thumbnail (1280 px, 174, q87)
and its original (2144 px, 83, q93, a hazy airliner shot) both fail; the NASA ISS075-E-188830 photo
(2160 px, 2396, q99) passes.

**Fact check is deterministic.** Gemini's check.json approved invented values before, so a script now
requires every printed number in stats, story and cover to appear in an opened source page or be
computed by calc.py; literal calc.py inputs do not count. On issue #01 it flags 120 m and 20 s and both
off-topic sources. Limits: numbers only, not the meaning around them; pages behind bot blockers confirm
nothing; "m" also reads as million, so some unit-less coincidences pass. Editorial review still matters.

**Edits.** Printed-text edits go through Figma (resync.json, refilled by the Claude task at 05:00 or
17:00); app-only fields publish directly. Template rebuilds are opt-in per date (rebuild.txt), cleared
by PR so no automation pushes to main. The health check fails when a refill waits more than 24 h.
