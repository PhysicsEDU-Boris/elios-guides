"""Cover-photo fallback: licensed candidates from Wikimedia Commons (CC0, public domain, CC BY, CC BY-SA).

Used by fetch_images.py --drop-failed when the writer's cover photo failed or was null. News-site photos
are never candidates: they are copyrighted. Returns _images entries ready for en.json/id.json.
"""
import re

import requests

API = "https://commons.wikimedia.org/w/api.php"
UA = "elios-guides-bot/1.0 (+https://github.com/PhysicsEDU-Boris/elios-guides)"
OK_LICENSE = re.compile(r"^(CC0|Public domain|PD\b|CC BY(-SA)? \d)", re.I)


def clean(html):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", "", html or "")).strip()


def candidates(en, min_side=1600, limit=5):
    """Commons photos for the place and keywords of this issue, big enough for the cover."""
    query = " ".join([en.get("cover.place", "")] + list(en.get("_keywords") or [])).strip()
    if not query:
        return []
    params = {"action": "query", "format": "json", "generator": "search", "gsrnamespace": 6, "gsrlimit": 20,
              "gsrsearch": f"{query} filetype:bitmap", "prop": "imageinfo", "iiprop": "url|size|mime|extmetadata",
              "iiextmetadatafilter": "LicenseShortName|Artist"}
    pages = (requests.get(API, params=params, timeout=30, headers={"User-Agent": UA}).json().get("query") or {}).get("pages") or {}
    out = []
    for page in sorted(pages.values(), key=lambda p: p.get("index", 0)):
        info = (page.get("imageinfo") or [{}])[0]
        meta = info.get("extmetadata") or {}
        lic = clean((meta.get("LicenseShortName") or {}).get("value"))
        if info.get("mime") != "image/jpeg" or max(info.get("width", 0), info.get("height", 0)) < min_side or not OK_LICENSE.match(lic):
            continue
        author = clean((meta.get("Artist") or {}).get("value")) or "Unknown author"
        out.append({"file": "cover.jpg", "source_url": info["url"].split("?")[0],  # Commons appends utm tracking parameters "license": lic, "credit": f"{author[:80]} / Wikimedia Commons"})
    return out[:limit]
