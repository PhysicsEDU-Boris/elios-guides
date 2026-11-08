import json

import resync


def setup(tmp_path, figma=True):
    new, old = tmp_path / "new", tmp_path / "old"
    for folder in (new, old):
        folder.mkdir()
        for lang in ("en", "id"):
            (folder / f"{lang}.json").write_text(json.dumps({"cover.title": "Hot city", "_quiz_pool": [1, 2, 3, 4]}))
    if figma:
        (new / "figma.json").write_text(json.dumps({"en": {}, "id": {}, "content_sha": resync.content_sha(new)}))
    return new, old


def edit(folder, lang, **kw):
    p = folder / f"{lang}.json"
    p.write_text(json.dumps(dict(json.loads(p.read_text()), **kw)))


def test_printed_text_edit_marks_figma_refill(tmp_path):
    new, old = setup(tmp_path)
    edit(new, "id", **{"cover.title": "Kota panas"})
    assert resync.decide(new, old) == "figma"
    r = json.loads((new / "resync.json").read_text())
    assert r["content_sha"] == resync.content_sha(new) and "cover.title" in r["reason"] and r["created"]


def test_app_only_edit_publishes_without_figma(tmp_path):
    new, old = setup(tmp_path)
    edit(new, "en", _quiz_explain={"1": {"why": "Because."}})
    assert resync.decide(new, old) == "publish"
    assert not (new / "resync.json").exists()


def test_no_change(tmp_path):
    new, old = setup(tmp_path)
    assert resync.decide(new, old) == "none"


def test_not_in_figma_yet(tmp_path):
    new, old = setup(tmp_path, figma=False)
    edit(new, "en", **{"cover.title": "Cooler"})
    assert resync.decide(new, old) == "none" and not (new / "resync.json").exists()


def test_claude_task_push_with_matching_figma_sha_is_done(tmp_path):
    new, old = setup(tmp_path)
    edit(new, "en", **{"cover.title": "Shorter"})
    (new / "figma.json").write_text(json.dumps({"content_sha": resync.content_sha(new)}))
    assert resync.decide(new, old) == "none" and not (new / "resync.json").exists()
