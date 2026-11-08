import json

import pytest

import check_sources

URL = "https://x.nasa.gov/images/1/a"


class Resp:
    def __init__(self, status, url, history=()):
        self.status_code, self.url, self.history = status, url, list(history)


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
    (tmp_path / "en.json").write_text(json.dumps({"_sources": [{"n": 1, "url": "https://a.gov/x/y"}, {"n": 2, "url": "https://b.gov/x/y"}]}))
    monkeypatch.setattr(check_sources, "check", lambda u: "returns HTTP 404" if "b.gov" in u else None)
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
