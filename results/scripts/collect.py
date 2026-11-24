#!/usr/bin/env python3
"""Collect every AutoSE run from GitHub into results/: artifacts, results.csv, seeded_reviews.csv, runs.md.

Usage (from the submission repo root, with `gh` logged in):
    python results/scripts/collect.py               # download + tables
    python results/scripts/collect.py --hidden      # also score autose PR branches against the hidden tests
"""
from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = "AlooKaLaddoo/markdown"
ROOT = Path(__file__).resolve().parents[2]
RUNS = ROOT / "results" / "runs"
LABELS = json.loads((ROOT / "experiment" / "seeded_prs" / "labels.json").read_text())
HIDDEN = ROOT / "experiment" / "hidden_tests"


def gh(*a: str) -> str:
    return subprocess.run(["gh", *a], text=True, capture_output=True, check=True).stdout


def jget(path: Path) -> dict:
    return json.loads(path.read_text()) if path.exists() else {}


def tokens(agents: list[dict]) -> tuple[int, int, float]:
    return (sum(a.get("input_tokens", 0) for a in agents), sum(a.get("output_tokens", 0) for a in agents),
            sum(a.get("cost_usd_nominal", 0) for a in agents))


def download(run: dict) -> Path:
    d = RUNS / str(run["databaseId"])
    if (d / "run.json").exists() and run["status"] == "completed":
        return d
    d.mkdir(parents=True, exist_ok=True)
    subprocess.run(["gh", "run", "download", str(run["databaseId"]), "-R", REPO, "-D", str(d)],
                   capture_output=True, text=True)
    jobs = json.loads(gh("run", "view", str(run["databaseId"]), "-R", REPO, "--json", "jobs"))["jobs"]
    run = run | {"jobs": {j["name"]: j["conclusion"] for j in jobs}}
    (d / "run.json").write_text(json.dumps(run, indent=2))
    return d


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--hidden", action="store_true")
    args = ap.parse_args()
    runs = json.loads(gh("run", "list", "-R", REPO, "--workflow", "autose.yml", "-L", "200", "--json",
                         "databaseId,event,status,conclusion,displayTitle,createdAt,updatedAt,url"))
    rows, seeded, links = [], [], []
    for run in sorted(runs, key=lambda r: r["createdAt"]):
        if run["status"] != "completed":
            continue
        d = download(run)
        meta = jget(d / "run.json")
        jobs = meta.get("jobs", {})
        if jobs.get("gate") in (None, "skipped"):
            continue  # not a trigger (ordinary comment / other label)
        build_dir = next(iter(d.glob("autose-build-*")), None)
        rel_dir = next(iter(d.glob("autose-release-*")), None)
        rev_dir = next(iter(d.glob("autose-review-*")), None)
        st = jget(build_dir / "state.json") if build_dir else {}
        rel = jget(rel_dir / "release.json") if rel_dir else {}
        ver = jget(rev_dir / "verdict.json") if rev_dir else {}
        agents = st.get("agents", []) + ([ver["agent"]] if ver.get("agent") else [])
        tin, tout, cost = tokens(agents)
        minutes = round((_ts(run["updatedAt"]) - _ts(run["createdAt"])) / 60, 1)
        rev = ver.get("reviewer") or {}
        if rev_dir and rev_dir.name.startswith("autose-review-pr"):
            pr = rev_dir.name.removeprefix("autose-review-pr")
            lab = LABELS.get(pr, {})
            final = ver.get("decision", {}).get("final", "none")
            seeded.append({"run_id": run["databaseId"], "pr": pr, "seed": lab.get("seed", ""),
                           "variant": ver.get("variant", "main"), "model": ver.get("model", ""),
                           "expected": lab.get("expected", ""), "got": final,
                           "correct": final == lab.get("expected"),
                           "expected_route": lab.get("route", ""), "got_route": ver.get("decision", {}).get("route", ""),
                           "reviewer_raw_verdict": rev.get("verdict", ""),
                           "blocking_findings": sum(f["severity"] in ("blocker", "major") for f in rev.get("findings", [])),
                           "probe_done": rev.get("checklist", {}).get("own_probe_done", ""),
                           "input_tokens": tin, "output_tokens": tout, "cost_usd_nominal": round(cost, 3),
                           "minutes": minutes, "url": run["url"]})
            links.append(f"| {run['databaseId']} | review-only, seeded PR #{pr} ({lab.get('seed', '')}), variant "
                         f"`{ver.get('variant', 'main')}` | [run]({run['url']}) | [PR #{pr}](https://github.com/{REPO}/pull/{pr}) | {final} |")
            continue
        stages = st.get("stages", {})
        row = {"run_id": run["databaseId"], "issue": st.get("issue", ""), "round": st.get("round", ""),
               "variant": st.get("variant", ""), "from_stage": st.get("from_stage", ""),
               "s1_requirements": _ok(stages.get("requirements"), st.get("from_stage") != "requirements"),
               "s2_design": _ok(stages.get("design"), st.get("from_stage") == "implementation"),
               "s3_implementation": _ok(stages.get("implementation")),
               "s4_testing": _ok(stages.get("testing")),
               "s5_release": "pass" if rel.get("ok") else ("fail" if rel else "-"),
               "s6_review": ver.get("decision", {}).get("final", "-"),
               "review_route": ver.get("decision", {}).get("route", "-"),
               "impl_attempts": stages.get("implementation", {}).get("attempts", 0),
               "n_acceptance_criteria": len(stages.get("requirements", {}).get("acceptance_criteria", [])),
               "build_status": st.get("status", "-"), "stop_reason": st.get("reason", ""),
               "pr": rel.get("pr", ""), "ci": rel.get("ci", ""),
               "blocking_findings": sum(f["severity"] in ("blocker", "major") for f in rev.get("findings", [])),
               "input_tokens": tin, "output_tokens": tout, "cost_usd_nominal": round(cost, 3), "minutes": minutes,
               "url": run["url"]}
        rows.append(row)
        pr_link = f"[PR #{row['pr']}](https://github.com/{REPO}/pull/{row['pr']})" if row["pr"] else "-"
        links.append(f"| {run['databaseId']} | issue #{row['issue']} round {row['round']} (variant `{row['variant']}`, "
                     f"from {row['from_stage']}) | [run]({run['url']}) | {pr_link} | build {row['build_status']}, "
                     f"review {row['s6_review']} |")
    write_csv(ROOT / "results" / "results.csv", rows)
    write_csv(ROOT / "results" / "seeded_reviews.csv", seeded)
    (ROOT / "results" / "runs.md").write_text(
        "# Runs\n\nEvery triggering run of `autose.yml` in the fork, oldest first (generated by "
        "`results/scripts/collect.py`). Each run page has the stage artifacts (spec.md, design.md, diff.patch, "
        "test_report.md, pr.md, review.md, verdict.json, agent transcripts).\n\n"
        "| Run id | What | Actions run | Pull request | Outcome |\n|---|---|---|---|---|\n" + "\n".join(links) + "\n")
    tot_in = sum(r["input_tokens"] for r in rows + seeded)
    tot_out = sum(r["output_tokens"] for r in rows + seeded)
    print(f"{len(rows)} build runs, {len(seeded)} seeded reviews; tokens in={tot_in:,} out={tot_out:,}")
    if args.hidden:
        score_hidden(rows)


