import io
import json
from pathlib import Path

import pytest
from PIL import Image, ImageDraw, ImageFilter

import fetch_images as f

FIXTURES = Path(__file__).parent / "fixtures" / "sharpness"


def detailed(size):
    """A sharp test picture: thin lines and edges everywhere."""
    im = Image.new("RGB", size, "white")
    d = ImageDraw.Draw(im)
    for x in range(0, size[0], 7):
        d.line([(x, 0), (x + size[1] // 3, size[1])], fill=(x % 255, 40, 90), width=1)
    return im


def jpeg(im, quality=92):
    buf = io.BytesIO()
    im.save(buf, "JPEG", quality=quality)
    return buf.getvalue()


@pytest.mark.parametrize("path", sorted(FIXTURES.glob("*.jpg")), ids=lambda p: p.stem)
def test_threshold_separates_calibration_samples(path):
    score = f.sharpness(Image.open(path))
    assert (score >= f.MIN_SHARPNESS) == path.stem.startswith("sharp"), score


def test_calibration_set_is_five_and_five():
    assert len(list(FIXTURES.glob("sharp-*.jpg"))) == 5 and len(list(FIXTURES.glob("blurry-*.jpg"))) == 5


def test_wikimedia_thumb_becomes_original():
    thumb = "https://upload.wikimedia.org/wikipedia/commons/thumb/f/fe/Goose_2020.jpg/1280px-Goose_2020.jpg"
    assert f.original_url(thumb) == "https://upload.wikimedia.org/wikipedia/commons/f/fe/Goose_2020.jpg"
    nasa = "https://assets.science.nasa.gov/a/ISS075-E-188830.jpg"
    assert f.original_url(nasa) == nasa


@pytest.mark.parametrize("q", [50, 69, 85, 95])
def test_jpeg_quality_estimate(q):
    est = f.jpeg_quality(Image.open(io.BytesIO(jpeg(detailed((300, 200)), q))))
    assert abs(est - q) <= 2


def test_saves_full_size_progressive_photo_and_thumb(tmp_path):
    nums = f.process(jpeg(detailed((3000, 2000))), tmp_path, "cover.image", "cover.jpg")
    assert nums["px"] == 3000 and nums["laplacian"] >= f.MIN_SHARPNESS and nums["jpeg_q"] >= 90
    for name, side in (("cover.jpg", 2000), ("photo.jpg", 2000), ("photo-800.jpg", 800)):
        with Image.open(tmp_path / name) as im:
            assert max(im.size) == side and im.info.get("progressive") and im.mode == "RGB"


def test_never_upscales(tmp_path):
    f.process(jpeg(detailed((1700, 1100))), tmp_path, "cover.image", "cover.jpg")
    assert Image.open(tmp_path / "photo.jpg").size == (1700, 1100)


def test_story_photo_is_not_the_app_photo(tmp_path):
    f.process(jpeg(detailed((1300, 900))), tmp_path, "story.image", "story.jpg")
    assert (tmp_path / "story.jpg").is_file() and not (tmp_path / "photo.jpg").exists()


@pytest.mark.parametrize("key,im,quality,why", [
    ("cover.image", detailed((1280, 850)), 92, "long side 1280 px < 1600 px"),
    ("story.image", detailed((1100, 700)), 92, "long side 1100 px < 1200 px"),
    ("cover.image", detailed((2400, 1600)).filter(ImageFilter.GaussianBlur(4)), 92, "soft"),
    ("cover.image", detailed((2400, 1600)), 55, "JPEG quality about 55"),
])
def test_rejects(tmp_path, key, im, quality, why):
    with pytest.raises(ValueError, match=why):
        f.process(jpeg(im, quality), tmp_path, key, "x.jpg")
    assert not list(tmp_path.iterdir())


def test_drop_failed_sets_photo_null_in_both_languages(tmp_path, monkeypatch):
    img = {"file": "cover.jpg", "source_url": "https://images-assets.nasa.gov/a.jpg", "license": "PD", "credit": "NASA"}
    for lang in ("en", "id"):
        (tmp_path / f"{lang}.json").write_text(json.dumps({"_images": {"cover.image": img, "story.image": None}}))
    monkeypatch.setattr(f, "fetch", lambda url: jpeg(detailed((900, 600))))
    assert f.main(tmp_path) == 1  # first attempt: fail so the repair pass can pick another photo
    assert f.main(tmp_path, drop_failed=True) == 0
    for lang in ("en", "id"):
        assert json.loads((tmp_path / f"{lang}.json").read_text())["_images"]["cover.image"] is None
    assert not (tmp_path / "photo.jpg").exists()
