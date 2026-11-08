"""Check one issue folder before it goes to Figma.

Usage: python scripts/validate.py issues/YYYY-MM-DD [--manifest manifest.json]
Exit 0 = OK, exit 1 = prints the list of problems.
"""
import json
import re
import sys
from pathlib import Path
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent.parent
LIMITS = json.loads((ROOT / "schema" / "limits.json").read_text(encoding="utf-8"))
ALLOWED_DOMAINS = ("nasa.gov", "noaa.gov", "usgs.gov", "esa.int", "copernicus.eu", "wikimedia.org", "bmkg.go.id")
OPTIONAL = {f"legend.{i}.{p}" for i in (4, 5) for p in ("symbol", "meaning", "unit")} | {"source.4", "source.5"}
# keys only id.json may have (see GEMINI.md)
ID_EXTRA = {
    "label.quest_map", "label.fun_fact", "label.timeline", "label.equation", "label.example",
    "label.graph", "label.tip", "label.quiz", "label.lab", "label.badge",
    "quest.1.title", "quest.2.title", "quest.3.title", "_per_page", "_replace",
}
TOLERANCE = 0.02
SCALE = {"k": 1e3, "thousand": 1e3, "rb": 1e3, "ribu": 1e3, "million": 1e6, "jt": 1e6, "juta": 1e6,
         "billion": 1e9, "bn": 1e9, "miliar": 1e9, "m": 1e6, "M": 1e9}


def domain_ok(url):
    host = (urlparse(url or "").hostname or "").lower()
    return urlparse(url or "").scheme == "https" and any(host == d or host.endswith("." + d) for d in ALLOWED_DOMAINS)


def parse_numbers(text, lang):
    """Numbers in a string, also scaled by a following word like 'million' / 'jt'. Returns list of candidate sets."""
    text = re.sub(r"\[\d+\]", "", str(text)).replace("−", "-")
    if lang == "id":
        pat, thou, dec = r"\d{1,3}(?:\.\d{3})+(?:,\d+)?|\d+(?:,\d+)?", ".", ","
    else:
        pat, thou, dec = r"\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?", ",", "."
    out = []
    for m in re.finditer(rf"({pat})\s*([A-Za-z]+)?", text):
        n = float(m.group(1).replace(thou, "").replace(dec, "."))
        cands = {n}
        word = m.group(2) or ""
        if word in SCALE or word.lower() in SCALE:
            cands.add(n * SCALE.get(word, SCALE.get(word.lower())))
        out.append(cands)
    return out


def flat_numbers(obj):
    if isinstance(obj, bool):
        return []
    if isinstance(obj, (int, float)):
        return [float(obj)]
    if isinstance(obj, dict):
        obj = list(obj.values())
    if isinstance(obj, list):
        return [x for v in obj for x in flat_numbers(v)]
    return []


def close(n, values):
    return any(abs(abs(n) - abs(v)) <= TOLERANCE * abs(v) if v else n == 0 for v in values)


def strings(obj):
    if isinstance(obj, str):
        yield obj
    elif isinstance(obj, dict):
        for v in obj.values():
            yield from strings(v)
    elif isinstance(obj, list):
        for v in obj:
            yield from strings(v)


def answer_key_letters(text):
    return {n: l.lower() for n, l in re.findall(r"([123])\s*([A-Da-d])\b", text or "")}


