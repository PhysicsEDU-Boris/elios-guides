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
    {"guide_date": "2026-11-08", "question_id": "p1", "attempts": 40, "wrong": 30, "wrong_rate": 0.75,
     "chosen_a": 20, "chosen_b": 10, "chosen_c": 6, "chosen_d": 4, "top_wrong": "a"},
    {"guide_date": "2026-11-08", "question_id": "p2", "attempts": 30, "wrong": 6, "wrong_rate": 0.2,
     "chosen_a": 24, "chosen_b": 3, "chosen_c": 2, "chosen_d": 1, "top_wrong": "b"},
]
SUMMARY = {"students": 4, "stops": {"days": 10, "story": 10, "physics": 9, "quiz": 6, "lab": 3},
           "per_day": [{"date": "2026-11-08", "story": 2, "physics": 2, "quiz": 2, "lab": 1}],
           "streaks": {"none": 0, "d1": 2, "d2_3": 1, "d4_6": 1, "d7": 0},
           "scans": {"total": 83, "phone_quiz": 28, "robot": 8, "contribute": 5, "unknown_device": 42,
                     "bins": {"b3": 29, "organic": 2, "recyclable": 52},
                     "robot_first": {"right": 2, "wrong": 6, "top_wrong": []}}}
SESSION = {"user": {"email": "boris@example.com"}}


@pytest.fixture
def page(tmp_path):
    try:
        from playwright.sync_api import sync_playwright
        p = sync_playwright().start()
        browser = p.chromium.launch()
    except Exception as error:
        pytest.skip(f"Chromium unavailable: {error}")
    page = browser.new_page(viewport={"width": 1440, "height": 900})
    page.route("**/supabase.min.js", lambda route: route.fulfill(body="", content_type="text/javascript"))
    page.route(PAGES + "manifest.json", lambda r: r.fulfill(json={"guides": [{"date": "2026-11-08", "issue": "01", "title": {"en": "Heat story", "id": "Cerita panas"}, "topic": {"en": "Heat"},
        "photo": {"thumb": "issues/2026-11-08/photo-800.jpg"}, "pdf": {"en": "issues/2026-11-08/en.pdf", "id": "issues/2026-11-08/id.pdf"},
        "content": {"en": "issues/2026-11-08/en.json", "id": "issues/2026-11-08/en.json"}}]}))
    page.route(PAGES + "issues/2026-11-08/en.json", lambda r: r.fulfill(json=EN))
    yield page
    browser.close()
    p.stop()


def stub(page, session, rpc_result):
    page.add_init_script(f"""window.supabase = {{ createClient: () => ({{
        auth: {{ getSession: async () => ({{ data: {{ session: {json.dumps(session)} }} }}), signOut: async () => {{}},
                 signInWithOtp: async () => ({{ error: null }}) }},
        rpc: async (name) => name === "magazine_stats" ? {{ data: [{{guide_date: "2026-11-08", started: 3, story: 3, physics: 2, quiz: 1, lab: 0}}], error: null }} : name === "insights_summary" && !{json.dumps(rpc_result)}.error ? {json.dumps({"data": SUMMARY, "error": None})} : ({json.dumps(rpc_result)}) }}) }};""")


def open_dashboard(page, rows=ROWS, tab="quiz"):
    stub(page, SESSION, {"data": rows, "error": None})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#questions .qcard", state="attached")
    page.click(f"#tabs [data-tab={tab}]")


def test_overview_shows_topics_streaks_learning_scans_and_waiting_cards(page):
    open_dashboard(page, tab="overview")
    text = page.inner_text("#app")
    assert "Heat energy" in text and "75% wrong" not in text and "Streaks: how loyal" in text and "Learning activity" in text
    assert page.locator("#kpis .kpi").count() == 6 and "83" in page.inner_text("#kpis")
    assert "scan with robot" in page.inner_text("#scans").lower() and "Recyclable" in page.inner_text("#scans")
    assert "Not collected yet" in page.inner_text("#clovers") and "Not collected yet" in page.inner_text("#videos")
    assert "Not the exact bin question yet" in page.inner_text("#robot")
    assert "Hi, boris" in page.inner_text("#topbar")


