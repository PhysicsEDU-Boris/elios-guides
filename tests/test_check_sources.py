import json

import pytest

import check_sources

URL = "https://x.nasa.gov/images/1/a"


class Resp:
    def __init__(self, status, url, history=(), text=""):
        self.status_code, self.url, self.history, self.text = status, url, list(history), text


def fake(real, probe=None):
    return lambda u: probe if u.endswith("-elios-missing-page-check") else real


@pytest.mark.parametrize("real,probe,ok", [
    (Resp(200, URL), None, True),
    (Resp(403, URL), None, True),                                                  # bot blocker
    (Resp(404, URL), None, False),
    (Resp(503, URL), None, False),
    (Resp(200, URL + "/", [1]), Resp(404, URL + "-x"), True),                      # real redirect
    (Resp(200, "https://x.nasa.gov/eo/", [1]), Resp(200, "https://x.nasa.gov/eo/", [1]), False),  # soft 404
])
def test_check(monkeypatch, real, probe, ok):
    monkeypatch.setattr(check_sources, "get", fake(real, probe))
    assert (check_sources.check(URL) is None) == ok


def test_unreachable(monkeypatch):
    def boom(u):
        raise check_sources.requests.ConnectionError("down")
    monkeypatch.setattr(check_sources, "get", boom)
    assert "cannot be reached" in check_sources.check(URL)


def test_main_exit_code(tmp_path, monkeypatch, capsys):
    (tmp_path / "en.json").write_text(json.dumps({"_sources": [{"n": 1, "url": "https://a.gov/x/y"}, {"n": 2, "url": "https://b.gov/x/y"}],
                                                  "story.lead": "See [1] and [2]."}))
    monkeypatch.setattr(check_sources, "get", lambda u: Resp(404 if "b.gov" in u else 200, u))
    assert check_sources.main(tmp_path) == 1
    assert "source 2 https://b.gov/x/y returns HTTP 404" in capsys.readouterr().out


def test_validate_flag_adds_source_errors(issue, monkeypatch, capsys):
    import validate
    issue.write()
    monkeypatch.setattr(check_sources, "errors", lambda folder: ["source 2 https://b.gov/x/y returns HTTP 404"])
    args = [str(issue.folder), "--manifest", str(issue.manifest)]
    assert validate.main(args) == 0
    assert validate.main(args + ["--check-sources"]) == 1
    assert "source 2 https://b.gov/x/y returns HTTP 404" in capsys.readouterr().out


# --- fact check against the opened pages (G4) ---

PAGE = "<html><nav>utah goosenecks river</nav><article><p>The San Juan River goosenecks in Utah loop for 5.5 miles. Photo taken 6 Oct 2026; rocks are 300 million years old.</p></article></html>"
OFF = "<html><article><p>Cyprus has snakes, cats and one river.</p></article></html>"


def test_main_article_is_not_replaced_by_a_related_article_card():
    page = ('<main><h1>Rain outlook</h1><p>Aceh recorded 140 mm and Sumatera Barat 121 mm.</p>'
            '<h2>Potensi Hujan Sepekan ke Depan Lainnya</h2>'
            '<article><p>Unrelated rain total 999 mm.</p></article></main>')
    text = check_sources.page_text(page)
    assert '140 mm' in text and '121 mm' in text
    assert '999' not in text and 'unrelated' not in text


def issue_dir(tmp_path, en, calc_py="v = 11 / 2\nprint(v)\n", calc_out=None):
    base = {"_slug": "utah-goosenecks-river", "cover.place": "Utah, USA", "story.lead": "Loops of 5.5 miles [1].",
            "stat.1.value": "5.5 mi", "_sources": [{"n": 1, "url": "https://a.gov/x/y"}]}
    (tmp_path / "en.json").write_text(json.dumps(dict(base, **en)))
    (tmp_path / "calc.py").write_text(calc_py)
    (tmp_path / "calc.out.json").write_text(json.dumps(calc_out or {"v": 5.5}))
    return tmp_path


def pages(monkeypatch, by_host):
    monkeypatch.setattr(check_sources, "get", lambda u: Resp(200, u, text=next(t for h, t in by_host.items() if h in u)))


def test_sourced_issue_passes(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE})
    assert check_sources.errors(issue_dir(tmp_path, {})) == []


