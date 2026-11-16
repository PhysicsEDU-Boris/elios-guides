"""Decide what an edit to issues/<date>/en.json or id.json needs.

Usage: python scripts/resync.py issues/YYYY-MM-DD OLD_FOLDER
OLD_FOLDER holds en.json/id.json before the push. Prints one action:
  export  - printed text changed (or the issue was never exported): render the PDFs again, then publish
  publish - only app fields changed (_quiz_explain, _quiz_pool, _lab_rubric): publish, PDFs stay as they are
  none    - nothing changed
"""
import json
import sys
from pathlib import Path

APP_ONLY = {"_quiz_explain", "_quiz_pool", "_lab_rubric"}  # shown by the app, not printed in the PDF


def load(folder, lang):
    try:
        return json.loads((Path(folder) / f"{lang}.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None


def printed(d):
    return {k: v for k, v in (d or {}).items() if k not in APP_ONLY}


def decide(folder, old):
    new = {l: load(folder, l) for l in ("en", "id")}
    before = {l: load(old, l) for l in ("en", "id")}
    if before == new:
        return "none"
    if not any(Path(folder).glob("*.pdf")) or any(printed(before[l]) != printed(new[l]) for l in ("en", "id")):
        return "export"
    return "publish"


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    print(decide(sys.argv[1], sys.argv[2]))
