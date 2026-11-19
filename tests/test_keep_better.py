import keep_better


def test_count_problems():
    assert keep_better.count_problems("OK\n") == 0
    assert keep_better.count_problems("VALIDATION FAILED (7 problems):\n- a") == 7
    assert keep_better.count_problems("VALIDATION FAILED (1 problem):\n- a") == 1
    assert keep_better.count_problems("Traceback ...") is None


def make(tmp_path):
    folder, snap = tmp_path / "issue", tmp_path / "snap"
    folder.mkdir(exist_ok=True)
    snap.mkdir(exist_ok=True)
    (snap / "en.json").write_text("before")
    (folder / "en.json").write_text("after")
    (folder / "extra.txt").write_text("x")
    return folder, snap


def test_worse_repair_is_reverted(tmp_path, monkeypatch):
    folder, snap = make(tmp_path)
    monkeypatch.setattr(keep_better, "validate", lambda f, e: "VALIDATION FAILED (106 problems):")
    assert keep_better.main([str(folder), str(snap), "2"]) == 2
    assert (folder / "en.json").read_text() == "before"
    assert not (folder / "extra.txt").exists()


def test_unreadable_validation_is_reverted(tmp_path, monkeypatch):
    folder, snap = make(tmp_path)
    monkeypatch.setattr(keep_better, "validate", lambda f, e: "Traceback")
    keep_better.main([str(folder), str(snap), "2"])
    assert (folder / "en.json").read_text() == "before"


def test_better_or_equal_repair_is_kept(tmp_path, monkeypatch):
    for out, expected in (("VALIDATION FAILED (1 problems):", 1), ("OK", 0), ("VALIDATION FAILED (2 problems):", 2)):
        folder, snap = make(tmp_path)
        monkeypatch.setattr(keep_better, "validate", lambda f, e, out=out: out)
        assert keep_better.main([str(folder), str(snap), "2"]) == expected
        assert (folder / "en.json").read_text() == "after"
        (snap / "en.json").write_text("before")
        (folder / "en.json").write_text("after")
