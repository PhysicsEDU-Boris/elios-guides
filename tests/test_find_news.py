from datetime import date
from types import SimpleNamespace

import find_news

# NASA's real feed misses a space between two xmlns attributes; it must still parse.
RSS = b"""<?xml version="1.0"?><rss xmlns:a="x"xmlns:b="y"><channel>
<item><title>Banjir rob rendam pesisir Jakarta</title><link>https://n.id/banjir</link>
 <pubDate>Thu, 19 Nov 2026 08:00:00 +0700</pubDate><description><![CDATA[<p>Air laut naik</p>]]></description></item>
<item><title>Badak Jawa dipindahkan</title><link>https://n.id/badak</link><pubDate>Thu, 19 Nov 2026 08:00:00 +0700</pubDate></item>
<item><title>Old flood story</title><link>https://n.id/old</link><pubDate>Mon, 02 Nov 2026 08:00:00 +0700</pubDate></item>
<item><title>Heat wave hits Java</title><link>https://n.id/used</link><pubDate>Wed, 18 Nov 2026 08:00:00 +0700</pubDate></item>
</channel></rss>"""
ATOM = b'<feed><entry><title>Storm winds</title><link href="https://a.gov/storm"/><updated>2026-11-20T01:00:00Z</updated></entry></feed>'
PAGE = "<main>Tide 1.2 m flooded 300 homes in Jakarta on 19 Nov 2026, BMKG said." + " text" * 200 + "</main>"


def test_items_parses_rss_with_bad_xmlns_and_atom():
    rss = list(find_news.items(RSS))
    assert rss[0] == ("Banjir rob rendam pesisir Jakarta", "https://n.id/banjir", date(2026, 11, 19), " Air laut naik ")
    assert list(find_news.items(ATOM)) == [("Storm winds", "https://a.gov/storm", date(2026, 11, 20), "")]


def test_find_keeps_recent_on_topic_unused_articles_with_text(monkeypatch):
    monkeypatch.setattr(find_news, "FEEDS", [("https://feed", "N", False)])

    def fetch(url):
        body = RSS if url == "https://feed" else PAGE.encode()
        return SimpleNamespace(status_code=200, url=url, history=[], content=body, text=body.decode())

    out = find_news.find(date(2026, 11, 20), {"n.id/used"}, fetch)
    assert [c["url"] for c in out["news"]] == ["https://n.id/banjir"]  # not off-topic, old or already used
    c = out["news"][0]
    assert c["date"] == "2026-11-19" and "1.2 m" in c["text"] and out["primary"] == []
