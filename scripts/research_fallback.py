"""Write (or repair) an issue with an OpenAI-compatible provider when Gemini CLI could not.

Usage: python scripts/research_fallback.py issues/YYYY-MM-DD [--problems FILE]
Env: RESEARCH_BASE_URL, RESEARCH_API_KEY, RESEARCH_MODEL (default openai/gpt-oss-120b with Groq's
server-side browser_search; any chat model that searches on its own works, e.g. an OpenCode one).
Three calls: en.json (searches the web, or fixes the listed problems), id.json (translation),
calc.py. sources.md is built from en.json. The normal validate + repair steps still judge the result.
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parent.parent
MAX_CONTEXT = 12000


def chat(base, key, model, system, user):
    if not base.startswith("https://"):
        raise ValueError("research base URL must be https")
    body = {"model": model, "max_tokens": 8000, "temperature": 0.3,
            "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]}
    if "openrouter.ai" in base:  # OpenRouter runs the web search itself (Exa), for any model
        body["plugins"] = [{"id": "web", "max_results": 6}]
    elif model.startswith("openai/gpt-oss"):  # Groq runs the search itself; other models must search on their own
        body["tools"] = [{"type": "browser_search"}]
    for attempt in range(3):
        r = requests.post(f"{base.rstrip('/')}/chat/completions", headers={"Authorization": f"Bearer {key}"},
                          json=body, timeout=300)
        if r.status_code == 429 or r.status_code >= 500:
            time.sleep(20 * (attempt + 1))
            continue
        if r.status_code == 404:  # wrong model name: say which ones this key can use
            try:
                ids = [m["id"] for m in requests.get(f"{base.rstrip('/')}/models", headers={"Authorization": f"Bearer {key}"}, timeout=30).json()["data"]]
            except (requests.RequestException, KeyError, ValueError):
                ids = []
            raise ValueError(f"research provider HTTP 404: {r.text[:200]} Available models: {ids}")
        if not r.ok:
            raise ValueError(f"research provider HTTP {r.status_code}: {r.text[:300]}")
        choice = (r.json().get("choices") or [{}])[0]
        if choice.get("finish_reason") != "stop":
            raise ValueError(f"research provider stopped early: finish_reason={choice.get('finish_reason')!r} usage={r.json().get('usage')} tail={(choice.get('message', {}).get('content') or '')[-200:]!r}")
        return choice["message"]["content"] or ""
    raise ValueError("research provider kept returning 429/5xx")


def extract(text, kind):
    """The first JSON object (or python block) in a reply, without markdown fences."""
    if kind == "py":
        m = re.search(r"```(?:python)?\n(.*?)```", text, re.S)
        return (m.group(1) if m else text).strip() + "\n"
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end < start:
        raise ValueError("reply has no JSON object")
    return json.loads(text[start:end + 1])


def sources_md(en):
    lines = []
    for s in en.get("_sources", []):
        lines += [f"{s['n']}. **{s['publisher']}**, \"{s['title']}\", {s['date']}.", f"   URL: `{s['url']}`", ""]
    return "\n".join(lines)


def read(path, limit=MAX_CONTEXT):
    try:
        return Path(path).read_text(encoding="utf-8")[:limit]
    except OSError:
        return ""


def write(folder, name, text):
    # write via a temp name so a later failure never leaves a half-written file under the real one
    tmp = folder / (name + ".tmp")
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(folder / name)


def run(folder, base, key, model, problems=None, root=ROOT):
    folder, root = Path(folder), Path(root)
    date = folder.name
    guide = (root / "GEMINI.md").read_text(encoding="utf-8")
    system = (f"{guide}\n\n## Example en.json\n{read(root / 'schema/example.en.json', 20000)}\n\n"
              f"## Example calc.py\n{read(root / 'schema/example.calc.py')}\n\n"
              f"## Limits (schema/limits.json)\n{read(root / 'schema/limits.json')}\n\n"
              f"## Formula bank (schema/formulas.json)\n{read(root / 'schema/formulas.json', 20000)}\n\n"
              "You have no file tools: reply with the requested file content only. Search the web and open "
              "real pages for every source; never invent a URL, title, date or number.")
    catalogue = read(root / ".gemini/published-manifest.json") or read(root / "manifest.json")
    remedial = read(root / ".gemini/remedial-brief.json")
    folder.mkdir(parents=True, exist_ok=True)
    if problems:
        task = (f"Repair issues/{date}/en.json. These checks failed:\n{problems}\n\nCurrent en.json:\n"
                f"{read(folder / 'en.json', 30000)}\n\nSource evidence (pages that were opened):\n"
                f"{read(root / '.gemini/source-evidence.json')}\n\nFix only these problems. A source that is "
                "missing, off-topic or a homepage is replaced by the exact article you find and open. "
                "Reply with the complete corrected en.json object only.")
    else:
        task = (f"Today is {date} (Asia/Jakarta). Write issues/{date}/en.json now. Catalogue of published "
                f"issues (next _issue number, topics and sources to avoid):\n{catalogue}\n"
                + (f"\nRemedial brief (today is a remedial day):\n{remedial}\n" if remedial else "")
                + "\nReply with the complete en.json object only.")
    en = extract(chat(base, key, model, system, task), "json")
    if not isinstance(en.get("_sources"), list) or not en["_sources"]:
        raise ValueError("en.json has no _sources")
    en_text = json.dumps(en, ensure_ascii=False, indent=1)
    idj = extract(chat(base, key, model, system,
                       f"Write issues/{date}/id.json for this en.json, following the id.json section. "
                       f"Reply with the complete id.json object only.\n\n{en_text}"), "json")
    calc = extract(chat(base, key, model, system,
                        "Write calc.py for this en.json (standard library only, prints one JSON object with "
                        "every computed value, as in the example). Reply with the python code only.\n\n" + en_text),
                   "py")
    compile(calc, "calc.py", "exec")
    for name, text in (("en.json", en_text + "\n"), ("id.json", json.dumps(idj, ensure_ascii=False, indent=1) + "\n"),
                       ("calc.py", calc), ("sources.md", sources_md(en))):
        write(folder, name, text)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("folder")
    ap.add_argument("--problems")
    a = ap.parse_args()
    env = os.environ.get
    if not (env("RESEARCH_BASE_URL") and env("RESEARCH_API_KEY")):
        sys.exit("RESEARCH_BASE_URL and RESEARCH_API_KEY are required")
    run(a.folder, env("RESEARCH_BASE_URL"), env("RESEARCH_API_KEY"), env("RESEARCH_MODEL") or "openai/gpt-oss-120b",
        read(a.problems, 6000) if a.problems else None)
    print(f"Wrote {a.folder} with the fallback provider.")
