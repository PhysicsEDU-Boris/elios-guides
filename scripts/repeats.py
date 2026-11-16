"""Repeat protection: the same news event must not become a second guide under a new name.

Two offline, deterministic checks against the last WINDOW catalogue entries:
  - sources: the main source article (_sources[0]) was used before, or two or more sources were;
  - terms: the title, topic, slug, place and keywords share too many words (Jaccard >= SIMILAR).
The manifest entry stores `sources` and `terms` (see update_manifest.py) so old guides need no re-reading.
"""
import re
from urllib.parse import urlparse

WINDOW = 60  # catalogue entries, about two months
SIMILAR = 0.4
STOP = {"the", "and", "for", "with", "from", "how", "why", "what", "are", "was", "this", "that", "yang", "dan", "di", "ke",
        "dari", "untuk", "pada", "dengan", "ini", "itu", "indonesia", "usa", "news", "guide"}


def norm_url(url):
    p = urlparse(str(url or "").strip().lower())
    return f"{p.netloc.removeprefix('www.')}{p.path.rstrip('/')}" if p.netloc else ""


def terms(*texts):
    """Lower-case words of 3+ letters without stop words, plural 's' removed: 'floods' == 'flood'."""
    words = {w[:-1] if len(w) > 3 and w.endswith("s") else w for t in texts for w in re.findall(r"[^\W\d_]{3,}", str(t).lower())}
    return sorted(words - STOP)


def issue_terms(d):
    return terms(d.get("cover.title"), d.get("story.title"), d.get("cover.topic"), d.get("_slug", "").replace("-", " "),
                 d.get("cover.place"), *(d.get("_keywords") or []))


def issue_sources(d):
    return sorted({u for u in (norm_url(s.get("url")) for s in d.get("_sources") or [] if isinstance(s, dict)) if u})


def guide_terms(g):
    return set(g.get("terms") or terms((g.get("title") or {}).get("en"), (g.get("topic") or {}).get("en"), str(g.get("slug", "")).replace("-", " ")))


def check(en, guides):
    """Problems for a new issue `en` against catalogue entries `guides` (newest first)."""
    errs = []
    mine, srcs = set(issue_terms(en)), issue_sources(en)
    main = norm_url(((en.get("_sources") or [{}])[0] or {}).get("url")) or None
    for g in guides[:WINDOW]:
        old = set(g.get("sources") or [])
        shared = old & set(srcs)
        if main and main in old:
            errs.append(f"main source {main} was already used on {g.get('date')}")
        elif len(shared) >= 2:
            errs.append(f"{len(shared)} sources were already used on {g.get('date')}: {', '.join(sorted(shared))[:160]}")
        theirs = guide_terms(g)
        score = len(mine & theirs) / len(mine | theirs) if mine | theirs else 0
        if score >= SIMILAR:
            errs.append(f"looks like the issue of {g.get('date')} ({score:.0%} of words shared: {', '.join(sorted(mine & theirs))[:120]})")
    return errs
