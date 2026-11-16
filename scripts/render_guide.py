"""Render issues/<date>/en.json + id.json into the 4-page A4 PDFs and cover PNGs (replaces the Figma export).

Usage: python scripts/render_guide.py YYYY-MM-DD
Template: render/guide.html (+ render/fill.js). Fails when a key has no place on the page, text is left
as {placeholder}, a page overflows, or an image does not load, so a bad issue is never published.
"""
import json
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parent.parent
BANK = {f["id"]: f for f in json.loads((ROOT / "schema" / "formulas.json").read_text(encoding="utf-8"))}
MASCOT = {"waste": "mascot-binb", "heat": "flame", "energy": "bulb", "air": "tree", "storm": "tree", "water": "tree"}
PX = 96 / 72  # CSS px per PDF point: the 595 x 842 px layout becomes a 595 x 842 pt A4 page


def render(date, root=ROOT):
    folder = Path(root) / "issues" / date
    template, fill = ROOT / "render" / "guide.html", (ROOT / "render" / "fill.js").read_text(encoding="utf-8")
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    out = []
    with sync_playwright() as p:
        browser = p.chromium.launch()
        for lang in ("en", "id"):
            content = json.loads((folder / f"{lang}.json").read_text(encoding="utf-8"))
            images = {k: (folder / Path(v["file"]).name).as_uri() for k, v in (content.get("_images") or {}).items() if v}
            page = browser.new_page(viewport={"width": 595, "height": 842}, device_scale_factor=2)
            page.goto(template.as_uri())
            page.evaluate("document.fonts.ready")
            result = page.evaluate(fill, {"content": content, "images": images,
                                          "mascot": MASCOT.get(content.get("_theme"), "bulb"),
                                          "latex": BANK.get(content.get("_formula"), {}).get("latex"),
                                          "theme": content.get("_theme")})
            page.wait_for_function("[...document.images].every(i => i.complete)")
            broken = page.evaluate("[...document.images].filter(i => !i.naturalWidth).map(i => i.src.split('/').pop())")
            bad = [f"{lang}: {name}: {result[name]}" for name in ("missing", "leftover") if result[name]]
            bad += [f"{lang}: page {f['page']} overflows ({f['used']} > {f['max']} px)" for f in result["fit"] if not f["ok"]]
            bad += [f"{lang}: the equation is wider than its card"] if not result["eq"]["ok"] else []
            bad += [f"{lang}: image did not load: {b}" for b in broken]
            if bad:
                raise RuntimeError("; ".join(bad))
            pdf_path, png_path = folder / f"{base}-{lang}.pdf", folder / f"{base}-cover-{lang}.png"
            page.pdf(path=str(pdf_path), width=f"{595 * PX}px", height=f"{842 * PX}px", scale=PX, print_background=True)
            pages = len(PdfReader(pdf_path).pages)
            if pages != 4:
                raise RuntimeError(f"{lang}: PDF has {pages} pages, expected 4")
            page.locator("#p1").screenshot(path=str(png_path))  # 1190 x 1684
            page.close()
            out += [pdf_path, png_path]
        browser.close()
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: render_guide.py YYYY-MM-DD")
    for path in render(sys.argv[1]):
        print(path.relative_to(ROOT))
