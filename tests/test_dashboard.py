import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
PAGES = "https://physicsedu-boris.github.io/elios-guides/"
EN = {"_formula": "heat-energy", "physics.equation": "Q = m × c × ΔT", "physics.equation_name": "Heat energy",
      "_answers": {"1": "b", "2": "a", "3": "c"}, "_quiz_pool": []}
for i in (1, 2, 3):
    EN[f"quiz.{i}.question"] = f"Question {i} <img src=x onerror=window.pwned=1>?"
    for letter in "abcd":
        EN[f"quiz.{i}.{letter}"] = f"option {i}{letter}"
ROWS = [
    {"guide_date": "2026-11-08", "question_id": "q1", "attempts": 40, "wrong": 30, "wrong_rate": 0.75,
     "chosen_a": 20, "chosen_b": 10, "chosen_c": 6, "chosen_d": 4, "top_wrong": "a"},
    {"guide_date": "2026-11-08", "question_id": "q2", "attempts": 30, "wrong": 6, "wrong_rate": 0.2,
     "chosen_a": 24, "chosen_b": 3, "chosen_c": 2, "chosen_d": 1, "top_wrong": "b"},
]


@pytest.fixture
def page(tmp_path):
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.launch()
    except Exception as error:
        pytest.skip(f"Chromium unavailable: {error}")
    page = browser.new_page()
    page.route("**/supabase.min.js", lambda route: route.fulfill(body="", content_type="text/javascript"))
    page.route(PAGES + "manifest.json", lambda r: r.fulfill(json={"guides": [{"date": "2026-11-08", "content": {"en": "issues/2026-11-08/en.json"}}]}))
    page.route(PAGES + "issues/2026-11-08/en.json", lambda r: r.fulfill(json=EN))
    yield page
    browser.close()
    p.stop()


def stub(page, session, rpc_result):
    page.add_init_script(f"""window.supabase = {{ createClient: () => ({{
        auth: {{ getSession: async () => ({{ data: {{ session: {json.dumps(session)} }} }}), signOut: async () => {{}},
                 signInWithOtp: async () => ({{ error: null }}) }},
        rpc: async () => ({json.dumps(rpc_result)}) }}) }};""")


def test_logged_in_dashboard_shows_concepts_and_questions_without_parsing_html(page):
    stub(page, {"user": {"email": "me@example.com"}}, {"data": ROWS, "error": None})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#questions .card")
    text = page.inner_text("#app")
    assert "Heat energy" in text and "70 answers on 2 question(s)" in text and "ready for a remedial guide" in text
    assert "75%" in text and "A: option 1a" in text
    assert page.locator("#questions img").count() == 0 and page.evaluate("window.pwned") is None  # guide text is never HTML
    assert page.locator(".opt.no.top").count() == 2 and page.locator(".opt.ok").count() == 2


def test_logged_out_visitor_only_sees_the_login_form(page):
    stub(page, None, {"data": [], "error": None})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#login:not([hidden])")
    assert page.locator("#app").is_hidden() and "Heat energy" not in page.inner_text("body")


def test_email_outside_the_allow_list_gets_a_clear_message(page):
    stub(page, {"user": {}}, {"data": None, "error": {"code": "42501", "message": "not allowed"}})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_function("document.getElementById('msg').textContent.includes('allow-list')")
