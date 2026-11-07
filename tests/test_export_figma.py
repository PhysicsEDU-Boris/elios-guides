import io
import json

import pytest
from pypdf import PdfReader, PdfWriter

import export_figma

TOKEN = "test-token-not-real"


def pdf_with_width(w):
    wr = PdfWriter()
    wr.add_blank_page(width=w, height=100)
    buf = io.BytesIO()
    wr.write(buf)
    return buf.getvalue()


class Resp:
    def __init__(self, status=200, body=None, content=b""):
        self.status_code, self._body, self.content = status, body, content

    def json(self):
        return self._body


@pytest.fixture
def setup(tmp_path, monkeypatch):
    folder = tmp_path / "issues" / "2026-11-09"
    folder.mkdir(parents=True)
    ids = {"en": ["1:1", "1:2", "1:3", "1:4"], "id": ["2:1", "2:2", "2:3", "2:4"]}
    (folder / "figma.json").write_text(json.dumps({l: {"wrapper": "9:9", "pages": p} for l, p in ids.items()}))
    (folder / "en.json").write_text(json.dumps({"_issue": "02", "_slug": "test-slug"}))
    calls = []
    # width encodes the page: node "1:3" → 103 pt wide
    width = {i: 100 + int(i.split(":")[1]) + (10 if i.startswith("2:") else 0) for p in ids.values() for i in p}
    flaky = {"n": 0}

    def fake_get(url, timeout=None, params=None, headers=None):
        calls.append((url, params, headers))
        if url == export_figma.API:
            assert headers == {"X-Figma-Token": TOKEN}
            if flaky["n"] < 1:
                flaky["n"] += 1
                return Resp(429)
            node_ids = params["ids"].split(",")
            # return the dict in reverse order to prove we merge by figma.json order
            return Resp(body={"err": None, "images": {i: f"https://cdn/{params['format']}/{i}" for i in reversed(node_ids)}})
        fmt, node = url.split("/")[-2:]
        return Resp(content=pdf_with_width(width[node]) if fmt == "pdf" else f"PNG {node}".encode())

    monkeypatch.setattr(export_figma.requests, "get", fake_get)
    monkeypatch.setattr(export_figma.time, "sleep", lambda s: None)
    return tmp_path, folder, calls


def test_merges_in_order(setup):
    root, folder, calls = setup
    export_figma.export("2026-11-09", TOKEN, root)
    for lang, base in (("en", 100), ("id", 110)):
        pdf = PdfReader(folder / f"elios-guide-02-test-slug-{lang}.pdf")
        assert [round(float(p.mediabox.width)) for p in pdf.pages] == [base + 1, base + 2, base + 3, base + 4]
    assert (folder / "elios-guide-02-test-slug-cover-en.png").read_bytes() == b"PNG 1:1"
    assert (folder / "elios-guide-02-test-slug-cover-id.png").read_bytes() == b"PNG 2:1"
    png_calls = [p for u, p, h in calls if p and p["format"] == "png"]
    assert png_calls == [{"ids": "1:1", "format": "png", "scale": 2}, {"ids": "2:1", "format": "png", "scale": 2}]


def test_retries_then_fails(setup, monkeypatch):
    root, folder, calls = setup
    monkeypatch.setattr(export_figma.requests, "get", lambda *a, **k: Resp(503))
    with pytest.raises(RuntimeError) as e:
        export_figma.export("2026-11-09", TOKEN, root)
    assert "503" in str(e.value) and TOKEN not in str(e.value)


def test_figma_error(setup, monkeypatch):
    root, folder, calls = setup
    monkeypatch.setattr(export_figma.requests, "get", lambda *a, **k: Resp(body={"err": "bad ids", "images": {}}))
    with pytest.raises(RuntimeError, match="bad ids"):
        export_figma.export("2026-11-09", TOKEN, root)