def test_quiz_tab_shows_questions_concepts_and_calendar_without_parsing_html(page):
    open_dashboard(page)
    text = page.inner_text("#app")
    assert "70 answers on 2 question(s)" in text and "ready for a remedial guide" in text.lower()
    assert "75%" in text and "A: option 1a" in text and "Buddy tip" in text
    assert page.locator("#questions img[src='x']").count() == 0 and page.evaluate("window.pwned") is None  # guide text is never HTML
    assert page.locator(".opt.no.top").count() == 2 and page.locator(".opt.ok").count() == 2
    assert page.locator("#calendar .day").count() == 3


def test_question_cards_expand_and_collapse_and_filters_work(page):
    open_dashboard(page)
    cards = page.locator("#questions .qcard")
    assert cards.nth(0).get_attribute("data-open") == "true" and cards.nth(1).get_attribute("data-open") == "false"
    cards.nth(1).locator(".header").click()
    assert cards.nth(1).get_attribute("data-open") == "true"
    page.get_by_role("button", name="Tough 1").click()
    assert page.locator("#questions .qcard").count() == 1 and "75%" in page.inner_text("#questions")
    page.get_by_role("button", name="All 2").click()
    assert page.locator("#questions .qcard").count() == 2


def test_theme_button_switches_between_light_and_dark(page):
    open_dashboard(page)
    assert page.get_attribute("html", "data-theme") == "light" and "Dark mode" in page.inner_text("#theme")
    page.click("#theme")
    assert page.get_attribute("html", "data-theme") == "dark" and "Light mode" in page.inner_text("#theme")


def test_without_recorded_choices_it_shows_the_right_answer_instead_of_bars(page):
    rows = [dict(r, chosen_a=0, chosen_b=0, chosen_c=0, chosen_d=0, top_wrong=None) for r in ROWS]
    open_dashboard(page, rows)
    assert "is not recorded yet" in page.inner_text("#questions") and page.locator(".opt").count() == 0
    assert "Right answer B: option 1b" in page.inner_text("#questions")


def test_logged_out_visitor_only_sees_the_login_and_the_magic_link_flow(page):
    stub(page, None, {"data": [], "error": None})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#login:not([hidden])")
    assert page.locator("#app").is_hidden() and page.locator("#topbar").is_hidden() and "Heat energy" not in page.inner_text("body")
    page.fill("#email", "me@school.com")
    page.get_by_role("button", name="Send my magic link").click()
    page.wait_for_selector("#sent:not([hidden])")
    assert "me@school.com" in page.inner_text("#sent") and "Check your inbox" in page.inner_text("#sent")


def test_email_outside_the_allow_list_gets_a_clear_screen(page):
    stub(page, {"user": {}}, {"data": None, "error": {"code": "42501", "message": "not allowed"}})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#denied:not([hidden])")
    assert "not on the list" in page.inner_text("#denied") and page.locator("#app").is_hidden()


def test_no_rows_shows_friendly_empty_texts(page):
    stub(page, SESSION, {"data": [], "error": None})
    page.goto((ROOT / "dashboard" / "index.html").as_uri())
    page.wait_for_selector("#topics h2", state="attached")
    assert "No quiz answers in this period yet" in page.inner_text("#topics")
    page.click("#tabs [data-tab=quiz]")
    assert "No question has enough answers" in page.inner_text("#questions")


def test_magazines_tab_lists_issues_and_shows_content_and_progress(page):
    open_dashboard(page, tab="magazines")
    page.wait_for_selector("#mdetail .mhead")
    assert "Heat story" in page.inner_text("#mlist") and "3 started" in page.inner_text("#mlist")
    assert "#01" in page.inner_text("#mhealth")
    detail = page.inner_text("#mdetail")
    assert "Heat energy" in detail and "Quiz done" in detail and "33%" in detail
    assert page.locator("#mdetail a[href$='en.pdf']").count() == 1 and page.evaluate("window.pwned") is None
