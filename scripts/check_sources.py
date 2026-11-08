"""Open every _sources url in issues/<date>/en.json and fail the ones that don't exist.

Usage: python scripts/check_sources.py issues/YYYY-MM-DD
A source fails if it can't be reached, returns 404/410/5xx, or redirects to the same place a made-up
url on that site redirects to (an invented article url that lands on the section's front page).
"""
import json
import sys
from pathlib import Path

import requests

UA = "Mozilla/5.0 (compatible; elios-guides-bot/1.0; +https://github.com/PhysicsEDU-Boris/elios-guides)"
# ponytail: 401/403/429 mean "a bot blocker answered", not "missing"; they pass with a note. If a site
# hides missing pages behind them, add a browser-based check.
BLOCKED = {401, 403, 429}


def get(url):
    r = requests.get(url, timeout=20, allow_redirects=True, headers={"User-Agent": UA}, stream=True)
    r.close()
    return r


def check(url):
    try:
        r = get(url)
    except requests.RequestException as e:
        return f"cannot be reached ({type(e).__name__})"
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


def main(folder):
    sources = json.loads((Path(folder) / "en.json").read_text(encoding="utf-8")).get("_sources") or []
    errs = [f"source {s.get('n')} {s.get('url')} {why}" for s in sources if (why := check(str(s.get("url", "")))) ]
    for e in errs:
        print(f"- {e}")
    return 1 if errs else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: check_sources.py issues/YYYY-MM-DD")
    sys.exit(main(sys.argv[1]))
