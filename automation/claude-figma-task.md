Schedule: every day at 05:00 Asia/Jakarta, including weekends.

Task: put today's ELIOS Guide into Figma (EN and ID). Research and writing are already done by another
agent; you only fill the template. Don't change the template, colours or font sizes.

1. Today = the current date in Asia/Jakarta (YYYY-MM-DD). Attach the repo PhysicsEDU-Boris/elios-guides
   with push access and clone branch guide/<today>. If the branch does not exist, or its PR title
   contains "NEEDS FIX", stop and report that; do nothing else.
2. Read issues/<today>/en.json, id.json, check.json and figma/fill.js. If check.json has any
   pass=false, stop and report.
3. Load the figma-use skill. For each language: take fill.js, replace __CONTENT__ with that file's JSON
   (as a JS object literal) and run it with use_figma on file pBZAnlSJnLGB5Je0tCth12. Keep the
   returned wrapper id, page ids and slots.
4. If missing is not empty or leftover is not empty: fix the JSON (only the text, never the facts),
   commit the change and run fill.js again for that language.
5. If any fit.ok is false: shorten the longest text on that page in the JSON (keep facts and [n] tags),
   commit, run again. At most 3 tries, then stop and report.
6. Photos: for each entry in slots, call upload_assets with nodeIds=[slot id], scaleMode FILL, and
   POST the bytes of issues/<today>/<_images[key].file> (image/jpeg) to the returned URL. Then hide the
   child layer named image.hint in that slot (one use_figma call). If the upload is blocked, leave the
   slot, say so in the report, and keep going.
7. One screenshot per wrapper (get_screenshot, maxDimension 1600). Look for clipped or overlapping text.
   Fix only by shortening text as in step 5.
8. Write issues/<today>/figma.json:
   {"en": {"wrapper": "...", "pages": ["...","...","...","..."]}, "id": {...}}
   Commit "figma: issue <_issue> <today>" and push to guide/<today>. This starts the PDF export.
9. Report in 5 lines: topic, both wrapper ids, fixes you made, photo status, anything that failed.
