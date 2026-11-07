import json
import subprocess
import sys

import pytest

from conftest import ROOT


def has(errs, text):
    assert any(text in e for e in errs), f"expected {text!r} in {errs}"


def test_example_passes(issue):
    assert issue.errors() == []


def test_cli_exit_codes(issue):
    issue.write()
    ok = subprocess.run([sys.executable, str(ROOT / "scripts/validate.py"), str(issue.folder), "--manifest", str(issue.manifest)], capture_output=True, text=True)
    assert ok.returncode == 0, ok.stdout
    issue.en["cover.title"] = "x" * 99
    issue.write()
    bad = subprocess.run([sys.executable, str(ROOT / "scripts/validate.py"), str(issue.folder), "--manifest", str(issue.manifest)], capture_output=True, text=True)
    assert bad.returncode == 1 and "cover.title" in bad.stdout


def test_missing_key(issue):
    del issue.en["story.lead"]
    has(issue.errors(), "en: missing key story.lead")


def test_empty_required(issue):
    issue.en["story.lead"] = ""
    has(issue.errors(), "story.lead is empty")


def test_optional_may_be_empty(issue):
    issue.en["source.4"] = issue.id["source.4"] = ""
    assert issue.errors() == []


def test_over_limit(issue):
    issue.id["cover.title"] = "x" * 35
    has(issue.errors(), "id: cover.title is 35 chars, limit 34")


def test_braces(issue):
    issue.en["story.title"] = "Hot {city}"
    has(issue.errors(), "story.title contains")


def test_braces_in_metadata(issue):
    issue.en["_quiz_pool"][0]["question"] = "{question}"
    has(issue.errors(), "_quiz_pool contains")


def test_key_sets_differ(issue):
    issue.id["extra.slot"] = "x"
    has(issue.errors(), "keys in id.json but not en.json: ['extra.slot']")
    del issue.id["extra.slot"]
    del issue.id["_lab_rubric"]
    has(issue.errors(), "keys in en.json but not id.json: ['_lab_rubric']")


def test_id_labels_allowed(issue):
    assert "label.quiz" in issue.id and issue.errors() == []


def test_answers_differ(issue):
    issue.id["_answers"] = {"1": "b", "2": "a", "3": "d"}
    issue.id["quiz.answer_key"] = "Kunci: 1B · 2A · 3D"
    has(issue.errors(), "_answers differ")


def test_quiz_pool_count(issue):
    issue.id["_quiz_pool"] = issue.id["_quiz_pool"][:9]
    has(issue.errors(), "_quiz_pool has a different number")


def test_answer_key_mismatch(issue):
    issue.en["quiz.answer_key"] = "Answer key: 1B · 2A · 3D"
    has(issue.errors(), "en: quiz.answer_key")


def test_all_same_letter(issue):
    for d, prefix in ((issue.en, "Answer key"), (issue.id, "Kunci")):
        d["_answers"] = {"1": "a", "2": "a", "3": "a"}
        d["quiz.answer_key"] = f"{prefix}: 1A · 2A · 3A"
    has(issue.errors(), "all 3 correct answers are the same letter")


def test_bad_citation(issue):
    issue.en["story.lead"] += " [7]"
    has(issue.errors(), "en: story.lead cites [7]")


def test_too_few_sources(issue):
    issue.en["_sources"] = issue.en["_sources"][:2]
    has(issue.errors(), "en: only 2 sources")


def test_no_primary(issue):
    for s in issue.id["_sources"]:
        s["primary"] = False
    has(issue.errors(), "id: no source has primary: true")


def test_image_needs_license(issue):
    issue.en["_images"]["cover.image"]["license"] = ""
    has(issue.errors(), "image cover.image needs license and credit")


def test_image_needs_credit(issue):
    del issue.en["_images"]["cover.image"]["credit"]
    has(issue.errors(), "image cover.image needs license and credit")


@pytest.mark.parametrize("url", ["https://example.com/a.jpg", "https://nasa.gov.evil.com/a.jpg", "http://www.nasa.gov/a.jpg"])
def test_image_domain(issue, url):
    issue.en["_images"]["cover.image"]["source_url"] = url
    has(issue.errors(), "is not https on")


def test_image_subdomain_ok(issue):
    issue.en["_images"]["cover.image"]["source_url"] = issue.id["_images"]["cover.image"]["source_url"] = "https://upload.wikimedia.org/x.jpg"
    assert issue.errors() == []


def test_image_not_downloaded(issue):
    (issue.folder / "cover.jpg").unlink()
    has(issue.errors(), "was not downloaded")


def test_calc_missing(issue):
    issue.write()
    (issue.folder / "calc.out.json").unlink()
    import validate
    has(validate.check(issue.folder, issue.manifest), "calc.out.json is missing")


def test_graph_raw_mismatch(issue):
    issue.en["_graph.2.raw"] = 30
    has(issue.errors(), "en: _graph.2.raw = 30")


def test_table_mismatch(issue):
    issue.en["table.r2c3"] = "25 °C"
    has(issue.errors(), "en: table.r2c3")


def test_example_result_mismatch(issue):
    issue.id["example.result"] = "Q = 25.000 J"
    has(issue.errors(), "id: example.result")


def test_graph_value_mismatch(issue):
    issue.en["graph.3.value"] = "26 °C"
    has(issue.errors(), "en: graph.3.value")


def test_id_decimal_comma(issue):
    assert issue.id["table.r2c3"] == "23,9 °C" and issue.id["table.r1c2"] == "4.200"
    assert issue.errors() == []


def test_id_with_dot_decimal_fails(issue):
    issue.id["table.r2c3"] = "23.9 °C"  # in id, '.' is a thousands separator
    has(issue.errors(), "id: table.r2c3")


def test_scaled_number():
    import validate
    assert any(5.78e7 in c for c in validate.parse_numbers("57,8 jt", "id"))
    assert any(5.78e7 in c for c in validate.parse_numbers("57.8 million", "en"))


def test_fact_check_fail(issue):
    issue.check.append({"item": "stat.2", "claim": "880 J", "source": 2, "pass": False, "note": "not found"})
    has(issue.errors(), "fact-check failed: stat.2")


def test_fact_check_missing(issue):
    issue.write()
    (issue.folder / "check.json").unlink()
    import validate
    has(validate.check(issue.folder, issue.manifest), "check.json is missing")


def test_duplicate_date(issue):
    issue.guides = [{"date": "2026-11-09", "slug": "other", "topic": {"en": "Other"}}]
    has(issue.errors(), "2026-11-09 is already in manifest.json")


def test_repeated_slug(issue):
    issue.guides = [{"date": "2026-11-06", "slug": "example-hot-city-surfaces", "topic": {"en": "Other"}}]
    has(issue.errors(), "slug 'example-hot-city-surfaces' was used")


def test_repeated_topic(issue):
    issue.guides = [{"date": "2026-11-06", "slug": "other", "topic": {"en": "heat and temperature"}}]
    has(issue.errors(), "topic 'heat and temperature' was used")


def test_old_topic_ok(issue):
    old = [{"date": f"2026-10-{d:02d}", "slug": f"s{d}", "topic": {"en": f"t{d}"}} for d in range(30, 15, -1)]
    old[-1]["topic"]["en"] = "Heat and temperature"  # 15th newest: allowed again
    issue.guides = old
    assert issue.errors() == []


def test_image_file_must_be_plain_name(issue):
    issue.en["_images"]["cover.image"]["file"] = "../cover.jpg"
    has(issue.errors(), "was not downloaded")
