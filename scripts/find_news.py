"""Find real, recent environmental news before the writer runs, so every issue starts from a dated article
a script has opened instead of a topic page the model guessed (the cause of most failed runs).

Usage: python scripts/find_news.py YYYY-MM-DD --manifest .gemini/published-manifest.json --out .gemini/news-candidates.json
Reads RSS feeds, keeps items from the last 7 days whose title or summary names a physics topic, drops
articles the catalogue already used, opens each page and keeps its article text. `news` entries are
events (source 1); `primary` entries are agency pages for the primary source.
"""
import argparse
import html
import json
import re
import sys
from datetime import date, datetime, timedelta
from email.utils import parsedate_to_datetime
from pathlib import Path

import requests

from check_sources import get, page_text, verdict
from repeats import WINDOW, norm_url

FEEDS = [  # (url, publisher, primary)
    ("https://www.mongabay.co.id/feed/", "Mongabay Indonesia", False),
    ("https://news.mongabay.com/feed/", "Mongabay", False),
    ("https://www.antaranews.com/rss/warta-bumi.xml", "ANTARA", False),
    ("https://en.antaranews.com/rss/news.xml", "ANTARA", False),
    ("https://news.un.org/feed/subscribe/en/news/topic/climate-change/feed/rss.xml", "UN News", False),
    ("https://www.sciencedaily.com/rss/earth_climate.xml", "ScienceDaily", False),
    ("https://earthobservatory.nasa.gov/feeds/earth-observatory.rss", "NASA Earth Observatory", True),
    ("https://science.nasa.gov/feed/", "NASA", True),
    ("https://www.noaa.gov/rss.xml", "NOAA", True),
]
# GEMINI.md topics, English and Indonesian stems.
TOPIC = re.compile(r"\b(flood|banjir|rain|hujan|heat|panas|temperature|suhu|drought|kekeringan|storm|badai|cyclone|siklon|"
                   r"wind|angin|wave|gelombang|tsunami|tide|rob\b|sea level|permukaan laut|pollution|polusi|air quality|"
                   r"kualitas udara|smog|haze|kabut asap|wildfire|kebakaran|landslide|longsor|waste|sampah|plastic|plastik|"
                   r"recycl|daur ulang|energy|energi|solar|surya|electric|listrik|power plant|pembangkit|coal|batu bara|"
                   r"emission|emisi|glacier|karhutla|radiation|radiasi|noise|kebisingan)", re.I)
LOCAL = re.compile(r"\b(indonesia|jakarta|java|jawa|sumatra|sumatera|kalimantan|borneo|sulawesi|papua|bali|nusa|"
                   r"southeast asia|asia tenggara|malaysia|philippines|vietnam|thailand)\b", re.I)
PER_FEED, MAX_FETCH, KEEP_NEWS, KEEP_PRIMARY, MAX_TEXT = 15, 24, 8, 5, 5000


def field(block, name):
    m = re.search(rf"(?is)<{name}\b[^>]*>(.*?)</{name}>", block)
    return html.unescape(re.sub(r"(?s)<!\[CDATA\[(.*?)\]\]>", r"\1", m.group(1))).strip() if m else ""


def parse_date(s):
    try:
        return parsedate_to_datetime(s).date()
    except (TypeError, ValueError):
        try:
            return datetime.fromisoformat(s.strip().replace("Z", "+00:00")).date()
        except (AttributeError, ValueError):
            return None


def items(xml):
    """(title, link, date, summary) of each RSS <item> or Atom <entry>; regex, because NASA's feed is not valid XML."""
    xml = xml.decode("utf-8", "replace") if isinstance(xml, bytes) else xml
    for m in re.finditer(r"(?is)<(item|entry)\b.*?</\1>", xml):
        block = m.group(0)
        link = field(block, "link") or (re.search(r'(?i)<link\b[^>]*href="([^"]+)"', block) or [None, ""])[1]
        summary = re.sub(r"<[^>]+>", " ", field(block, "description") or field(block, "summary"))
        yield field(block, "title"), link, parse_date(field(block, "pubDate") or field(block, "updated") or field(block, "published")), summary


def score(title, summary, text):
    head = f"{title} {summary}"
    return 3 * bool(LOCAL.search(head)) + bool(LOCAL.search(text)) + len(set(m.lower() for m in TOPIC.findall(head)))


def find(day, used, fetch=get):
    since = day - timedelta(days=7)
    found = []
    for url, publisher, primary in FEEDS:
        try:
            r = fetch(url)
            entries = list(items(r.content))[:PER_FEED] if r.status_code == 200 else []
        except requests.RequestException as e:
            print(f"feed {url}: {type(e).__name__}", file=sys.stderr)
            continue
        for title, link, d, summary in entries:
            if link and d and since <= d <= day and TOPIC.search(title) and norm_url(link) not in used:
                found.append({"url": link, "title": title, "publisher": publisher, "date": d.isoformat(),
                              "primary": primary, "summary": re.sub(r"\s+", " ", summary).strip()[:300]})
    found.sort(key=lambda c: score(c["title"], c["summary"], ""), reverse=True)
    out = {"news": [], "primary": []}
    for c in found[:MAX_FETCH]:
        kind = "primary" if c["primary"] else "news"
        if len(out[kind]) >= (KEEP_PRIMARY if c["primary"] else KEEP_NEWS):
            continue
        try:
            r = fetch(c["url"])
        except requests.RequestException:
            continue
        if r.status_code != 200 or verdict(c["url"], r):
            continue
        text = page_text(r.text)
        if len(text) < 800 or len(re.findall(r"\d", text)) < 5:  # no facts to write from
            continue
        out[kind].append({**c, "url": r.url, "text": text[:MAX_TEXT]})
    for kind in out:
        out[kind].sort(key=lambda c: score(c["title"], c["summary"], c["text"]), reverse=True)
    return out


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("date")
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args(argv)
    try:
        guides = json.loads(Path(a.manifest).read_text(encoding="utf-8")).get("guides") or []
    except (OSError, ValueError):
        guides = []
    used = {u for g in guides[:WINDOW] for u in g.get("sources") or []}
    out = find(date.fromisoformat(a.date), used)
    Path(a.out).write_text(json.dumps(out, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(out['news'])} news and {len(out['primary'])} primary candidates")
    for c in out["news"] + out["primary"]:
        print(f"  {c['date']} {c['publisher']}: {c['title'][:90]}")
    return 0 if out["news"] else 1


if __name__ == "__main__":
    sys.exit(main())
