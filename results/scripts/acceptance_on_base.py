#!/usr/bin/env python3
"""E2 metric: run each autose PR's acceptance-test file (tests/test_autose_issue_N.py, written by the Tester in the
main design or by the Implementer in E2) against the unchanged base code. A test that fails there detects the change.

Usage (from the submission repo root, gh logged in):  python results/scripts/acceptance_on_base.py
Writes results/acceptance_on_base.csv.
"""
import csv
import re
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "AlooKaLaddoo/markdown"
BASE = "4c2c535"  # fork setup commit = upstream 3f2c551 + workflow; product code identical to 3f2c551
PRS = [(12, 1, "main"), (15, 2, "main"), (11, 3, "main"), (13, 4, "main"), (14, 5, "main"),
       (16, 1, "e2"), (18, 2, "e2"), (17, 3, "e2"), (19, 4, "e2"), (20, 5, "e2")]
ROOT = Path(__file__).resolve().parents[2]

rows = []
with tempfile.TemporaryDirectory() as tmp:
    src = Path(tmp) / "fork"
    subprocess.run(["git", "clone", "-q", f"https://github.com/{REPO}.git", str(src)], check=True)
    subprocess.run(["git", "checkout", "-q", BASE], cwd=src, check=True)
    subprocess.run([sys.executable, "-m", "venv", str(Path(tmp) / "venv")], check=True)
    py = str(Path(tmp) / "venv" / "bin" / "python")
    subprocess.run([py, "-m", "pip", "install", "-q", "-e", ".[testing]"], cwd=src, check=True)
    for pr, issue, variant in PRS:
        subprocess.run(["git", "fetch", "-q", "origin", f"pull/{pr}/head"], cwd=src, check=True)
        name = f"tests/test_autose_issue_{issue}.py"
        test = subprocess.run(["git", "show", f"FETCH_HEAD:{name}"], cwd=src, text=True, capture_output=True,
                              check=True).stdout
        (src / name).write_text(test)
        out = subprocess.run([py, "-m", "unittest", name], cwd=src, text=True, capture_output=True).stderr
        (src / name).unlink()
        ran = int(re.search(r"Ran (\d+) test", out).group(1))
        failed = sum(int(n) for n in re.findall(r"(?:failures|errors)=(\d+)", out.splitlines()[-1]))
        rows.append({"pr": pr, "issue": issue, "variant": variant, "acceptance_tests": ran,
                     "fail_on_base": failed, "base_result": out.strip().splitlines()[-1]})
        print(rows[-1])
with (ROOT / "results" / "acceptance_on_base.csv").open("w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
for v in ("main", "e2"):
    sel = [r for r in rows if r["variant"] == v]
    print(v, sum(r["fail_on_base"] for r in sel), "of", sum(r["acceptance_tests"] for r in sel))
