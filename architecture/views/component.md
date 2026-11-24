# Component view

The workflow runs in the fork `AlooKaLaddoo/markdown` (Python-Markdown pinned at `3f2c551`). One GitHub Actions workflow (`.github/workflows/autose.yml`) contains five jobs. Agents are headless Claude Code sessions (`claude -p`). Each session is started by a deterministic Python orchestrator (`.github/autose/orchestrator.py`) with its own system prompt, its own tool list and its own model. No agent ever holds a GitHub token. Only deterministic steps talk to GitHub.

```mermaid
flowchart TB
    subgraph GH["GitHub (fork AlooKaLaddoo/markdown)"]
        ISSUE["Issue + label 'autose'<br/>or '/autose' comment"]
        PR["Pull request<br/>autose/issue-N"]
        CI["ci.yml<br/>(unittest suite)"]
        STATE["State comment on issue<br/>&lt;!-- autose-state --&gt;"]
        ART["Workflow artifacts<br/>spec.md, design.md, diff.patch,<br/>test_report.md, pr.md, review.md,<br/>transcripts"]
    end

    subgraph WF["autose.yml"]
        GATE["gate job<br/>who / what / which mode<br/>perms: none"]
        BUILD["build job<br/>stages 1-4<br/>perms: contents:read, issues:read, actions:read"]
        REL["release job<br/>stage 5 (no LLM)<br/>perms: contents:write, pull-requests:write, actions:write"]
        REV["review job<br/>stage 6<br/>perms: contents:read, issues:read, pull-requests:read"]
        ROUTE["route job<br/>post review, decide loop-back<br/>perms: pull-requests:write, issues:write, actions:write"]
    end

    subgraph ORCH["orchestrator.py (deterministic state machine)"]
        CHECKS["checks.py<br/>spec / design / build / tests"]
    end

    subgraph AGENTS["Agents (claude -p, CLAUDE_CODE_SUBPROCESS_ENV_SCRUB=1)"]
        AN["Analyst - Opus 5.5<br/>tools: Read, Grep, Glob<br/>stages 1 + 2<br/>(A1 skill + ARCHITECTURE.md)"]
        IM["Implementer - Opus 5.5<br/>tools: Read, Grep, Glob, Edit, Write,<br/>Bash(python -m unittest / compileall / python -c)<br/>stage 3"]
        TE["Tester - Opus 5.5<br/>tools: Read, Grep, Glob, Edit, Write,<br/>Bash(python -m unittest / python -c)<br/>stage 4, clean checkout, spec only"]
        RV["Reviewer - Sonnet 5.5<br/>tools: Read, Grep, Glob, Write,<br/>Bash(python / git diff)<br/>stage 6, structured verdict"]
        JU["Spec judge - Haiku 5.5<br/>no tools<br/>testability check"]
    end

    ISSUE -->|issues.labeled / issue_comment| GATE
    GATE --> BUILD --> REL --> REV --> ROUTE
    BUILD --- ORCH
    ORCH -->|spec / design prompt| AN
    ORCH -->|spec + design + failures| IM
    ORCH -->|spec only| TE
    ORCH -->|ACs| JU
    REV -->|issue + diff + repo at PR head| RV
    BUILD -->|upload| ART
    REL -->|git push with GITHUB_TOKEN,<br/>gh pr create| PR
    REL -->|gh workflow run ci.yml --ref branch| CI
    ROUTE -->|gh pr review --comment| PR
    ROUTE -->|update| STATE
    ROUTE -->|gh workflow run autose.yml<br/>round+1, from_stage| WF
```

## What each component may do

| Component | Model | Tools / permissions | Can push? | Sees |
|---|---|---|---|---|
| gate job | none | none (`permissions: {}`) | no | event payload |
| Analyst (stages 1, 2) | `claude-opus-5-5` | Read, Grep, Glob | no | issue (as untrusted data), repo, `ARCHITECTURE.md`, A1 skill; on loop-back: `review.md` or failing test summary |
| Spec judge | `claude-haiku-5-5` | none | no | acceptance criteria only |
| Implementer (stage 3) | `claude-opus-5-5` | Read, Grep, Glob, Edit, Write, `Bash(python -m unittest:*)`, `Bash(python -m compileall:*)`, `Bash(python -c:*)` | no | `spec.md`, `design.md`, repo; on retry: failing test output; on loop-back: `review.md` |
| Tester (stage 4) | `claude-opus-5-5` | Read, Grep, Glob, Edit, Write, `Bash(python -m unittest:*)`, `Bash(python -c:*)` | no | `spec.md` and a clean checkout of the base commit only |
| orchestrator + checks | none | runs tests, compiles, parses artifacts; runs agent-written code outside the sandbox, without credentials since PR #21 | no | everything (it is code) |
| release job | none | `contents: write`, `pull-requests: write`, `actions: write` | yes (only `autose/*` branches) | artifacts from build |
| Reviewer (stage 6) | `claude-sonnet-5-5` | Read, Grep, Glob, Write, `Bash(python:*)`, `Bash(git diff:*)` | no (no token, `persist-credentials: false`) | issue, diff, repo at PR head commit |
| route job | none | `pull-requests: write`, `issues: write`, `actions: write` | no | `verdict.json` |
| human maintainer | - | merge button | yes | everything |
