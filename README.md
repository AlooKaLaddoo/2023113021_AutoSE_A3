# AutoSE Assignment 3: an agentic SDLC workflow (issue in, reviewed pull request out)

Roll number 2023113021. Report: [`report.pdf`](report.pdf) (source [`report.md`](report.md)).

## Where it runs

- **Fork:** <https://github.com/AlooKaLaddoo/markdown>. It is a fork of `Python-Markdown/markdown`, pinned at upstream commit
  **`3f2c5510bd8d64a73ec18342f740371bcde9b20c`**, with one setup commit on top (workflow, agent code, CI, the A2
  `ARCHITECTURE.md`), and later fix commits whose messages link the runs that motivated them.
- **Workflow:** [`.github/workflows/autose.yml`](https://github.com/AlooKaLaddoo/markdown/blob/master/.github/workflows/autose.yml).
  The agent code is in [`.github/autose/`](https://github.com/AlooKaLaddoo/markdown/tree/master/.github/autose).
  A copy of both is in [`workflow/`](workflow/).
  The copy includes [PR #21](https://github.com/AlooKaLaddoo/markdown/pull/21) (result-event parsing and credential-free
  checks), a fix made after all runs had finished while we checked the results. No run used it.
- **Protected `master`:** Python-Markdown's default branch is `master` (the brief's `main`). It needs a pull request and the `tests` CI check, also for admins, and allows no force pushes. The workflow never merges.
  *Timeline:* protection (PR + `tests` check, no force pushes) was switched on at setup, but **admin enforcement was off
  while the workflow was being debugged**. Our own fix commits `0799449`, `79cd0cc`, `3eb36e4`, `6b5f4a3` and
  `dc99bf1` were therefore pushed by the repository owner directly to `master`. Each one's message names the run that
  exposed the bug. Admin enforcement was switched on after the last run, so since then nobody, admins included, can
  push to `master` directly.
- **Where the CI proof is.** The release job dispatches `ci.yml` on the PR branch (pushes made with `GITHUB_TOKEN` do
  not trigger workflows) and waits for it. That run is linked in each run's `release.json` and in the PR description's
  stage 5 check. GitHub treats `github-actions[bot]` as a first-time contributor (approval policy
  `first_time_contributors`), so the PR-triggered `ci` runs on bot PRs wait for a maintainer's approval. We approved
  them after the experiment, and every autose PR (#11-#20) now shows the `tests` check passing on its head commit.
  Approving the waiting run is therefore a small manual step for a maintainer after every bot PR.

## Models

All agents run as headless Claude Code (`claude -p`, CLI 2.1.331) on a **Claude Team subscription**. The token
comes from `claude setup-token` and is stored as the repository secret `CLAUDE_CODE_OAUTH_TOKEN`. There is no
per-token API bill, so the spending limit is the plan's usage limit (ADR-006). Token counts are reported from the
CLI's usage output (`results/results.csv`). **Total over all 26 runs: 9.25 M input tokens (mostly cache reads) and 0.36 M output tokens, counted from every result event in the transcripts; $0 billed (API-list equivalent $15.67).**

| Role | Stages | Model |
|---|---|---|
| Analyst | 1 Requirements (our A1 skill), 2 Design (our A2 `ARCHITECTURE.md`) | `claude-opus-5-5` |
| Spec testability judge | inside the stage 1 check | `claude-haiku-5-5` |
| Implementer | 3 Implementation | `claude-opus-5-5` |
| Tester | 4 Testing (acceptance tests written from the spec, blind to the code) | `claude-opus-5-5` |
| Release | 5 (deterministic code, no LLM) | none |
| Reviewer | 6 Review (separate job, read-only token) | `claude-sonnet-5-5` |

## How to trigger

Only `OWNER`, `MEMBER` and `COLLABORATOR` can start a run.

| You do | Effect |
|---|---|
| Add the label **`autose`** to an issue | full run: stages 1-6, review rounds re-dispatched automatically (at most 2 send-backs) |
| Comment **`/autose`** on an issue | same as the label |
| Comment **`/autose review`** on a pull request whose body says `Closes #N` | stage 6 only (used for the seeded PRs) |
| Add `variant=e1_friendly_reviewer` or `variant=e2_implementer_writes_tests` to the comment, or use *Run workflow* (`workflow_dispatch`) | decision-experiment variants (`experiment/variants.md`) |

Progress is visible in three places: the Actions run (every stage's artifacts and agent transcripts), the PR (`pr.md` as
its description, the review as a PR review), and a status comment on the issue that links every round.

## Repository layout

```
README.md                  this file
report.pdf / report.md     the report
architecture/
  views/                   component view, sequence view (real run), stage map
  decisions/               ADR-001 ... ADR-012 (Nygard format; superseded ones kept)
workflow/                  copy of .github/workflows/ and .github/autose/ (agent code, prompts, A1 skill)
experiment/
  issues/                  the 5 issue texts (with our notes: type, upstream source)
  hidden_tests/            2-4 hidden acceptance tests per issue + reference solutions
  seeded_prs/              the 5 reviewer-check PRs (diffs + labels.json ground truth)
  variants.md              what each decision-experiment variant changes
results/
  results.csv              one row per build run (stages, attempts, PR, CI, review, tokens, minutes)
  seeded_reviews.csv       one row per reviewer run on a seeded PR
  hidden_tests.csv         hidden-test results per autose PR
  runs.md                  links to every Actions run, PR and review
  runs/<run_id>/           downloaded artifacts of every run
  scripts/                 collect.py (rebuilds the tables from GitHub), build_report.py
```

## AI use

I used Claude Code (Opus 5.5) as a coding assistant for this assignment. It helped draft the workflow YAML, the
orchestrator and check code, the prompts, the collection scripts and first drafts of the ADRs and the report,
based on design decisions discussed with me. I reviewed all generated code and text, and I edited and own the
ADRs and their reasoning. All runs, PRs and results in this repository are real and linked in
`results/runs.md`.
