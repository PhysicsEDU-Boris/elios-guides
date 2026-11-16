import json
from datetime import date

import pytest

import validate
import weak_questions as wq


def en(formula="heat-energy", n=60):
    d = {"_formula": formula, "physics.equation": "Q = m × c × ΔT", "physics.equation_name": "Heat energy", "_theme": "heat",
         "_answers": {"1": "b", "2": "a", "3": "c"},
         "_quiz_pool": [{"question": "Pool question?", "options": ["w", "x", "y", "z"], "answer": 2, "explanation": "."}]}
    for i in (1, 2, 3):
        d[f"quiz.{i}.question"] = f"Question {i}?"
        for letter in "abcd":
            d[f"quiz.{i}.{letter}"] = f"opt {i}{letter}"
    return d


def row(day, qid, attempts, wrong, top_wrong="a"):
    return {"guide_date": day, "question_id": qid, "attempts": attempts, "wrong": wrong, "wrong_rate": round(wrong / attempts, 3), "top_wrong": top_wrong}


def test_remedial_day_is_every_second_day():
    days = [date(2026, 11, d) for d in range(10, 16)]
    assert all(wq.is_remedial_day(a) != wq.is_remedial_day(b) for a, b in zip(days, days[1:]))


def test_question_lookup_for_printed_and_pool_questions():
    assert wq.question_of(en(), "p2") == ("Question 2?", {"a": "opt 2a", "b": "opt 2b", "c": "opt 2c", "d": "opt 2d"}, "a")
    assert wq.question_of(en(), "pool-0")[2] == "c" and wq.question_of(en(), "pool-9") is None and wq.question_of(en(), "p7") is None


def test_rank_groups_by_concept_and_ignores_thin_data():
    docs = {"2026-11-08": en(), "2026-11-09": en("speed")}
    docs["2026-11-09"]["physics.equation"] = "v = s ÷ t"
    stats = [row("2026-11-08", "p1", 40, 30), row("2026-11-08", "p2", 40, 10), row("2026-11-09", "p1", 40, 38), row("2026-11-09", "p3", 10, 10)]
    ranked = wq.rank(stats, docs)
    assert [g["concept"]["key"] for g in ranked] == ["speed"] or [g["concept"]["key"] for g in ranked] == ["heat-energy"]
    assert [g["attempts"] for g in ranked] == [80] and ranked[0]["concept"]["key"] == "heat-energy"  # speed has only 40 usable answers
    assert ranked[0]["wrong_rate"] == 0.5 and ranked[0]["questions"][0]["question_id"] == "p1"
    assert ranked[0]["questions"][0]["most_common_wrong"] == "A: opt 1a" and ranked[0]["questions"][0]["correct"] == "B: opt 1b"


def test_recently_covered_concept_is_skipped():
    ranked = [{"concept": {"key": "heat-energy"}}, {"concept": {"key": "speed"}}]
    guides = [{"date": "2026-11-12", "remedial": {"concept": "heat-energy", "questions": ["2026-11-08#p1"]}}]
    assert wq.pick(ranked, guides, date(2026, 11, 16))["concept"]["key"] == "speed"
    assert wq.pick(ranked, guides, date(2026, 11, 30))["concept"]["key"] == "heat-energy"  # cooldown over
    assert wq.pick([], guides, date(2026, 11, 16)) is None


def test_main_writes_a_brief_only_when_everything_is_in_place(tmp_path, monkeypatch, capsys):
    out, manifest = tmp_path / "brief.json", tmp_path / "m.json"
    manifest.write_text(json.dumps({"guides": [{"date": "2026-11-08", "content": {"en": "issues/2026-11-08/en.json"}}]}))
    args = ["--date", "2026-11-16", "--manifest", str(manifest), "--out", str(out)]
    assert wq.is_remedial_day(date(2026, 11, 16)) or pytest.skip("parity")
    out.write_text("stale")
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    assert wq.main(args) == 0 and not out.exists()  # no secrets: no brief, stale file removed

    class Reply:
        def __init__(self, data):
            self.data = data

        def raise_for_status(self):
            pass

        def json(self):
            return self.data

    monkeypatch.setenv("SUPABASE_URL", "https://x.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_KEY", "service-key")
    monkeypatch.setattr(wq.requests, "post", lambda url, **kw: Reply([row("2026-11-08", "p1", 80, 60)]))
    monkeypatch.setattr(wq.requests, "get", lambda url, **kw: Reply(en()))
    assert wq.main(args) == 0
    brief = json.loads(out.read_text())
    assert brief["concept"]["key"] == "heat-energy" and brief["questions"][0]["question_id"] == "p1" and brief["wrong_rate"] == 0.75
    assert "service-key" not in out.read_text()


def docs(r=None, other=None):
    en_, id_ = {"_formula": "heat-energy"}, {"_formula": "heat-energy"}
    if r is not None:
        en_["_remedial"] = r
    if other is not None:
        id_["_remedial"] = other
    return {"en": en_, "id": id_}


def test_remedial_shape_rules():
    ok = {"concept": "heat-energy", "questions": ["2026-11-08#p1", "2026-11-09#pool-1"]}
    assert validate.check_remedial(docs(ok, ok)) == [] and validate.check_remedial(docs()) == []
    assert "identical" in validate.check_remedial(docs(ok, None))[0]
    for bad in ({"concept": "x", "questions": []}, {"concept": "", "questions": ["2026-11-08#p1"]}, {"concept": "x", "questions": ["p1"]},
                {"concept": "x", "questions": ["2026-11-08#p1"] * 4}, "text"):
        assert validate.check_remedial(docs(bad, bad)), bad


def test_remedial_guide_may_repeat_its_formula_but_must_match_the_concept():
    ok = {"concept": "heat-energy", "questions": ["2026-11-08#p1"]}
    recent = [{"formula": "heat-energy"}]
    d = docs(ok, ok)
    d["en"].update({"physics.equation": "Q = m × c × ΔT"})
    errs = validate.check_formula(d, recent)
    assert not any("last 30" in e for e in errs)
    wrong = {"concept": "speed", "questions": ["2026-11-08#p1"]}
    assert any("must be the _formula" in e for e in validate.check_formula(docs(wrong, wrong), []))