@pytest.mark.parametrize("status", [200, 403, 404])
def test_evidence_preserves_fetch_failures_and_bounds_article_text(tmp_path, monkeypatch, status):
    body = PAGE.replace('</article>', 'x' * 20000 + '</article>')
    monkeypatch.setattr(check_sources, "get", lambda u: Resp(status, u, text=body))
    folder = issue_dir(tmp_path, {})
    output = tmp_path / "evidence.json"
    errors = check_sources.errors(folder, output)
    snapshot = json.loads(output.read_text())
    source = snapshot["sources"][0]
    assert snapshot["errors"] == errors
    assert source["status"] == status and source["url"] == source["final_url"]
    if status == 200:
        assert source["truncated"] is True and len(source["text"]) == 16000
        assert "San Juan".lower() in source["text"]
    else:
        assert source["text"] == "" and source["error"]


def test_stat_not_in_source_fails(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE})
    errs = check_sources.errors(issue_dir(tmp_path, {"stat.2.value": "120 m"}))
    assert any("stat.2.value = '120 m': 120 is not in any source page" in e for e in errs), errs


def test_scaled_source_number_is_not_the_bare_number(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE})  # "300 million years" must not confirm "300 km"
    errs = check_sources.errors(issue_dir(tmp_path, {"stat.2.value": "300 km"}))
    assert any("stat.2.value" in e for e in errs), errs


def test_calc_inputs_need_a_source_but_computed_values_do_not(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE})
    calc = "s = 120\nt = 20\nprint(s / t)\n"
    folder = issue_dir(tmp_path, {"story.body_1": "It moved 120 m in 20 s, so 6 m/s [1]."}, calc, {"s": 120, "t": 20, "v": 6.0})
    errs = check_sources.errors(folder)
    assert any(": 120 is not" in e for e in errs) and any(": 20 is not" in e for e in errs)
    assert not any(": 6 is not" in e for e in errs), errs


def test_cover_and_story_numbers_are_checked_but_boilerplate_is_not(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE})
    folder = issue_dir(tmp_path, {"cover.news_date": "News: 7 Oct 2026", "cover.read_time": "12 min read", "cover.xp_total": "60 XP"})
    errs = check_sources.errors(folder)
    assert errs == ["cover.news_date = 'News: 7 Oct 2026': 7 is not in any source page or computed by calc.py"]


def test_uncited_source_fails(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE, "b.gov": PAGE})
    folder = issue_dir(tmp_path, {"_sources": [{"n": 1, "url": "https://a.gov/x/y"}, {"n": 2, "url": "https://b.gov/x/y"}]})
    assert check_sources.errors(folder) == ["source 2 https://b.gov/x/y is never cited with [2]"]


def test_off_topic_source_fails(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": PAGE, "b.gov": OFF})
    folder = issue_dir(tmp_path, {"_sources": [{"n": 1, "url": "https://a.gov/x/y"}, {"n": 2, "url": "https://b.gov/x/y"}],
                                  "story.body_1": "More [2]."})
    errs = check_sources.errors(folder)
    assert len(errs) == 1 and "source 2 https://b.gov/x/y is off-topic: mentions ['river']" in errs[0], errs


def test_menus_do_not_count_as_topic(tmp_path, monkeypatch):
    nav_only = "<html><nav>utah goosenecks</nav><article>Cyprus cats and one river.</article></html>"
    pages(monkeypatch, {"a.gov": PAGE, "b.gov": nav_only})
    folder = issue_dir(tmp_path, {"_sources": [{"n": 1, "url": "https://a.gov/x/y"}, {"n": 2, "url": "https://b.gov/x/y"}],
                                  "story.body_1": "More [2]."})
    assert any("source 2" in e and "off-topic" in e for e in check_sources.errors(folder))


def test_keywords_can_add_indonesian_terms(tmp_path, monkeypatch):
    pages(monkeypatch, {"a.gov": "<article>Banjir di Jakarta setinggi 5,5 m.</article>"})
    folder = issue_dir(tmp_path, {"_slug": "jakarta-flood", "cover.place": "Jakarta", "_keywords": ["banjir"], "stat.1.value": "5.5 m"})
    assert check_sources.errors(folder) == []


def test_blocked_source_confirms_nothing(tmp_path, monkeypatch):
    monkeypatch.setattr(check_sources, "get", lambda u: Resp(403, u, text=PAGE))
    errs = check_sources.errors(issue_dir(tmp_path, {}, calc_out={"v": 1}))
    assert errs and all("not in any source page" in e for e in errs)
