"""Fill `sources` and `terms` for catalogue entries published before repeat protection existed.

Usage: python scripts/backfill_repeats.py CATALOGUE.json [GIT_REF]   (default ref: origin/published)
Reads each missing entry's en.json from GIT_REF and rewrites only the local catalogue copy; the published
branch is never changed. Entries whose file cannot be read are left as they are.
"""
import json
import subprocess
import sys

import repeats


def backfill(guides, read):
    filled = 0
    for g in guides[:repeats.WINDOW]:
        if "sources" in g and "terms" in g:
            continue
        try:
            d = json.loads(read(g["content"]["en"]))
        except (KeyError, TypeError, ValueError, OSError):
            continue
        g["sources"], g["terms"] = repeats.issue_sources(d), repeats.issue_terms(d)
        filled += 1
    return filled


if __name__ == "__main__":
    path, ref = sys.argv[1], (sys.argv[2] if len(sys.argv) > 2 else "origin/published")
    manifest = json.load(open(path, encoding="utf-8"))

    def read(name):
        return subprocess.run(["git", "show", f"{ref}:{name}"], capture_output=True, text=True, check=True).stdout

    n = backfill(manifest.get("guides") or [], read)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, indent=2, ensure_ascii=False)
    print(f"backfilled repeat fields for {n} catalogue entries")
