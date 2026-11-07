"""Download the licensed photos listed in issues/<date>/en.json → JPEG, max 1600 px.

Usage: python scripts/fetch_images.py issues/YYYY-MM-DD
"""
import io
import json
import sys
from pathlib import Path

import requests
from PIL import Image

from validate import domain_ok

MAX_BYTES = 8 * 1024 * 1024
UA = "elios-guides-bot/1.0 (+https://github.com/PhysicsEDU-Boris/elios-guides)"


def fetch(url):
    if not domain_ok(url):
        raise ValueError(f"domain not allowed: {url}")
    with requests.get(url, stream=True, timeout=30, headers={"User-Agent": UA}) as r:
        r.raise_for_status()
        if not domain_ok(r.url):  # after redirects
            raise ValueError(f"redirected to a domain that is not allowed: {r.url}")
        ctype = r.headers.get("Content-Type", "")
        if not ctype.startswith("image/"):
            raise ValueError(f"not an image ({ctype or 'no content type'}): {url}")
        data = b""
        for chunk in r.iter_content(65536):
            data += chunk
            if len(data) > MAX_BYTES:
                raise ValueError(f"bigger than 8 MB: {url}")
    return data


def to_jpeg(data, dest):
    im = Image.open(io.BytesIO(data))
    im = im.convert("RGB")
    im.thumbnail((1600, 1600))
    im.save(dest, "JPEG", quality=85, optimize=True)


def main(folder):
    folder = Path(folder)
    images = json.loads((folder / "en.json").read_text(encoding="utf-8")).get("_images") or {}
    failed = 0
    for key, img in images.items():
        if not img:
            continue
        name = Path(img.get("file") or "").name  # no paths outside the issue folder
        try:
            if not name:
                raise ValueError("no file name")
            to_jpeg(fetch(img.get("source_url")), folder / name)
            print(f"{key}: saved {name}")
        except Exception as e:  # keep going; validate.py reports the missing file
            failed += 1
            print(f"{key}: FAILED {e}")
    return 1 if failed else 0


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: fetch_images.py issues/YYYY-MM-DD")
    sys.exit(main(sys.argv[1]))
