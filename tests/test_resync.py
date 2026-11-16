import json

import resync


def setup(tmp_path, exported=True):
    new, old = tmp_path / "new", tmp_path / "old"
    for folder in (new, old):
        folder.mkdir()
        for lang in ("en", "id"):
            (folder / f"{lang}.json").write_text(json.dumps({"cover.title": "Hot city", "_quiz_pool": [1, 2, 3, 4]}))
    if exported:
        (new / "guide-en.pdf").write_bytes(b"%PDF")
    return new, old


def edit(folder, lang, **kw):
    p = folder / f"{lang}.json"
    p.write_text(json.dumps(dict(json.loads(p.read_text()), **kw)))


def test_printed_text_edit_renders_again(tmp_path):
    new, old = setup(tmp_path)
    edit(new, "id", **{"cover.title": "Kota panas"})
    assert resync.decide(new, old) == "export"


def test_app_only_edit_publishes_without_rendering(tmp_path):
    new, old = setup(tmp_path)
    edit(new, "en", _quiz_explain={"1": {"why": "Because."}})
    assert resync.decide(new, old) == "publish"


def test_no_change(tmp_path):
    new, old = setup(tmp_path)
    assert resync.decide(new, old) == "none"


def test_never_exported_issue_is_rendered_even_for_app_only_edits(tmp_path):
    new, old = setup(tmp_path, exported=False)
    edit(new, "en", _quiz_pool=[1, 2, 3, 4, 5])
    assert resync.decide(new, old) == "export"
