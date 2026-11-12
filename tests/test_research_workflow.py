"""Exercise the actual date/resume shell step without contacting GitHub."""
import os
import re
import subprocess
import textwrap
from pathlib import Path

import pytest


def test_gemini_can_read_generated_evidence_without_exposing_its_settings(tmp_path):
    root = Path(__file__).resolve().parents[1]
    (tmp_path / ".gitignore").write_text((root / ".gitignore").read_text())
    (tmp_path / ".gemini").mkdir()
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    for name, ignored in (("published-manifest.json", False), ("source-evidence.json", False), ("settings.json", True)):
        path = f".gemini/{name}"
        (tmp_path / path).write_text("{}")
        result = subprocess.run(["git", "check-ignore", "-q", path], cwd=tmp_path)
        assert result.returncode == int(not ignored)


@pytest.mark.parametrize("resume,exists,filled,expected,output", [
    ("false", "true", "false", 0, "skip=true"),
    ("false", "false", "false", 0, "branch=guide/2026-11-12"),
    ("true", "true", "false", 0, "resume=true"),
    ("true", "true", "true", 1, "Already filled in Figma"),
    ("true", "false", "false", 1, "branch=guide/2026-11-12"),
])
def test_resume_preserves_failed_branches_and_rejects_filled_issues(tmp_path, resume, exists, filled, expected, output):
    workflow = (Path(__file__).resolve().parents[1] / ".github/workflows/daily-research.yml").read_text()
    block = workflow.split("      - name: Pick date and skip if it exists\n", 1)[1]
    script = textwrap.dedent(re.search(r"        run: \|\n(.*?)(?=\n  research:)", block, re.S)[1])
    git = tmp_path / "git"
    git.write_text('#!/bin/bash\ncase "$1" in\nfetch|ls-remote) test "$EXISTS" = true;;\ncat-file) test "$FILLED" = true;;\n*) exit 99;;\nesac\n')
    git.chmod(0o755)
    out = tmp_path / "output"
    result = subprocess.run(["bash", "-e", "-o", "pipefail", "-c", script], cwd=tmp_path,
                            env=dict(os.environ, PATH=f"{tmp_path}:{os.environ['PATH']}", INPUT_DATE="2026-11-12",
                                     DRY_RUN="false", RESUME=resume, EXISTS=exists, FILLED=filled, GITHUB_OUTPUT=str(out)),
                            text=True, capture_output=True)
    assert result.returncode == expected, result.stderr
    assert output in result.stdout + out.read_text()
    if resume == "true":
        assert "skip=true" not in out.read_text()
