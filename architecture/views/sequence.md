# Sequence view: one real run, issue #5 (the vague issue), two rounds

Runs [45421953103](https://github.com/AlooKaLaddoo/markdown/actions/runs/45421953103) (round 1) and [45423178755](https://github.com/AlooKaLaddoo/markdown/actions/runs/45423178755) (round 2, dispatched by round 1's route job); PR [#14](https://github.com/AlooKaLaddoo/markdown/pull/14). Times are UTC on 2026-11-24, taken from `state.json` and the job records.

```mermaid
sequenceDiagram
    autonumber
    actor M as Maintainer
    participant GH as GitHub (issue / PR)
    participant WF as autose.yml jobs
    participant O as orchestrator.py
    participant AN as Analyst (Opus)
    participant JU as Judge (Haiku)
    participant IM as Implementer (Opus)
    participant TE as Tester (Opus)
    participant RV as Reviewer (Sonnet)
    M->>GH: 15:08:09 label autose on issue 5
    GH->>WF: issues.labeled → gate (maintainer, mode=full)
    WF->>O: build job 15:08:19 (contents:read, no GitHub token for agents)
    O->>AN: issue as untrusted data + A1 skill
    AN-->>O: spec.md (63 s)
    O->>JU: 9 acceptance criteria
    JU-->>O: AC-FR-002-03 not testable (docs prose)
    O->>AN: retry with check output
    AN-->>O: spec.md v2: Q-001 change default slugify? → ASSUMP-001 keep default
    O->>JU: re-check → all testable, check PASS 15:10:44
    O->>AN: spec.md + ARCHITECTURE.md
    AN-->>O: design.md (toc.py slugify_unicode) → AST check PASS 15:11:19
    O->>IM: spec + design
    IM-->>O: working tree change (29 s) → build check PASS
    O->>TE: spec only, clean base checkout
    TE-->>O: tests/test_autose_issue_5.py (4 of them fail on base, as expected)
    O->>O: full suite with new tests: OK → status passed 15:12:18
    WF->>GH: release job: push autose/issue-5, open PR 14, dispatch ci.yml → success (22 s)
    WF->>RV: review job 15:13:19: issue + diff + repo at PR head, read-only token
    RV-->>WF: request_changes, 2 major (emoji regression, default still gives _1)
    WF->>GH: route: post review on PR 14, state comment, gh workflow run round 2 from implementation
    GH->>WF: workflow_dispatch round 2 (15:14:24), prev artifacts downloaded
    O->>IM: spec + design + review.md
    IM-->>O: fix (67 s) → build PASS, suite OK (acceptance tests reused)
    WF->>GH: release: new commit on autose/issue-5, CI success
    WF->>RV: fresh reviewer session (no memory of round 1)
    RV-->>WF: approve, every checklist item true (ran 1188 tests + probes)
    WF->>GH: 15:18:04 post approval, state comment "a human decides"
    M->>GH: merge or close (never done by the workflow)
```

Total wall-clock: 6 min 20 s (round 1) + 3 min 41 s (round 2).
