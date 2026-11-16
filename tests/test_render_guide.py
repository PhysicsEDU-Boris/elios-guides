import json
import shutil
from pathlib import Path

import pytest
from PIL import Image
from pypdf import PdfReader

import render_guide

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def chromium():
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            p.chromium.launch().close()
    except Exception as error:  # browser not installed: run `python -m playwright install chromium`
        pytest.skip(f"Chromium unavailable: {error}")


@pytest.fixture
def issue(tmp_path, chromium):
    folder = tmp_path / "issues" / "2026-11-20"
    folder.mkdir(parents=True)
    en = json.loads((ROOT / "schema/example.en.json").read_text(encoding="utf-8"))
    en["_images"] = {"cover.image": None, "story.image": None, "physics.diagram": None}  # no photos: placeholders
    for lang in ("en", "id"):
        (folder / f"{lang}.json").write_text(json.dumps(dict(en, **{"guide.lang": lang.upper()})), encoding="utf-8")
    return tmp_path, folder


def test_renders_two_four_page_a4_pdfs_and_hd_covers(issue):
    root, folder = issue
    out = render_guide.render("2026-11-20", root)
    assert len(out) == 4
    for pdf in folder.glob("*.pdf"):
        reader = PdfReader(pdf)
        assert len(reader.pages) == 4 and abs(float(reader.pages[0].mediabox.width) - 595) < 1
    for png in folder.glob("*-cover-*.png"):
        assert Image.open(png).size == (1190, 1684)  # the old Figma export size


def test_overflow_blocks_the_issue(issue):
    root, folder = issue
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    en["story.body_1"] = "Long sentence about rivers. " * 400
    (folder / "en.json").write_text(json.dumps(en), encoding="utf-8")
    with pytest.raises(RuntimeError, match="overflows"):
        render_guide.render("2026-11-20", root)
    assert not list(folder.glob("*.pdf"))


def test_key_with_no_place_on_the_page_blocks_the_issue(issue):
    root, folder = issue
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    en["story.typo_key"] = "nowhere to go"
    (folder / "en.json").write_text(json.dumps(en), encoding="utf-8")
    with pytest.raises(RuntimeError, match="story.typo_key"):
        render_guide.render("2026-11-20", root)


def test_missing_photo_file_blocks_the_issue(issue):
    root, folder = issue
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    en["_images"]["cover.image"] = {"file": "cover.jpg"}
    (folder / "en.json").write_text(json.dumps(en), encoding="utf-8")
    with pytest.raises(RuntimeError, match="image did not load"):
        render_guide.render("2026-11-20", root)