def score_hidden(rows):
    """Check out each autose PR head and run that issue's hidden tests."""
    out = []
    seen = {}
    for r in rows:
        if r["pr"]:
            seen[(r["issue"], r["variant"], r["pr"])] = r
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "fork"
        subprocess.run(["git", "clone", "-q", f"https://github.com/{REPO}.git", str(src)], check=True)
        subprocess.run([sys.executable, "-m", "venv", str(Path(tmp) / "venv")], check=True)
        py = str(Path(tmp) / "venv" / "bin" / "python")
        for (issue, variant, pr), r in seen.items():
            head = json.loads(gh("pr", "view", str(pr), "-R", REPO, "--json", "headRefOid,state"))
            subprocess.run(["git", "fetch", "-q", "origin", f"pull/{pr}/head"], cwd=src, check=True)
            subprocess.run(["git", "checkout", "-q", "--detach", head["headRefOid"]], cwd=src, check=True)
            subprocess.run([py, "-m", "pip", "install", "-q", "-e", ".[testing]"], cwd=src, check=True)
            p = subprocess.run([py, "-m", "unittest", "discover", "-v", "-s", str(HIDDEN), "-p", f"test_issue{issue}.py",
                                "-t", str(HIDDEN)], cwd=src, text=True, capture_output=True)
            passed = p.stderr.count("... ok")
            total = passed + p.stderr.count("... FAIL") + p.stderr.count("... ERROR")
            suite = subprocess.run([py, "-m", "unittest", "discover", "-s", "tests", "-t", "."], cwd=src, text=True,
                                   capture_output=True).stderr.strip().splitlines()[-1]
            out.append({"issue": issue, "variant": variant, "pr": pr, "head_sha": head["headRefOid"][:10],
                        "hidden_passed": passed, "hidden_total": total, "existing_suite": suite,
                        "detail": " | ".join(l for l in p.stderr.splitlines() if l.endswith(("ok", "FAIL", "ERROR")))})
            print(out[-1])
    write_csv(ROOT / "results" / "hidden_tests.csv", out)


def _ok(stage: dict | None, reused: bool = False) -> str:
    if reused and not stage:
        return "reused"
    if not stage:
        return "-"
    return "pass" if stage.get("ok") else "fail"


def _ts(s: str) -> float:
    from datetime import datetime
    return datetime.fromisoformat(s.replace("Z", "+00:00")).timestamp()


def write_csv(path: Path, rows: list[dict]):
    if not rows:
        path.write_text("")
        return
    with path.open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)


if __name__ == "__main__":
    main()
