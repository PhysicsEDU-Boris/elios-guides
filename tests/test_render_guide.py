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


def test_every_formula_typesets_and_fits_its_card(chromium):
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 595, "height": 842})
        page.goto((ROOT / "render" / "guide.html").as_uri())
        page.evaluate("document.fonts.ready")
        bad = page.evaluate("""(bank) => { const el = document.querySelector('[data-key="physics.equation"]'); el.style.fontSize = '16px';
            return bank.filter(f => { katex.render(f.latex, el, { throwOnError: true }); return el.scrollWidth > el.clientWidth; }).map(f => f.id); }""",
                            render_guide_bank())
        browser.close()
    assert bad == []


def render_guide_bank():
    return list(render_guide.BANK.values())


def test_latex_braces_are_not_reported_as_leftover_placeholders(issue):
    root, folder = issue
    f = render_guide.BANK["planet-equilibrium-temperature"]  # latex has { } and fractions
    for lang in ("en", "id"):
        d = json.loads((folder / f"{lang}.json").read_text(encoding="utf-8"))
        d["_formula"], d["physics.equation"] = f["id"], f["text"]
        for i in range(1, 6):
            d[f"legend.{i}.symbol"] = f["symbols"][i - 1][0] if i <= len(f["symbols"]) else ""
        (folder / f"{lang}.json").write_text(json.dumps(d), encoding="utf-8")
    assert len(render_guide.render("2026-11-20", root)) == 4
