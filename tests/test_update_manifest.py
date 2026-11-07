import json
from datetime import datetime, timezone

import pytest

import update_manifest
from conftest import Issue


def make(issue, date):
    folder = issue.root / "issues" / date
    folder.mkdir(parents=True, exist_ok=True)
    en = dict(issue.en, _example=False, _issue=date[-2:], _slug=f"topic-{date}")
    id_ = dict(issue.id, _example=False, _issue=en["_issue"], _slug=en["_slug"])
    for l, d in (("en", en), ("id", id_)):
        (folder / f"{l}.json").write_text(json.dumps(d), encoding="utf-8")
        base = f"elios-guide-{en['_issue']}-{en['_slug']}"
        (folder / f"{base}-{l}.pdf").write_bytes(b"%PDF")
        (folder / f"{base}-cover-{l}.png").write_bytes(b"png")


@pytest.fixture
def repo(issue):
    issue.write()
    return issue


def test_entry_and_order(repo):
    for date in ("2026-11-05", "2026-11-09", "2026-11-07"):
        make(repo, date)
        update_manifest.update(date, repo.root, now=datetime(2026, 11, 9, 0, 0, tzinfo=timezone.utc))
    m = json.loads(repo.manifest.read_text())
    assert [g["date"] for g in m["guides"]] == ["2026-11-09", "2026-11-07", "2026-11-05"]
    assert m["updated"] == "2026-11-09T07:00:00+07:00"
    g = m["guides"][0]
    assert g["xp"] == 60 and g["title"]["en"] == "Why city streets get so hot"
    assert g["pdf"]["id"] == "issues/2026-11-09/elios-guide-09-topic-2026-11-09-id.pdf"
    assert g["cover"]["en"] == "issues/2026-11-09/elios-guide-09-topic-2026-11-09-cover-en.png"
    assert g["content"] == {"en": "issues/2026-11-09/en.json", "id": "issues/2026-11-09/id.json"}


def test_replace_same_date(repo):
    make(repo, "2026-11-09")
    update_manifest.update("2026-11-09", repo.root)
    update_manifest.update("2026-11-09", repo.root)
    assert len(json.loads(repo.manifest.read_text())["guides"]) == 1


def test_cap_365(repo):
    old = [{"date": f"2025-{m:02d}-{d:02d}"} for m in range(1, 13) for d in range(1, 32)][:400]
    repo.manifest.write_text(json.dumps({"updated": None, "guides": old}))
    make(repo, "2026-11-09")
    update_manifest.update("2026-11-09", repo.root)
    guides = json.loads(repo.manifest.read_text())["guides"]
    assert len(guides) == 365 and guides[0]["date"] == "2026-11-09"
    assert guides[1]["date"] > guides[-1]["date"]


def test_refuses_example(repo):
    make(repo, "2026-11-09")
    p = repo.root / "issues/2026-11-09/en.json"
    p.write_text(json.dumps(dict(json.loads(p.read_text()), _example=True)))
    with pytest.raises(SystemExit):
        update_manifest.update("2026-11-09", repo.root)


def test_requires_exported_files(repo):
    make(repo, "2026-11-09")
    for f in (repo.root / "issues/2026-11-09").glob("*.pdf"):
        f.unlink()
    with pytest.raises(SystemExit, match="missing"):
        update_manifest.update("2026-11-09", repo.root)
