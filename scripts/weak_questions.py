"""Turn the answer statistics in Supabase into a brief for a remedial guide.

Usage: python scripts/weak_questions.py --date YYYY-MM-DD --manifest CATALOGUE.json --out .gemini/remedial-brief.json
Env:   SUPABASE_URL, SUPABASE_SERVICE_KEY (Actions secrets). Without them, or with too little data, no brief
       is written and the day stays a normal news guide.
Every second day (even date ordinal) is a remedial day. The brief names the concept (formula) students miss
most, the hardest questions with their most common wrong answer, and avoids a concept covered in the last
COOLDOWN_DAYS days (manifest entry field `remedial.concept`).
"""
import argparse
import json
import os
import re
import sys
from datetime import date
from pathlib import Path

import requests

PAGES = "https://physicsedu-boris.github.io/elios-guides/"
MIN_ATTEMPTS = 60  # answers per concept before it counts
MIN_QUESTION = 30  # answers per question (also enforced by question_stats)
COOLDOWN_DAYS = 14
LETTERS = "abcd"


def is_remedial_day(d):
    return d.toordinal() % 2 == 0


def concept_of(en):
    """The concept a guide teaches: its formula id (or, for old guides, the printed equation)."""
    return {"key": en.get("_formula") or en.get("physics.equation", ""), "formula": en.get("_formula"),
            "equation": en.get("physics.equation", ""), "name": en.get("physics.equation_name", ""), "theme": en.get("_theme")}


def question_of(en, qid):
    """(question, {letter: option}, correct letter) for p1-p3 (printed) or pool-N (0-based quiz pool, as the app names them); None if absent."""
    try:
        if re.fullmatch(r"p[1-3]", qid):
            n = qid[1:]
            return (en[f"quiz.{n}.question"], {l: en[f"quiz.{n}.{l}"] for l in LETTERS}, str(en["_answers"][n]).lower())
        q = en["_quiz_pool"][int(re.fullmatch(r"pool-(\d{1,2})", qid)[1])]
        return q["question"], dict(zip(LETTERS, q["options"])), LETTERS[int(q["answer"])]
    except (KeyError, IndexError, ValueError, TypeError):  # TypeError: no regex match
        return None


def rank(stats, docs):
    """Concepts with enough answers, hardest first. stats: question_stats rows; docs: {date: en.json dict}."""
    groups = {}
    for row in stats:
        en = docs.get(str(row["guide_date"]))
        q = question_of(en, row["question_id"]) if en else None
        if not q or row["attempts"] < MIN_QUESTION:
            continue
        g = groups.setdefault(concept_of(en)["key"], {"concept": concept_of(en), "attempts": 0, "wrong": 0, "questions": []})
        g["attempts"] += row["attempts"]
        g["wrong"] += row["wrong"]
        wrong_opt = row.get("top_wrong")
        g["questions"].append({
            "guide_date": str(row["guide_date"]), "question_id": row["question_id"], "question": q[0],
            "correct": f"{q[2].upper()}: {q[1][q[2]]}", "attempts": row["attempts"], "wrong_rate": float(row["wrong_rate"]),
            "most_common_wrong": f"{wrong_opt.upper()}: {q[1][wrong_opt]}" if wrong_opt in q[1] else None,
        })
    out = [g for g in groups.values() if g["attempts"] >= MIN_ATTEMPTS]
    for g in out:
        g["wrong_rate"] = round(g["wrong"] / g["attempts"], 3)
        g["questions"].sort(key=lambda q: -q["wrong_rate"])
    return sorted(out, key=lambda g: -g["wrong_rate"])


def pick(ranked, guides, today):
    """First ranked concept not covered by a remedial guide in the last COOLDOWN_DAYS days."""
    recent = {(g.get("remedial") or {}).get("concept") for g in guides
              if (g.get("remedial") or {}).get("concept") and (today - date.fromisoformat(g["date"])).days < COOLDOWN_DAYS}
    return next((g for g in ranked if g["concept"]["key"] not in recent), None)


def brief(choice):
    return {"concept": choice["concept"], "attempts": choice["attempts"], "wrong_rate": choice["wrong_rate"],
            "questions": choice["questions"][:3]}


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--date", required=True)
    ap.add_argument("--manifest", required=True)
    ap.add_argument("--out", required=True)
    args = ap.parse_args(argv)
    out, today = Path(args.out), date.fromisoformat(args.date)
    out.unlink(missing_ok=True)  # never leave a stale brief
    url, key = os.environ.get("SUPABASE_URL"), os.environ.get("SUPABASE_SERVICE_KEY")
    if not is_remedial_day(today):
        print(f"{today} is a news day: no remedial brief")
        return 0
    if not (url and key):
        print("SUPABASE_URL / SUPABASE_SERVICE_KEY not set: no remedial brief")
        return 0
    guides = json.loads(Path(args.manifest).read_text(encoding="utf-8")).get("guides") or []
    try:
        r = requests.post(f"{url.rstrip('/')}/rest/v1/rpc/question_stats", timeout=60,
                          headers={"apikey": key, "Authorization": f"Bearer {key}"}, json={"p_days": 30, "p_min": MIN_QUESTION})
        r.raise_for_status()
        stats = r.json()
        docs = {}
        for g in guides:
            if any(str(s["guide_date"]) == g["date"] for s in stats):
                docs[g["date"]] = requests.get(PAGES + g["content"]["en"], timeout=60).json()
    except (requests.RequestException, ValueError, KeyError) as e:
        print(f"could not read statistics ({type(e).__name__}): no remedial brief")  # a news guide still goes out
        return 0
    choice = pick(rank(stats, docs), guides, today)
    if not choice:
        print("not enough answers yet (or every weak concept was covered recently): no remedial brief")
        return 0
    out.write_text(json.dumps(brief(choice), indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"remedial brief: {choice['concept']['name'] or choice['concept']['key']} ({choice['wrong_rate']:.0%} wrong over {choice['attempts']} answers)")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
