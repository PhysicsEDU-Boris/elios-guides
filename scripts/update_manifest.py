"""Add (or replace) one issue in manifest.json, newest first, last 365 kept.

Usage: python scripts/update_manifest.py YYYY-MM-DD
"""
import json
import hashlib
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WIB = timezone(timedelta(hours=7))
KEEP = 365


def update(date, root=ROOT, now=None):
    root = Path(root)
    folder = f"issues/{date}"
    en, id_ = (json.loads((root / folder / f"{l}.json").read_text(encoding="utf-8")) for l in ("en", "id"))
    if en.get("_example") or id_.get("_example"):
        raise SystemExit("refusing to publish an _example issue")
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    for l in ("en", "id"):
        for name in (f"{base}-{l}.pdf", f"{base}-cover-{l}.png"):
            if not (root / folder / name).is_file():
                raise SystemExit(f"missing {folder}/{name}; run export_figma.py first")
    revision = hashlib.sha256()
    for lang in ("en", "id"):
        for name in (f"{base}-{lang}.pdf", f"{base}-cover-{lang}.png"):
            revision.update((root / folder / name).read_bytes())
    xp = re.search(r"\d+", en.get("guide.xp", ""))
    entry = {
        "revision": revision.hexdigest(),
        "date": date, "issue": en["_issue"], "slug": en["_slug"], "xp": int(xp.group()) if xp else 60,
        "title": {"en": en["cover.title"], "id": id_["cover.title"]},
        "topic": {"en": en["cover.topic"], "id": id_["cover.topic"]},
        "cover": {l: f"{folder}/{base}-cover-{l}.png" for l in ("en", "id")},
        "pdf": {l: f"{folder}/{base}-{l}.pdf" for l in ("en", "id")},
        "content": {l: f"{folder}/{l}.json" for l in ("en", "id")},
    }
    path = root / "manifest.json"
    manifest = json.loads(path.read_text(encoding="utf-8"))
    guides = [g for g in manifest.get("guides") or [] if g.get("date") != date] + [entry]
    guides.sort(key=lambda g: g["date"], reverse=True)
    manifest["guides"] = guides[:KEEP]
    manifest["updated"] = (now or datetime.now(WIB)).astimezone(WIB).isoformat(timespec="seconds")
    path.write_text(json.dumps(manifest, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return entry


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: update_manifest.py YYYY-MM-DD")
    print(json.dumps(update(sys.argv[1]), ensure_ascii=False))
