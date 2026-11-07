"""Run issues/<date>/calc.py in isolation and save its JSON output as calc.out.json.

Usage: python scripts/run_calc.py issues/YYYY-MM-DD
"""
import json
import subprocess
import sys
from pathlib import Path


def run(folder):
    folder = Path(folder)
    # -I: isolated mode (no user site, no PYTHON* env, script dir not on sys.path).
    # Minimal env: no proxy vars, no tokens. ponytail: this is not a network sandbox; the
    # workflow step simply has no secrets. Add a firewall/container if calc.py ever needs stronger limits.
    proc = subprocess.run(
        [sys.executable, "-I", "calc.py"], cwd=folder, env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
        capture_output=True, text=True, timeout=30,
    )
    if proc.returncode != 0:
        raise SystemExit(f"calc.py failed (exit {proc.returncode}):\n{proc.stderr[-2000:]}")
    try:
        out = json.loads(proc.stdout)
    except json.JSONDecodeError as e:
        raise SystemExit(f"calc.py must print one JSON object: {e}\n{proc.stdout[:500]}")
    if not isinstance(out, dict):
        raise SystemExit("calc.py must print a JSON object, not " + type(out).__name__)
    (folder / "calc.out.json").write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    return out


if __name__ == "__main__":
    if len(sys.argv) != 2:
        sys.exit("usage: run_calc.py issues/YYYY-MM-DD")
    print(json.dumps(run(sys.argv[1]), ensure_ascii=False))
