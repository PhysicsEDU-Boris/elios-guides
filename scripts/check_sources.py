"""Open every _sources url in issues/<date>/en.json, fail the missing ones, and fact-check the issue
against the pages that were opened.

Usage: python scripts/check_sources.py issues/YYYY-MM-DD
A source fails if it can't be reached, returns 404/410/5xx, redirects to the same place a made-up
url on that site redirects to (an invented article url that lands on the section's front page),
is never cited ([n]), or does not mention the topic (fewer than 2 topic keywords in its article text).
Every number in stat.N.value, story.* and cover.* must appear in a source page or be a value calc.py
computed (numbers typed into calc.py are inputs; they need a source too).
"""
import ast
import html
import json
import re
import sys
from pathlib import Path

import requests

from validate import close, flat_numbers, parse_numbers

UA = "Mozilla/5.0 (compatible; elios-guides-bot/1.0; +https://github.com/PhysicsEDU-Boris/elios-guides)"
# ponytail: 401/403/429 mean "a bot blocker answered", not "missing"; they pass with a note. If a site
# hides missing pages behind them, add a browser-based check. Their text is unknown, so they confirm nothing.
BLOCKED = {401, 403, 429}
# Template boilerplate, not news facts.
EXEMPT = {"cover.read_time", "cover.level", "cover.xp_total", "cover.subject", "story.image_credit"}
MAX_TEXT = 3_000_000


def get(url):
    return requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": UA})


def verdict(url, r):
    if r.status_code in BLOCKED:
        return None
    if r.status_code >= 400:
        return f"returns HTTP {r.status_code}"
    if r.history:
        # Soft 404: if a page that surely doesn't exist lands on the same url, so does this one.
        try:
            probe = get(url.rstrip("/") + "-elios-missing-page-check")
        except requests.RequestException:
            return None
        if probe.url == r.url:
            return f"redirects to {r.url}, like a missing page does"
    return None


def check(url):
    try:
        return verdict(url, get(url))
    except requests.RequestException as e:
        return f"cannot be reached ({type(e).__name__})"


def page_text(page):
    """Visible article text of an HTML page, lower case (menus, footers and related links removed)."""
    t = re.sub(r"(?is)<(script|style|noscript|nav|header|footer|aside|form|svg)\b.*?</\1>", " ", page[:MAX_TEXT])
    m = re.search(r"(?is)<article\b.*?</article>", t) or re.search(r"(?is)<main\b.*?</main>", t)
    t = html.unescape(re.sub(r"<[^>]+>", " ", m.group(0) if m else t))
    return re.sub(r"\s+", " ", t).lower()


def keywords(en):
    words = re.split(r"[-\s,]+", str(en.get("_slug", ""))) + re.split(r"[\s,]+", str(en.get("cover.place", "")))
    kws = {w.lower() for w in words if len(w) >= 4} | {str(k).lower() for k in en.get("_keywords") or [] if str(k).strip()}
    return kws


def calc_values(folder):
    """calc.out.json values that calc.py computed, i.e. not typed in as a literal number."""
    try:
        values = flat_numbers(json.loads((folder / "calc.out.json").read_text(encoding="utf-8")))
        tree = ast.parse((folder / "calc.py").read_text(encoding="utf-8"))
    except (OSError, ValueError, SyntaxError):
        return []
    literals = [float(n.value) for n in ast.walk(tree) if isinstance(n, ast.Constant) and type(n.value) in (int, float)]
    return [v for v in values if not any(v == lit for lit in literals)]


def fact_errors(en, texts, computed):
    errs = []
    # "20 million years" in a source is 20,000,000, not a source for "20 s".
    sourced = [max(cands) for t in texts for lang in ("en", "id") for cands in parse_numbers(t, lang)]
    keys = [f"stat.{i}.value" for i in (1, 2, 3)] + [k for k in en if k.startswith(("story.", "cover.")) and k not in EXEMPT]
    for k in keys:
        for cands in parse_numbers(en.get(k, ""), "en"):
            if not any(close(n, sourced) or close(n, computed) for n in cands):
                errs.append(f"{k} = {en.get(k)!r}: {min(cands):g} is not in any source page or computed by calc.py")
    return errs


def errors(folder):
    folder = Path(folder)
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    sources = en.get("_sources") or []
    cited = {int(n) for k, v in en.items() if not k.startswith("_") for n in re.findall(r"\[(\d+)\]", str(v))}
    kws = keywords(en)
    errs, texts = [], []
    for s in sources:
        n, url = s.get("n"), str(s.get("url", ""))
        if n not in cited:
            errs.append(f"source {n} {url} is never cited with [{n}]")
        try:
            r = get(url)
        except requests.RequestException as e:
            errs.append(f"source {n} {url} cannot be reached ({type(e).__name__})")
            continue
        if why := verdict(url, r):
            errs.append(f"source {n} {url} {why}")
            continue
        if r.status_code in BLOCKED:
            continue
        text = page_text(r.text)
        texts.append(text)
        found = {k for k in kws if re.search(rf"\b{re.escape(k)}", text)}
        if len(found) < min(2, len(kws)):
            errs.append(f"source {n} {url} is off-topic: mentions {sorted(found) or 'none'} of the topic keywords {sorted(kws)}")
    return errs + fact_errors(en, texts, calc_values(folder))


def main(folder):
    errs = errors(folder)
    for e in errs:
        print(f"- {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check_sources.py issues/YYYY-MM-DD")
    sys.exit(main(sys.argv[1]))
