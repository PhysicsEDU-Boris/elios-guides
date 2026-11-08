"""Download the licensed photos listed in issues/<date>/en.json and keep only sharp, full-size ones.

Usage: python scripts/fetch_images.py issues/YYYY-MM-DD [--drop-failed]
Each slot file (cover.jpg, story.jpg) is the original, scaled down to at most 2000 px (never up).
The cover photo is also saved as photo.jpg + photo-800.jpg for the app.
--drop-failed (last attempt): a slot whose photo fails is set to null in en.json and id.json, so the
issue goes out with the topic illustration instead of a blurry photo.
"""
import io
import json
import re
import sys
from pathlib import Path

import requests
from PIL import Image, ImageCms, ImageFilter, ImageStat

from validate import MIN_LONG_SIDE, PHOTO_MAX, THUMB, domain_ok

MAX_BYTES = 30 * 1024 * 1024  # originals are big; 8 MB pushed the writer to pick thumbnails
UA = "elios-guides-bot/1.0 (+https://github.com/PhysicsEDU-Boris/elios-guides)"
# Calibrated on tests/fixtures/sharpness (sharp 144-2945, blurry 13-88; see test_fetch_images.py).
MIN_SHARPNESS = 120
MIN_JPEG_QUALITY = 70
# IJG standard luminance table (quality 50); the scale of the actual table gives the quality.
STD_LUMA = [16, 11, 10, 16, 24, 40, 51, 61, 12, 12, 14, 19, 26, 58, 60, 55, 14, 13, 16, 24, 40, 57, 69, 56,
            14, 17, 22, 29, 51, 87, 80, 62, 18, 22, 37, 56, 68, 109, 103, 77, 24, 35, 55, 64, 81, 104, 113, 92,
            49, 64, 78, 87, 103, 121, 120, 101, 72, 92, 95, 98, 112, 100, 103, 99]


def original_url(url):
    """Wikimedia /thumb/<a>/<ab>/<File>/<N>px-<File> -> the original upload of <File>."""
    m = re.match(r"(https://upload\.wikimedia\.org/wikipedia/[^/]+)/thumb/(\w/\w\w/[^/]+)/[^/]+$", url or "")
    return f"{m.group(1)}/{m.group(2)}" if m else url


def fetch(url):
    if not domain_ok(url):
        raise ValueError(f"domain not allowed: {url}")
    with requests.get(url, stream=True, timeout=60, headers={"User-Agent": UA}) as r:
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
                raise ValueError(f"bigger than {MAX_BYTES >> 20} MB: {url}")
    return data


def sharpness(im):
    """Variance of the Laplacian on a grey copy, long side 1024 px (never enlarged)."""
    grey = im.convert("L")
    grey.thumbnail((1024, 1024))
    lap = grey.filter(ImageFilter.Kernel((3, 3), [0, 1, 0, 1, -4, 1, 0, 1, 0], scale=1, offset=128))
    return ImageStat.Stat(lap).var[0]


def jpeg_quality(im):
    """Estimated IJG quality of a JPEG from its luminance table; None for PNG and other formats."""
    tables = getattr(im, "quantization", None)
    if im.format != "JPEG" or not tables:
        return None
    scale = sum(tables[min(tables)]) * 100 / sum(STD_LUMA)
    return round(5000 / scale) if scale > 100 else round((200 - scale) / 2)


def srgb(im):
    icc = im.info.get("icc_profile")
    if icc:
        try:
            im = ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"), outputMode="RGB")
        except (ImageCms.PyCMSError, OSError):
            pass  # unreadable profile: treat the pixels as sRGB
    return im.convert("RGB")


def check(im, min_side):
    """Returns (problems, numbers) for one downloaded image."""
    nums = {"px": max(im.size), "laplacian": round(sharpness(im), 1), "jpeg_q": jpeg_quality(im)}
    problems = []
    if nums["px"] < min_side:
        problems.append(f"long side {nums['px']} px < {min_side} px")
    if nums["laplacian"] < MIN_SHARPNESS:
        problems.append(f"soft: Laplacian variance {nums['laplacian']} < {MIN_SHARPNESS}")
    if nums["jpeg_q"] is not None and nums["jpeg_q"] < MIN_JPEG_QUALITY:
        problems.append(f"JPEG quality about {nums['jpeg_q']} < {MIN_JPEG_QUALITY}")
    return problems, nums


def save(im, dest, side, quality):
    im = im.copy()
    im.thumbnail((side, side), Image.LANCZOS)  # thumbnail never enlarges
    im.save(dest, "JPEG", quality=quality, optimize=True, progressive=True)


def process(data, folder, key, name):
    im = Image.open(io.BytesIO(data))
    problems, nums = check(im, MIN_LONG_SIDE.get(key, 0))
    if problems:
        raise ValueError("; ".join(problems) + f" {nums}")
    im = srgb(im)
    save(im, folder / name, PHOTO_MAX, 85)
    if key == "cover.image":
        save(im, folder / "photo.jpg", PHOTO_MAX, 85)
        save(im, folder / "photo-800.jpg", THUMB, 82)
    return nums


def drop(folder, key):
    for lang in ("en", "id"):
        p = folder / f"{lang}.json"
        d = json.loads(p.read_text(encoding="utf-8"))
        (d.get("_images") or {})[key] = None
        p.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main(folder, drop_failed=False):
    folder = Path(folder)
    images = json.loads((folder / "en.json").read_text(encoding="utf-8")).get("_images") or {}
    for stale in ("photo.jpg", "photo-800.jpg"):
        (folder / stale).unlink(missing_ok=True)
    failed = 0
    for key, img in images.items():
        if not img:
            continue
        name = Path(img.get("file") or "").name  # no paths outside the issue folder
        try:
            if not name:
                raise ValueError("no file name")
            url = original_url(img.get("source_url"))
            nums = process(fetch(url), folder, key, name)
            print(f"{key}: saved {name} {nums}")
        except Exception as e:  # keep going; validate.py reports the missing file
            failed += 1
            if name:
                (folder / name).unlink(missing_ok=True)
            print(f"{key}: REJECTED {e}")
            if drop_failed:
                drop(folder, key)
                print(f"{key}: no usable photo, set to null (photo = null; the app shows the topic illustration)")
    return 1 if failed and not drop_failed else 0


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if a != "--drop-failed"]
    if len(args) != 1:
        sys.exit("usage: fetch_images.py issues/YYYY-MM-DD [--drop-failed]")
    sys.exit(main(args[0], "--drop-failed" in sys.argv))
