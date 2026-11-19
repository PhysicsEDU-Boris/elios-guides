#!/usr/bin/env python3
"""Keep a repair only if it left fewer validation problems than before.

usage: keep_better.py issues/YYYY-MM-DD SNAPSHOT_DIR BASELINE_COUNT [--manifest M] [--check-sources]

Validates the issue folder as it is now. If that has more problems than BASELINE_COUNT, the folder's
files are replaced by the copy in SNAPSHOT_DIR (taken before the repair), so a repair that deletes
content or breaks a valid file can never make the issue worse. Prints the problem count that stands.
"""
import re
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def count_problems(output):
    """Problem count from validate.py output; None when the output is not recognisable."""
    if re.search(r"^OK\s*$", output, re.M):
        return 0
    m = re.search(r"VALIDATION FAILED \((\d+) problems?\)", output)
    return int(m.group(1)) if m else None


def validate(folder, extra):
    proc = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate.py"), str(folder), *extra],
                          capture_output=True, text=True)
    return proc.stdout + proc.stderr


def restore(folder, snapshot):
    folder, snapshot = Path(folder), Path(snapshot)
    for p in folder.iterdir():
        if p.is_file():
            p.unlink()
    for p in snapshot.iterdir():
        if p.is_file():
            shutil.copy2(p, folder / p.name)


def main(argv):
    if len(argv) < 3:
        sys.exit(__doc__)
    folder, snapshot, baseline = argv[0], argv[1], int(argv[2])
    extra = argv[3:]
    now = count_problems(validate(folder, extra))
    if now is None or now > baseline:
        restore(folder, snapshot)
        print(f"repair made it worse ({now} problems, was {baseline}); kept the files from before the repair")
        return baseline
    print(f"repair kept ({now} problems, was {baseline})")
    return now


if __name__ == "__main__":
    main(sys.argv[1:])
