"""Validate exported issue data and add only public assets to the Pages archive.

Usage: python scripts/publish.py YYYY-MM-DD SOURCE_ROOT SITE_ROOT [--check-sources]
Never runs issue-supplied Python or copies repository credentials/configuration.
"""
import json
import re
import shutil
import sys
import tempfile
from datetime import date as Date
from pathlib import Path

from PIL import Image
from pypdf import PdfReader

import check_sources
import update_manifest
import validate


def publish(date, source, site, check_urls=False):
    if not re.fullmatch(r"\d{4}-\d{2}-\d{2}", date) or Date.fromisoformat(date).isoformat() != date:
        raise ValueError("invalid issue date")
    source, site = Path(source), Path(site)
    folder = source / "issues" / date
    if folder.is_symlink() or any(p.is_symlink() for p in folder.rglob("*")):
        raise ValueError("issue contains symlinks")
    manifest = site / "manifest.json"
    catalogue = json.loads(manifest.read_text()) if manifest.exists() else {"guides": [], "updated": None}
    # Re-exporting a corrected issue replaces its entry while keeping all other dates.
    checking = dict(catalogue, guides=[g for g in catalogue["guides"] if g["date"] != date])
    with tempfile.TemporaryDirectory() as temp:
        check_manifest = Path(temp) / "manifest.json"
        check_manifest.write_text(json.dumps(checking))
        errors = validate.check(folder, check_manifest)
    checks = json.loads((folder / "check.json").read_text())
    if not isinstance(checks, list) or not checks:
        errors.append("fact-check must contain verified claims")
    if check_urls:
        errors += check_sources.errors(folder)
    en = json.loads((folder / "en.json").read_text())
    id_ = json.loads((folder / "id.json").read_text())
    if en.get("_example") or id_.get("_example"):
        errors.append("cannot publish an example")
    if en.get("_issue") != id_.get("_issue") or en.get("_slug") != id_.get("_slug"):
        errors.append("English and Indonesian issue identifiers differ")
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    if not re.fullmatch(r"elios-guide-[a-zA-Z0-9-]+", base):
        errors.append("invalid asset filename")
    if errors:
        raise ValueError("\n".join(errors))
    names, photos = update_manifest.public_files(en)
    for lang in ("en", "id"):
        pdf = f"{base}-{lang}.pdf"
        png = f"{base}-cover-{lang}.png"
        if len(PdfReader(folder / pdf).pages) != 4:
            raise ValueError(f"{pdf} must have four pages")
        with Image.open(folder / png) as image:
            if image.format != "PNG":
                raise ValueError(f"{png} must be a PNG")
            image.verify()
    names += [n for n in photos if (folder / n).is_file()]  # validate.check already checked photo rules
    # All validation completes before touching the previously published site.
    target = site / "issues" / date
    target.mkdir(parents=True, exist_ok=True)
    for name in names:
        shutil.copyfile(folder / name, target / name)
    for name in photos:
        if name not in names:
            (target / name).unlink(missing_ok=True)  # a re-publish without a photo must not keep the old one
    if not manifest.exists():
        manifest.write_text(json.dumps(catalogue))
    entry = update_manifest.update(date, site)
    (site / ".nojekyll").touch()
    return entry


if __name__ == "__main__":
    if len(sys.argv) not in (4, 5):
        sys.exit(__doc__)
    print(json.dumps(publish(*sys.argv[1:4], check_urls="--check-sources" in sys.argv), ensure_ascii=False))
