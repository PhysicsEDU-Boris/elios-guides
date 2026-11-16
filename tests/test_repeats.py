import repeats


def issue(title, topic, slug, place, keywords, urls):
    return {"cover.title": title, "story.title": title, "cover.topic": topic, "_slug": slug, "cover.place": place,
            "_keywords": keywords, "_sources": [{"n": i + 1, "url": u} for i, u in enumerate(urls)]}


def entry(date, d):
    return {"date": date, "sources": repeats.issue_sources(d), "terms": repeats.issue_terms(d)}


JAKARTA = issue("Jakarta floods after heavy rain", "Floods", "jakarta-floods-heavy-rain", "Jakarta, Indonesia", ["banjir", "rainfall"],
                ["https://www.bmkg.go.id/press/jakarta-rain/", "https://www.bnpb.go.id/berita/a", "https://news.example.com/x"])


def test_url_normalisation():
    assert repeats.norm_url("HTTPS://www.NASA.gov/a/b/?utm=1#top") == "nasa.gov/a/b"
    assert repeats.norm_url("") == "" and repeats.norm_url("not a url") == ""


def test_same_event_under_a_new_slug_is_caught_by_words():
    again = issue("Floods hit Jakarta again", "Flood", "banjir-jakarta-again", "Jakarta", ["rainfall", "flood"], ["https://other.example/z"])
    errs = repeats.check(again, [entry("2026-11-10", JAKARTA)])
    assert len(errs) == 1 and "2026-11-10" in errs[0] and "jakarta" in errs[0]


def test_different_event_in_the_same_city_passes():
    heat = issue("Why Jakarta streets burn at noon", "Urban heat", "jakarta-urban-heat", "Jakarta, Indonesia", ["panas", "asphalt"],
                 ["https://other.example/heat1", "https://other.example/heat2", "https://other.example/heat3"])
    assert repeats.check(heat, [entry("2026-11-10", JAKARTA)]) == []


def test_main_source_reuse_is_caught_even_with_different_words():
    other = issue("A satellite view of storm clouds", "Storms", "storm-clouds-satellite", "Philippines", ["typhoon"],
                  ["https://bmkg.go.id/press/jakarta-rain", "https://a.example/1", "https://a.example/2"])
    assert "main source" in repeats.check(other, [entry("2026-11-10", JAKARTA)])[0]


def test_two_shared_background_sources_are_caught_but_one_is_not():
    base = issue("Wind power on Java coasts", "Wind", "java-wind-power", "Java", ["turbine"], ["https://a.example/1", "https://b.example/2", "https://c.example/3"])
    one = issue("Solar farms in Bali", "Solar", "bali-solar", "Bali", ["panel"], ["https://x.example/1", "https://b.example/2", "https://y.example/3"])
    two = issue("Solar farms in Bali", "Solar", "bali-solar", "Bali", ["panel"], ["https://x.example/1", "https://b.example/2", "https://c.example/3"])
    assert repeats.check(one, [entry("2026-11-10", base)]) == []
    assert "2 sources" in repeats.check(two, [entry("2026-11-10", base)])[0]


def test_old_entries_without_stored_fields_still_work_and_window_is_limited():
    old = {"date": "2026-11-01", "slug": "jakarta-floods-heavy-rain", "title": {"en": "Jakarta floods after heavy rain"}, "topic": {"en": "Floods"}}
    assert repeats.check(JAKARTA, [old])
    assert repeats.check(JAKARTA, [{"date": "x", "terms": ["unrelated"]}] * repeats.WINDOW + [old]) == []


def test_backfill_fills_only_entries_that_lack_the_fields():
    import json

    import backfill_repeats
    done = {"content": {"en": "a"}, "sources": ["x"], "terms": ["y"]}
    todo = {"content": {"en": "b"}}
    broken = {"content": {"en": "c"}}
    files = {"b": json.dumps(JAKARTA)}

    def read(name):
        if name not in files:
            raise OSError(name)
        return files[name]

    assert backfill_repeats.backfill([done, todo, broken], read) == 1
    assert done["sources"] == ["x"] and todo["terms"] == repeats.issue_terms(JAKARTA) and "sources" not in broken


def test_the_real_goosenecks_pair_is_caught_by_the_main_source():
    a = issue("How fast rivers carve deep rocks", "Water flow", "utah-goosenecks-river-flow", "Utah, USA", ["river"],
              ["https://science.nasa.gov/earth/earth-observatory/taking-a-gander-at-utahs-goosenecks", "https://a.example/1", "https://a.example/2"])
    b = issue("Meanders and gravity", "Energy", "utah-san-juan-river-meanders", "Utah", ["meander"],
              ["https://science.nasa.gov/earth/earth-observatory/taking-a-gander-at-utahs-goosenecks/", "https://b.example/1", "https://b.example/2"])
    assert "main source" in repeats.check(b, [entry("2026-11-08", a)])[0]
