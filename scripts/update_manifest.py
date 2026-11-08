"""Add (or replace) one issue in manifest.json, newest first, last 365 kept.

Usage: python scripts/update_manifest.py YYYY-MM-DD
Manifest v2 only adds fields; every v1 field keeps its name and format (see README).
"""
import json
import hashlib
import re
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
WIB = timezone(timedelta(hours=7))
KEEP = 365
THEMES = ("water", "heat", "air", "energy", "waste", "storm")
XP_PARTS = {"story": 10, "physics": 20, "quiz": 10, "lab": 20}
PHOTOS = ("photo.jpg", "photo-800.jpg")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def public_files(en):
    """Every file of the issue that is published, in a fixed order (photos only if present)."""
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    return ["en.json", "id.json"] + [n for l in ("en", "id") for n in (f"{base}-{l}.pdf", f"{base}-cover-{l}.png")], list(PHOTOS)


def photo_entry(root, folder, en, id_):
    img = (en.get("_images") or {}).get("cover.image")
    if not img or not all((root / folder / n).is_file() for n in PHOTOS):
        return None  # the app shows the topic illustration
    with Image.open(root / folder / "photo.jpg") as im:
        w, h = im.size
    return {
        "src": f"{folder}/photo.jpg", "thumb": f"{folder}/photo-800.jpg",
        "w": w, "h": h, "caption": {"en": en.get("cover.image_caption", ""), "id": id_.get("cover.image_caption", "")},
        "credit": img.get("credit", ""), "license": img.get("license", ""), "source_url": img.get("source_url", ""),
    }


def update(date, root=ROOT, now=None):
    root = Path(root)
    folder = f"issues/{date}"
    en, id_ = (json.loads((root / folder / f"{l}.json").read_text(encoding="utf-8")) for l in ("en", "id"))
    if en.get("_example") or id_.get("_example"):
        raise SystemExit("refusing to publish an _example issue")
    if en.get("_theme") not in THEMES:
        raise SystemExit(f"_theme {en.get('_theme')!r} must be one of {', '.join(THEMES)}")
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    required, optional = public_files(en)
    for name in required:
        if not (root / folder / name).is_file():
            raise SystemExit(f"missing {folder}/{name}; run export_figma.py first")
    revision = hashlib.sha256()
    for name in required + [n for n in optional if (root / folder / n).is_file()]:
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
        # v2 (additive): v1 "xp" stays the total int, so the split lives in "xp_parts".
        "schema": 2,
        "theme": en["_theme"],
        "photo": photo_entry(root, folder, en, id_),
        "content_sha": {l: sha((root / folder / f"{l}.json").read_bytes()) for l in ("en", "id")},
        "xp_parts": dict(XP_PARTS),
        "pages": len(PdfReader(root / folder / f"{base}-en.pdf").pages),
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