def check_lang(d, lang, folder):
    errs = []
    for k, limit in LIMITS.items():
        if k not in d:
            errs.append(f"{lang}: missing key {k}")
            continue
        v = d[k]
        if not isinstance(v, str):
            errs.append(f"{lang}: {k} must be a string")
            continue
        if v == "" and k not in OPTIONAL:
            errs.append(f"{lang}: {k} is empty (only legend.4/5.* and source.4/5 may be empty)")
        if len(v) > limit:
            errs.append(f"{lang}: {k} is {len(v)} chars, limit {limit}")
    for k, v in d.items():
        if any(c in s for s in strings(v) for c in "{}"):
            errs.append(f"{lang}: {k} contains {{ or }}")

    # answers
    ans = d.get("_answers") or {}
    if sorted(ans) != ["1", "2", "3"] or any(str(a).lower() not in "abcd" or len(str(a)) != 1 for a in ans.values()):
        errs.append(f"{lang}: _answers must be {{'1','2','3'}} → a/b/c/d")
    elif len({str(a).lower() for a in ans.values()}) == 1:
        errs.append(f"{lang}: all 3 correct answers are the same letter")
    if answer_key_letters(d.get("quiz.answer_key")) != {k: str(v).lower() for k, v in ans.items()}:
        errs.append(f"{lang}: quiz.answer_key {d.get('quiz.answer_key')!r} does not match _answers {ans}")

    # sources
    srcs = d.get("_sources") or []
    ns = {s.get("n") for s in srcs if isinstance(s, dict)}
    if len(srcs) < 3:
        errs.append(f"{lang}: only {len(srcs)} sources, need at least 3")
    if not any(isinstance(s, dict) and s.get("primary") is True for s in srcs):
        errs.append(f"{lang}: no source has primary: true")
    for src in srcs:
        if isinstance(src, dict) and urlparse(str(src.get("url", ""))).path.strip("/") == "":
            errs.append(f"{lang}: source {src.get('n')} url {src.get('url')!r} is a homepage; link the article or data page")
    if not re.fullmatch(r"\d{2,}", str(d.get("_issue", ""))):
        errs.append(f"{lang}: _issue {d.get('_issue')!r} must be at least two digits, e.g. \"03\"")
    for k, v in d.items():
        if k.startswith("_"):
            continue
        for n in re.findall(r"\[(\d+)\]", str(v)):
            if int(n) not in ns:
                errs.append(f"{lang}: {k} cites [{n}] but there is no _sources entry {n}")

    # images
    for key, img in (d.get("_images") or {}).items():
        if img is None:
            continue
        if not img.get("license") or not img.get("credit"):
            errs.append(f"{lang}: image {key} needs license and credit")
        if not domain_ok(img.get("source_url")):
            errs.append(f"{lang}: image {key} source_url {img.get('source_url')!r} is not https on {', '.join(ALLOWED_DOMAINS)}")
        if not img.get("file") or Path(img["file"]).name != img["file"] or not (folder / img["file"]).is_file():
            errs.append(f"{lang}: image {key} file {img.get('file')!r} was not downloaded")

    # numbers vs calc.out.json
    calc_path = folder / "calc.out.json"
    if not calc_path.is_file():
        errs.append("calc.out.json is missing (calc.py did not run)")
    else:
        values = flat_numbers(json.loads(calc_path.read_text(encoding="utf-8")))
        for i in (1, 2, 3):
            raw = d.get(f"_graph.{i}.raw")
            if not isinstance(raw, (int, float)) or isinstance(raw, bool):
                errs.append(f"{lang}: _graph.{i}.raw must be a number")
            elif not close(raw, values):
                errs.append(f"{lang}: _graph.{i}.raw = {raw} is not in calc.out.json (±2%)")
        # ponytail: table headers/note are labels (e.g. "PM2.5"), so only the 9 cells are checked
        keys = [f"table.r{r}c{c}" for r in (1, 2, 3) for c in (1, 2, 3)] + ["example.result"] + [f"graph.{i}.value" for i in (1, 2, 3)]
        for k in keys:
            for cands in parse_numbers(d.get(k, ""), lang):
                if not any(close(n, values) for n in cands):
                    errs.append(f"{lang}: {k} = {d.get(k)!r}: {min(cands):g} is not in calc.out.json (±2%)")
    return errs


def check(folder, manifest_path=ROOT / "manifest.json"):
    folder = Path(folder)
    errs = []
    docs = {}
    for lang in ("en", "id"):
        p = folder / f"{lang}.json"
        try:
            docs[lang] = json.loads(p.read_text(encoding="utf-8"))
        except FileNotFoundError:
            errs.append(f"{p.name} is missing")
        except json.JSONDecodeError as e:
            errs.append(f"{p.name} is not valid JSON: {e}")
    if errs:
        return errs
    en, id_ = docs["en"], docs["id"]
    for lang, d in docs.items():
        errs += check_lang(d, lang, folder)

    only_en = set(en) - set(id_)
    only_id = set(id_) - set(en) - ID_EXTRA
    if only_en:
        errs.append(f"keys in en.json but not id.json: {sorted(only_en)}")
    if only_id:
        errs.append(f"keys in id.json but not en.json: {sorted(only_id)}")
    if en.get("_answers") != id_.get("_answers"):
        errs.append(f"_answers differ: en {en.get('_answers')} id {id_.get('_answers')}")
    if len(en.get("_quiz_pool") or []) != len(id_.get("_quiz_pool") or []):
        errs.append("_quiz_pool has a different number of questions in en.json and id.json")

    check_path = folder / "check.json"
    try:
        items = json.loads(check_path.read_text(encoding="utf-8"))
        for it in items:
            if it.get("pass") is not True:
                errs.append(f"fact-check failed: {it.get('item')}: {it.get('claim')} ({it.get('note')})")
    except FileNotFoundError:
        errs.append("check.json is missing (fact-check did not run)")
    except (json.JSONDecodeError, AttributeError, TypeError) as e:
        errs.append(f"check.json is not a list of objects: {e}")

    guides = json.loads(Path(manifest_path).read_text(encoding="utf-8")).get("guides") or []
    if any(g.get("date") == folder.name for g in guides):
        errs.append(f"{folder.name} is already in manifest.json")
    slug, topic = str(en.get("_slug", "")).lower(), str(en.get("cover.topic", "")).strip().lower()
    for g in guides[:14]:
        if str(g.get("slug", "")).lower() == slug:
            errs.append(f"slug {slug!r} was used on {g.get('date')}")
        if topic and str((g.get("topic") or {}).get("en", "")).strip().lower() == topic:
            errs.append(f"topic {topic!r} was used on {g.get('date')}")
    return errs


def main(argv):
    if not argv or argv[0].startswith("-"):
        sys.exit("usage: validate.py issues/YYYY-MM-DD [--manifest manifest.json]")
    manifest = Path(argv[argv.index("--manifest") + 1]) if "--manifest" in argv else ROOT / "manifest.json"
    errs = check(argv[0], manifest)
    if errs:
        print(f"VALIDATION FAILED ({len(errs)} problems):")
        print("\n".join(f"- {e}" for e in errs))
        return 1
    print("OK")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
