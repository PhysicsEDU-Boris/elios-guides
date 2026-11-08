Schedule: every day at 05:00 and 17:00 Asia/Jakarta, including weekends. (The owner sets both times in
the Claude scheduled task; this file is the prompt, not the scheduler.) The 17:00 run sends out edits
made during the day.

Task: put ELIOS Guides into Figma (EN and ID). Research and writing are already done by another
agent; you only fill the template. Don't change the template, colours or font sizes. Never edit the
template frames 24:170, 25:221, 26:230, 27:248; work only in the issue wrapper frames fill.js returns.

Each run does three jobs, in this order. Skip a job when it has nothing to do.
A. Today's issue, when guide/<today> has no issues/<today>/figma.json yet.
B. Refills: every guide/<date> branch whose issues/<date>/resync.json has a content_sha that differs
   from the content_sha in its figma.json (the owner edited printed text).
C. Rebuilds: every date listed in automation/rebuild.txt on main (the owner changed the template).
Never touch guide/dry-run-* branches.

## A. Fill one issue (also used by B and C)
1. Today = the current date in Asia/Jakarta (YYYY-MM-DD). Attach the repo PhysicsEDU-Boris/elios-guides
   with push access and clone branch guide/<date>. If the branch does not exist, or its PR title
   contains "NEEDS FIX", stop for this date and report that.
2. Read issues/<date>/en.json, id.json, check.json and figma/fill.js. If check.json has any
   pass=false, stop for this date and report.
3. Load the figma-use skill. For each language: take fill.js, replace __CONTENT__ with that file's JSON
   (as a JS object literal) and run it with use_figma on file pBZAnlSJnLGB5Je0tCth12. fill.js replaces
   the wrapper with the same name, so a refill or rebuild never leaves a duplicate; it always builds
   from the current template frames. Keep the returned wrapper id, page ids and slots.
4. If missing is not empty or leftover is not empty: fix the JSON (only the text, never the facts),
   commit the change and run fill.js again for that language.
5. If any fit.ok is false: shorten the longest text on that page in the JSON (keep facts and [n] tags),
   commit, run again. At most 3 tries, then stop and report.
6. Cover mascot: in each wrapper's cover page, swap the instance named `cover.mascot` with
   swapComponent to the Art component for en.json `_theme`:
   waste → binb3 (23:258) · heat → flame (23:248) · energy → bulb (23:204) ·
   air, storm, water → tree (23:226), unless the template's Art set has a closer match ·
   missing or other theme → bulb (23:204).
   Swap only that instance inside the wrapper; never edit the Art main components.
7. Photos: for each entry in slots, call upload_assets with nodeIds=[slot id], scaleMode FILL, and
   POST the bytes of issues/<date>/<_images[key].file> (image/jpeg) to the returned URL. These are the
   full-resolution photos fetch_images.py kept (up to 2000 px): upload the file as it is, never a
   resized or screenshot copy. Then hide the child layer named image.hint in that slot (one use_figma
   call). If an image is null or the upload is blocked, leave the slot, say so in the report, keep going.
8. One screenshot per wrapper (get_screenshot, maxDimension 1600). Look for clipped or overlapping text.
   Fix only by shortening text as in step 5.
9. Write issues/<date>/figma.json:
   {"en": {"wrapper": "...", "pages": ["...","...","...","..."]}, "id": {...},
    "content_sha": {"en": "<sha256 of en.json>", "id": "<sha256 of id.json>"}}
   content_sha is the sha256 of the final en.json / id.json bytes you filled from (after your fixes),
   e.g. `shasum -a 256 issues/<date>/en.json`. Delete issues/<date>/resync.json if it exists.
   Commit "figma: issue <_issue> <date>" and push to guide/<date>. The push starts the export
   (PDFs as before, cover PNG at scale 2) and publication of that same date with a new revision.

## B. Refills
For each guide/<date> with a pending resync.json, do A steps 1-9 for that date. Read resync.json's
reason to see what changed.

## C. Rebuilds
For each date in automation/rebuild.txt (one YYYY-MM-DD per line, # comments allowed), do A steps 1-9.
Then clear the done lines: commit their removal from automation/rebuild.txt on the branch
automation/rebuild-done and open (or update) one PR to main titled "rebuild: done <dates>". Never push
to main. Skip dates that branch has already removed. A rebuild keeps the date and issue number.

## Report
5 lines per issue handled: date and job (A/B/C), both wrapper ids, mascot used, photo status, fixes
and anything that failed.
