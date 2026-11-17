import json

import pytest

import research_fallback as rf
from conftest import ROOT, example_en


def fake_chat(replies):
    calls = []

    def chat(base, key, model, system, user):
        calls.append(user)
        return replies[len(calls) - 1]
    chat.calls = calls
    return chat


def test_writes_all_four_files(tmp_path, monkeypatch):
    en = example_en()
    monkeypatch.setattr(rf, "chat", fake_chat([f"Here:\n```json\n{json.dumps(en)}\n```", json.dumps(en),
                                               "```python\nprint('{}')\n```"]))
    folder = tmp_path / "issues" / "2026-11-20"
    rf.run(folder, "https://x", "k", "m", root=ROOT)
    assert {p.name for p in folder.iterdir()} == {"en.json", "id.json", "calc.py", "sources.md"}
    assert json.loads((folder / "en.json").read_text())["_slug"] == en["_slug"]
    assert en["_sources"][0]["url"] in (folder / "sources.md").read_text()


def test_repair_sends_problems_and_current_file(tmp_path, monkeypatch):
    en = example_en()
    folder = tmp_path / "issues" / "2026-11-20"
    folder.mkdir(parents=True)
    (folder / "en.json").write_text('{"_slug": "old", "_sources": [{"n": 1}]}')
    chat = fake_chat([json.dumps(en), json.dumps(en), "print(1)"])
    monkeypatch.setattr(rf, "chat", chat)
    rf.run(folder, "https://x", "k", "m", problems="- source 2 is off-topic", root=ROOT)
    assert "source 2 is off-topic" in chat.calls[0] and '"_slug": "old"' in chat.calls[0]


def test_bad_reply_leaves_no_files(tmp_path, monkeypatch):
    monkeypatch.setattr(rf, "chat", fake_chat(["no json here"]))
    folder = tmp_path / "issues" / "2026-11-20"
    with pytest.raises(ValueError):
        rf.run(folder, "https://x", "k", "m", root=ROOT)
    assert not list(folder.iterdir())
