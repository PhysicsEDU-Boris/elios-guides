"""Export one issue from Figma → merged PDF + cover PNG per language.

Usage: FIGMA_TOKEN=... python scripts/export_figma.py YYYY-MM-DD
"""
import io
import json
import os
import sys
import time
from pathlib import Path

import requests
from pypdf import PdfWriter

ROOT = Path(__file__).resolve().parent.parent
FILE_KEY = "pBZAnlSJnLGB5Je0tCth12"
API = f"https://api.figma.com/v1/images/{FILE_KEY}"


def get(url, **kw):
    """GET with 3 retries on 429/5xx. Errors never include the token (it is only in headers)."""
    for attempt in range(4):
        r = requests.get(url, timeout=120, **kw)
        if r.status_code != 429 and r.status_code < 500:
            break
        if attempt < 3:
            time.sleep(2 ** (attempt + 1))
    if r.status_code >= 400:
        raise RuntimeError(f"HTTP {r.status_code} from {url.split('?')[0]}")
    return r


def render(ids, fmt, token, scale=None):
    params = {"ids": ",".join(ids), "format": fmt}
    if scale:
        params["scale"] = scale
    data = get(API, params=params, headers={"X-Figma-Token": token}).json()
    if data.get("err"):
        raise RuntimeError(f"Figma error: {data['err']}")
    urls = data.get("images") or {}
    missing = [i for i in ids if not urls.get(i)]
    if missing:
        raise RuntimeError(f"Figma did not render nodes {missing}")
    return [get(urls[i]).content for i in ids]


def export(date, token, root=ROOT):
    folder = Path(root) / "issues" / date
    pages = json.loads((folder / "figma.json").read_text(encoding="utf-8"))
    en = json.loads((folder / "en.json").read_text(encoding="utf-8"))
    base = f"elios-guide-{en['_issue']}-{en['_slug']}"
    out = []
    for lang in ("en", "id"):
        ids = pages[lang]["pages"]
        if len(ids) != 4:
            raise ValueError(f"figma.json {lang} needs 4 page ids, got {len(ids)}")
        writer = PdfWriter()
        for pdf in render(ids, "pdf", token):
            writer.append(io.BytesIO(pdf))
        pdf_path = folder / f"{base}-{lang}.pdf"
        with open(pdf_path, "wb") as f:
            writer.write(f)
        png_path = folder / f"{base}-cover-{lang}.png"
        png_path.write_bytes(render(ids[:1], "png", token, scale=2)[0])
        out += [pdf_path, png_path]
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: export_figma.py YYYY-MM-DD")
    token = os.environ.get("FIGMA_TOKEN")
    if not token:
        sys.exit("FIGMA_TOKEN is not set")
    for p in export(sys.argv[1], token):
        print(p.relative_to(ROOT))
