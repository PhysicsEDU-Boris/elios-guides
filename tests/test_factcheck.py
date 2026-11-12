import json

import pytest

import factcheck

ITEM = {"item": "stat.1", "claim": "rainfall", "source": "1", "pass": False, "note": "unconfirmed"}
KEY = "private-test-key"


@pytest.fixture
def setup(tmp_path, monkeypatch):
    folder = tmp_path / "issue"
    folder.mkdir()
    for name in ("en.json", "id.json", "calc.out.json"):
        (folder / name).write_text("{}")
    (folder / "calc.py").write_text('print("{}")')
    (tmp_path / "GEMINI.md").write_text("## id.json\nRequired Indonesian labels")
    evidence = tmp_path / "evidence.json"
    evidence.write_text(json.dumps({"sources": [{"status": 404, "text": ""}]}))
    monkeypatch.setattr(factcheck.time, "sleep", lambda seconds: None)
    return folder, evidence, tmp_path


def response(items, status=200, finish="STOP"):
    class Response:
        status_code = status

        def json(self):
            return {"candidates": [{"finishReason": finish, "content": {"parts": [{"text": json.dumps(items)}]}}]}
    return Response()


def test_one_structured_request_preserves_failed_claims(setup, monkeypatch):
    folder, evidence, root = setup
    calls = []

    def post(url, headers, json, timeout):
        assert KEY not in url and headers == {"x-goog-api-key": KEY}
        assert "tools" not in json and json["generationConfig"]["responseMimeType"] == "application/json"
        assert '"status": 404' in json["contents"][0]["parts"][0]["text"]
        calls.append(url)
        return response([ITEM])

    monkeypatch.setattr(factcheck.requests, "post", post)
    assert factcheck.factcheck(folder, KEY, "gemini-3.5-flash-lite", evidence, root) == [ITEM]
    assert json.loads((folder / "check.json").read_text()) == [ITEM]
    assert len(calls) == 1


@pytest.mark.parametrize("items", [[], {}, [dict(ITEM, **{"pass": "true"})], [dict(ITEM, claim=None)], [{}]])
def test_invalid_report_never_reuses_previous_approval(setup, monkeypatch, items):
    folder, evidence, root = setup
    (folder / "check.json").write_text(json.dumps([dict(ITEM, **{"pass": True})]))
    monkeypatch.setattr(factcheck.requests, "post", lambda *a, **kw: response(items))
    with pytest.raises(ValueError):
        factcheck.factcheck(folder, KEY, "gemini-3.5-flash-lite", evidence, root)
    assert not (folder / "check.json").exists()


def test_retries_service_error_but_rejects_truncated_report(setup, monkeypatch):
    folder, evidence, root = setup
    replies = iter([response(None, 503), response([ITEM], finish="MAX_TOKENS")])
    monkeypatch.setattr(factcheck.requests, "post", lambda *a, **kw: next(replies))
    with pytest.raises(ValueError, match="complete report"):
        factcheck.factcheck(folder, KEY, "gemini-3.5-flash-lite", evidence, root)
    assert not (folder / "check.json").exists()


def test_http_failure_does_not_print_the_api_key(setup, monkeypatch):
    folder, evidence, root = setup
    monkeypatch.setattr(factcheck.requests, "post", lambda *a, **kw: response(None, 403))
    with pytest.raises(RuntimeError) as error:
        factcheck.factcheck(folder, KEY, "gemini-3.5-flash-lite", evidence, root)
    assert "403" in str(error.value) and KEY not in str(error.value)
