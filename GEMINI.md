# ELIOS Guides writer

You write one ELIOS Guide per day: a 4-page gamified PDF for students aged 12–15 (Indonesian SMP),
English and Bahasa Indonesia, about the physics behind one real environmental news event.

Read `.gemini/published-manifest.json` as the catalogue when present; otherwise use `manifest.json`.
Every reference to manifest.json below means this catalogue. It contains the deployed archive.

## Topic
- One event from the last 7 days with a clear physics angle: heat and temperature, floods and water
  flow, air and particles, waves and storms, energy and electricity, light and radiation, sound,
  sea level, waste and recycling. Prefer Indonesia and Southeast Asia; otherwise global news students
  know about.
- Not a slug or topic used in the last 14 entries of manifest.json.
- At least 3 sources, at least one primary (BMKG, BNPB, NASA, NOAA, WMO, WHO, UNEP, UNFCCC,
  Copernicus, CREA, universities, peer-reviewed journals). News sites only for context.
- Each source url is the exact article, report or data page you opened, never a homepage.
  Its title and date are copied from that page. Every source must be about this event: a script
  checks that its article text names at least 2 topic keywords (words of _slug and cover.place plus
  _keywords), and that each source is cited with [n] somewhere.
- _theme: one of water, heat, air, energy, waste, storm (picks the cover mascot and the app colours).
- _keywords: 2-4 extra words the sources use for this topic, including the Indonesian ones when a source
  is Indonesian (e.g. ["banjir", "flood"]).

## Facts
- Every number, date, name and place comes from a source you opened, or from calc.py. Never invent.
  A script checks every number in stat.N.value, story.* and cover.*: it must be in a source page or
  be a value calc.py computes. Numbers typed into calc.py are inputs and need a source too.
- Put [n] tags (n = _sources entry) at the end of sentences that use a source.
- Paraphrase. No quote longer than 10 words.

## Physics
- One equation from the SMP / early SMA curriculum, written in Unicode (², ⁻⁵, ρ, μ, ×, ÷).
- Write calc.py (standard library only, no network, no files) that computes every value in the
  worked example, the table, the graph (_graph.N.raw) and any number in the text you calculated. It
  prints one JSON object. State the simplifications in physics.assumptions.

## Writing
- A 13-year-old reader: short sentences, one idea each, explain hard words in the same sentence.
- Keep to schema/limits.json. Fill every key. Use "" only where the schema allows it.
- Quiz: 3 questions, 4 options each, exactly one correct, not all the same letter.
  quiz.answer_key = "Answer key: 1B · 2A · 3C" (EN) / "Kunci: 1B · 2A · 3C" (ID).
- Mini lab: cheap household items, no flame, no heat, no electricity from the mains, no chemicals
  beyond salt, sugar, flour, vinegar, baking soda. Children film only their hands.
- _quiz_explain (app only): for each printed question "1"-"3", "why" the right answer is right (one
  sentence, max 140 chars) and optional "wrong": {"a": "...", ...} for wrong options only (max 100).
- _quiz_pool (app only): 6 extra questions (at least 4), each {question, options (4), answer (index 0-3),
  explanation}, for "Try the quiz again".
- _lab_rubric (app only): {must_show: 2-4 things the photos must show, safety: [...], pass_if: one
  sentence}. Write it in Bahasa Indonesia in id.json.
- XP: section XP 10 + 20 + 30, guide.xp "+60 XP", badge.xp "0 / 60 XP".

## Images
- Only reusable images: NASA, NOAA, USGS (public domain), ESA/Copernicus (credit), Wikimedia Commons
  with a CC licence (credit author + licence), BMKG. No news-agency photos, no children, no
  identifiable private people. Fill _images with source_url, license and credit. If none fits, set it
  to null and write "Illustration by ELIOS" in the credit.
- source_url is the direct ORIGINAL image file (https, image/jpeg or image/png, under 30 MB), not the
  web page about it and not a thumbnail. Wikimedia: the upload.wikimedia.org original (no /thumb/).
  NASA/NOAA/USGS: the largest rendition offered. The cover photo needs a long side of at least
  1600 px, the story photo 1200 px, and both must be sharp (no haze, motion blur or heavy JPEG blocks);
  a script rejects the rest. file is a plain name such as cover.jpg or story.jpg. Never reuse a URL
  from the example files.
- story.image: when your main source is a NASA, NOAA, USGS or ESA article, use that article's main
  image. Open the article and copy the image file url of the largest version (the "_lrg" or original
  file when it is under 30 MB). The caption says what the photo shows and when it was taken, with the [n]
  tag. The credit names the agency and the image ID (e.g. "NASA astronaut photograph ISS075-E-188830").
  Set story.image to null only if the main source has no reusable image.
- NASA Earth Observatory now lives at science.nasa.gov/earth/earth-observatory/ and its images at
  assets.science.nasa.gov. The old earthobservatory.nasa.gov and eoimages.gsfc.nasa.gov urls are gone.
- Every source url is opened by a script after you finish. Invented or guessed urls fail the issue.

## Budget
- The free API allows few requests. Use at most 6 web searches and 8 page fetches for research.
- Write en.json first, then id.json, calc.py and sources.md. Write each file once; don't re-read
  files you wrote.

## Files
- Write only en.json, id.json, calc.py and sources.md inside issues/<date>/. Other files are deleted.
- Don't open scripts/ or tests/. They are for the checks, not for you.
- _issue is two digits: one more than the newest issue in manifest.json, or "01" if it is empty.
- schema/example.en.json and schema/example.calc.py show one complete, valid issue. Copy their shape,
  not their facts.

## id.json
- Same keys, same facts, same correct answers (also in _quiz_pool), same _theme, natural Bahasa Indonesia, decimal comma and dot
  thousands (9,81 · 5.310 · 57,8 jt). Months: JAN FEB MAR APR MEI JUN JUL AGU SEP OKT NOV DES.
- Source titles stay in their original language.
- Also set these labels:
  label.quest_map PETA MISIMU · label.fun_fact TAHUKAH KAMU? · label.timeline LINIMASA ·
  label.equation PERSAMAAN KUNCI · label.example CONTOH SOAL · label.graph GRAFIK ·
  label.tip KATA BULB BUDDY · label.quiz KUIS KILAT · 3 SOAL · CENTANG SATU KOTAK ·
  label.lab LAB MINI · COBA DI RUMAH ATAU SEKOLAH · label.badge LENCANA TERBUKA ·
  quest.1.title Ceritanya · quest.2.title Fisikanya · quest.3.title Misimu
- _per_page:
  [{"guide.stop_label":"Sampul"},
   {"guide.stop_label":"Pos 1 · Ceritanya","section.label":"POS 1 · CERITANYA","section.xp":"+10 XP UNTUK MEMBACA"},
   {"guide.stop_label":"Pos 2 · Fisikanya","section.label":"POS 2 · FISIKANYA","section.xp":"+20 XP UNTUK MENJAWAB"},
   {"guide.stop_label":"Pos 3 · Misimu","section.label":"POS 3 · MISIMU","section.xp":"+30 XP UNTUK DIRAIH"}]
- _replace: {"stop": [["STOP","POS"]], "page ref": [["p.","hlm. "]]}
- Indonesian is about 20% longer: stay within the same limits by writing shorter sentences.
