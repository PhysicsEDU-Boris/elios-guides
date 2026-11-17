import io
import json

from PIL import Image

import fetch_images
import find_images


def page(index, url, license_, width=2400, mime="image/jpeg", artist="<a href='x'>Ana</a>"):
    return {"index": index, "imageinfo": [{"url": url, "width": width, "height": width * 2 // 3, "mime": mime, "extmetadata": {
        "LicenseShortName": {"value": license_}, "Artist": {"value": artist}}}]}


class Reply:
    def __init__(self, pages):
        self.pages = pages

    def json(self):
        return {"query": {"pages": {str(i): p for i, p in enumerate(self.pages)}}}


def test_only_big_jpeg_photos_with_free_licences_are_candidates(monkeypatch):
    pages = [page(1, "https://upload.wikimedia.org/a.jpg", "CC BY-SA 4.0"),
             page(2, "https://upload.wikimedia.org/nc.jpg", "CC BY-NC 4.0"),
             page(3, "https://upload.wikimedia.org/small.jpg", "CC0", width=900),
             page(4, "https://upload.wikimedia.org/map.png", "CC0", mime="image/png"),
             page(5, "https://upload.wikimedia.org/pd.jpg", "Public domain")]
    monkeypatch.setattr(find_images.requests, "get", lambda *a, **kw: Reply(pages))
    found = find_images.candidates({"cover.place": "Utah, USA", "_keywords": ["river"]})
    assert [c["source_url"].rsplit("/", 1)[1] for c in found] == ["a.jpg", "pd.jpg"]
    assert found[0] == {"file": "cover.jpg", "source_url": "https://upload.wikimedia.org/a.jpg",
                        "license": "CC BY-SA 4.0", "credit": "Ana / Wikimedia Commons"}


def test_no_place_or_keywords_means_no_search(monkeypatch):
    monkeypatch.setattr(find_images.requests, "get", lambda *a, **kw: 1 / 0)
    assert find_images.candidates({}) == []


def test_failed_cover_falls_back_to_a_commons_archive_photo(tmp_path, monkeypatch):
    for lang in ("en", "id"):
        (tmp_path / f"{lang}.json").write_text(json.dumps({"cover.place": "Utah, USA", "cover.image_caption": "old", "_images": {"cover.image": None}}))
    img = {"file": "cover.jpg", "source_url": "https://upload.wikimedia.org/a.jpg", "license": "CC0", "credit": "Ana / Wikimedia Commons"}
    monkeypatch.setattr(find_images, "candidates", lambda en: [img])
    monkeypatch.setattr(fetch_images, "fetch", lambda url: b"bytes")
    monkeypatch.setattr(fetch_images, "process", lambda data, folder, key, name: (folder / name).write_bytes(b"x") or {"px": 2400})
    fetch_images.commons_cover(tmp_path)
    en, id_ = (json.loads((tmp_path / f"{l}.json").read_text()) for l in ("en", "id"))
    assert en["_images"]["cover.image"] == img and en["cover.image_caption"] == "Archive photo · Utah, USA"
    assert id_["cover.image_caption"] == "Foto arsip · Utah, USA"


def test_no_commons_photo_keeps_the_cover_null(tmp_path, monkeypatch):
    (tmp_path / "en.json").write_text(json.dumps({"_images": {"cover.image": None}}))
    monkeypatch.setattr(find_images, "candidates", lambda en: (_ for _ in ()).throw(OSError("offline")))
    fetch_images.commons_cover(tmp_path)  # must not raise
    assert json.loads((tmp_path / "en.json").read_text())["_images"]["cover.image"] is None


def test_narrower_queries_are_tried_when_the_long_one_finds_nothing(monkeypatch):
    asked = []

    def get(url, params, **kw):
        asked.append(params["gsrsearch"])
        pages = [page(1, "https://upload.wikimedia.org/a.jpg", "CC0")] if "storm" in params["gsrsearch"] else []
        return Reply(pages)
    monkeypatch.setattr(find_images.requests, "get", get)
    found = find_images.candidates({"cover.place": "Jakarta, Indonesia", "_keywords": ["angin", "storm"], "_theme": "storm"})
    assert [c["source_url"].rsplit("/", 1)[1] for c in found] == ["a.jpg"]
    assert asked[0].startswith("storm angin")
