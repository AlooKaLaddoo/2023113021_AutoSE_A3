# Decision-experiment variants

Both experiments use the same workflow code. The variant is chosen with the `variant` input of
`workflow_dispatch` (or `variant=<name>` in a `/autose` comment) and is defined in
`.github/autose/config.json` → `variants`. Everything not listed below is identical to `main`.

## E1: reviewer independence (tests ADR-006 and ADR-008)

**Question.** Does our reviewer design catch more defects than a "friendly" reviewer that uses the same model as the
builder and reads the author's description?

| | `main` (our design) | `e1_friendly_reviewer` (baseline) |
|---|---|---|
| Model | `claude-sonnet-5-5` (differs from the builder) | `claude-opus-5-5` (same as the builder) |
| Prompt | `prompts/reviewer.md`: issue first, mandatory suite run and own probes, evidence per finding, explicit prior that automated changes are often wrong | `prompts/reviewer_friendly.md`: "read the issue, the PR description and the diff and decide" |
| Sees the PR description (author's claims) | no | yes |
| Tools, permissions, job, JSON schema, orchestrator validation | same | same |

**Material.** The five seeded PRs #6-#10 (`experiment/seeded_prs/`, ground truth in `labels.json`, written before any
reviewer run): one correct fix and four with known defects (incomplete fix, wrong href, wrong layer, weakened test
plus prompt injection).

**Metric.** Correct final decision (approve vs. request_changes) per PR; correct route; whether the reviewer ran its
own probes; tokens.

## E2: who writes the acceptance tests (tests ADR-001 and ADR-003)

**Question.** Does a separate Tester that writes the acceptance tests from `spec.md` only, without seeing the
implementation, produce better PRs than letting the Implementer write its own acceptance tests?

| | `main` (our design) | `e2_implementer_writes_tests` |
|---|---|---|
| Who writes `tests/test_autose_issue_N.py` | Tester agent, clean checkout of the base commit, spec only | the Implementer, in the same session that writes the code |
| Tester agent | runs | skipped |
| Everything else (spec, design, checks, retries, release, review) | same | same |

**Material.** The same issues, run once per variant.

**Metric.** Hidden acceptance tests passed (`experiment/hidden_tests/`), new acceptance tests that fail on the base
commit (do the tests detect the change at all?), implementation attempts, reviewer outcome, tokens.
