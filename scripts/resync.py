"""Decide what an edit to issues/<date>/en.json or id.json needs, and mark Figma refills.

Usage: python scripts/resync.py issues/YYYY-MM-DD OLD_FOLDER
OLD_FOLDER holds en.json/id.json before the push. Prints one action:
  figma   - printed text changed after the Figma fill: writes resync.json for the Claude task
  publish - only app fields changed (_quiz_explain, _quiz_pool, _lab_rubric): publish without Figma
  none    - nothing to do (no change, not exported yet, or Figma already has this text)
"""
import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

APP_ONLY = {"_quiz_explain", "_quiz_pool", "_lab_rubric"}  # shown by the app, not printed in the PDF


def load(folder, lang):
    try:
        return json.loads((Path(folder) / f"{lang}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def printed(d):
    return {k: v for k, v in (d or {}).items() if k not in APP_ONLY}


def content_sha(folder):
    return {l: hashlib.sha256((Path(folder) / f"{l}.json").read_bytes()).hexdigest() for l in ("en", "id")}


def decide(folder, old, now=None):
    folder = Path(folder)
    new = {l: load(folder, l) for l in ("en", "id")}
    before = {l: load(old, l) for l in ("en", "id")}
    figma = load(folder, "figma") or {}
    if before == new or not figma:
        return "none"  # unchanged, or not in Figma yet (the next daily run fills it with this text)
    sha = content_sha(folder)
    if all(printed(before[l]) == printed(new[l]) for l in ("en", "id")):
        return "publish"
    if figma.get("content_sha") == sha:
        return "none"  # the Claude task pushed this text together with figma.json
    changed = sorted(k for l in ("en", "id") for k in set(printed(before[l])) | set(printed(new[l]))
                     if printed(before[l]).get(k) != printed(new[l]).get(k))
    (folder / "resync.json").write_text(json.dumps({
        "reason": f"printed text changed: {', '.join(dict.fromkeys(changed))[:300]}",
        "content_sha": sha,
        "created": (now or datetime.now(timezone.utc)).isoformat(timespec="seconds"),
    }, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return "figma"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(decide(sys.argv[1], sys.argv[2]))
