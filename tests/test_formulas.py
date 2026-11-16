import json
from pathlib import Path

import pytest

import validate

ROOT = Path(__file__).resolve().parent.parent
BANK = json.loads((ROOT / "schema/formulas.json").read_text(encoding="utf-8"))
LIMITS = validate.LIMITS


def test_every_formula_fits_the_template_limits():
    assert len({f["id"] for f in BANK}) == len(BANK)
    for f in BANK:
        assert f["level"] in ("core", "stretch") and f["themes"] and set(f["themes"]) <= set(validate.THEMES), f["id"]
        assert 1 <= len(f["symbols"]) <= 5 and len(f["text"]) <= LIMITS["physics.equation"], f["id"]
        assert len(f["name"]) <= LIMITS["physics.equation_name"], f["id"]
        for symbol, meaning, unit in f["symbols"]:
            assert symbol and len(symbol) <= LIMITS["legend.1.symbol"], (f["id"], symbol)
            assert len(meaning) <= LIMITS["legend.1.meaning"] and len(unit) <= LIMITS["legend.1.unit"], (f["id"], meaning, unit)
        assert len({s[0] for s in f["symbols"]}) == len(f["symbols"]), f["id"]


def test_every_theme_has_core_and_stretch_choices():
    for theme in validate.THEMES:
        levels = [f["level"] for f in BANK if theme in f["themes"]]
        assert levels.count("core") >= 3 and levels.count("stretch") >= 3, theme


def docs(fid="heat-energy"):
    f = next(f for f in BANK if f["id"] == fid)
    d = {"_formula": fid, "physics.equation": f["text"]}
    for i in range(1, 6):
        d[f"legend.{i}.symbol"] = f["symbols"][i - 1][0] if i <= len(f["symbols"]) else ""
    return {"en": dict(d), "id": dict(d)}


def stretch():
    return next(f["id"] for f in BANK if f["level"] == "stretch")


def test_valid_formula_passes():
    assert validate.check_formula(docs(), []) == []


def test_unknown_formula_and_mismatches_fail():
    assert "not an id" in validate.check_formula(dict(en=dict(docs()["en"], _formula="made-up"), id={}), [])[0]
    d = docs()
    d["id"]["physics.equation"] = "Q = m × c"
    d["en"]["legend.2.symbol"] = "x"
    errs = validate.check_formula(d, [])
    assert any("id: physics.equation" in e for e in errs) and any("en: legend symbols" in e for e in errs)


def test_recent_formula_is_rejected():
    assert any("last 30" in e for e in validate.check_formula(docs(), [{"formula": "heat-energy"}]))
    assert validate.check_formula(docs(), [{"formula": "speed"}]) == []


def test_two_stretch_formulas_in_a_row_are_rejected():
    fid = stretch()
    other = next(f["id"] for f in BANK if f["level"] == "stretch" and f["id"] != fid)
    assert any("stretch" in e for e in validate.check_formula(docs(fid), [{"formula": other}]))
    assert validate.check_formula(docs(fid), [{"formula": "speed"}]) == []
