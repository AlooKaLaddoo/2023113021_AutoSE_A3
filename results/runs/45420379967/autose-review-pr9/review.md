## AutoSE independent review: ❌ REQUEST CHANGES

Reviewer: `claude-sonnet-5-5` (variant `main`), fresh context: issue + diff + repository at `974119b34c`; no access to the spec, design, test report or implementer transcript.

**Summary.** Request changes. The `~~` pattern is registered in the core inline patterns, so strikethrough is always on, and the `strikethrough` extension does nothing. Without the extension, `markdown.markdown('~~a~~ x')` already returns `<p><del>a</del> x</p>`. The issue explicitly asks for the feature to be off unless the extension is enabled. Existing tests pass (1168 OK). Nesting, a single `~` and an unclosed `~~` behave correctly, but the default-off requirement is violated and untested. The pattern needs to move into the extension's `extendMarkdown`, with a test that it stays off by default.

**What the issue asks for** (listed before reading the diff):
- Provide a built-in extension usable as extensions=['strikethrough']
- Render ~~text~~ as <del>text</del>
- Other inline markup (bold, emphasis, links) inside still works
- A single ~ or unclosed ~~ is left alone
- Off unless the extension is enabled (default behaviour must not change)

**Checklist**

- [ ] addresses every issue point
- [x] existing tests pass
- [x] own probe done
- [ ] no regression found
- [ ] fits codebase design
- [x] no out of scope changes

**Findings**

| Severity | Location | Problem | Evidence |
|---|---|---|---|
| blocker | `markdown/inlinepatterns.py:95` | The strikethrough pattern is registered in the core build_inlinepatterns, so it is always on. The issue requires it to be off unless the extension is enabled. This changes default output for every user, and the extension is an empty no-op. It also goes against the repo's extension pattern, where optional syntax is registered in extendMarkdown. | markdown.markdown('~~a~~ x') with no extensions prints '<p><del>a</del> x</p>'. The extension's extendMarkdown body is just `pass`. |
| major | `tests/test_syntax/extensions/test_strikethrough.py:1` | The tests never check that the feature is off by default. They also don't cover a single ~, an unclosed ~~, or links and emphasis inside ~~. A test for the default-off requirement would have failed on this change. | The file has only test_basic and test_with_bold, both run with extensions=['strikethrough']. |
| minor | `markdown/extensions/strikethrough.py:1` | The docstring says the pattern lives in core so the extension 'keeps working'. That describes a design that contradicts the issue. There is also no docs or changelog entry for the new extension. | The docstring reads: 'The pattern itself is part of the core inline patterns'. |

**Commands the reviewer ran**

- `python -m unittest discover -s tests -t .  (1168 tests, OK)`
- `python /tmp/claude/p.py (probes: default vs extension output, single ~ and unclosed ~~, link and em inside ~~, ~~~~)`

Reviewer's own verdict: `request_changes`, proposed route: `design`.

**Orchestrator decision:** `request_changes` → route `design` (2 blocker/major finding(s) with evidence).

_A human maintainer decides whether to merge. The workflow never merges._
