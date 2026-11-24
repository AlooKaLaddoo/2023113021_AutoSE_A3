Closes #2

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45421936778)._

### Requirements (from spec.md)

- **FR-001** Render deeply nested inline list markers without raising: The system SHALL return a string, and SHALL NOT raise RecursionError or any other exception, when markdown.markdown() is given a single line made of many repeated unordered or ordered list markers followed by text.
  - `AC-FR-001-01` given The default Python recursion limit (sys.getrecursionlimit() unchanged, 1000 in CPython) and source = '- ' * 500 + 'x', when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str; the return value starts with '<ul>' and contains the character 'x'
  - `AC-FR-001-02` given The default Python recursion limit and source = '1. ' * 500 + 'x', when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str; the return value starts with '<ol>' and contains the character 'x'
  - `AC-FR-001-03` given The default Python recursion limit and source = '- ' * 5000 + 'x' (10 KB), when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str and contains the character 'x'
  - `AC-FR-001-04` given The default Python recursion limit and source = '* ' * 500 + 'x', and separately source = '+ ' * 500 + 'x', when markdown.markdown(source) is called for each source, then No exception is raised in either call; each return value is an instance of str and contains the character 'x'
- **FR-002** Render many progressively indented list lines without raising: The system SHALL return a string, and SHALL NOT raise RecursionError or any other exception, when markdown.markdown() is given a few hundred list-item lines where each line is indented further than the previous one.
  - `AC-FR-002-01` given The default Python recursion limit and source = '\n'.join(' ' * (4 * i) + '- x' for i in range(300)), when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str and starts with '<ul>'
  - `AC-FR-002-02` given The default Python recursion limit and source = '\n\n'.join(' ' * (4 * i) + '1. x' for i in range(300)), when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str and starts with '<ol>'
  - `AC-FR-002-03` given The default Python recursion limit and source = '\n'.join(' ' * i + '- x' for i in range(300)), when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str
- **FR-003** Keep rendering of shallow nested lists unchanged: The system SHALL render nested lists of 3 or fewer levels to exactly the same HTML as before the change.
  - `AC-FR-003-01` given source = '* Tab\n    * Tab\n        * Tab', when markdown.markdown(source) is called, then The return value equals exactly '<ul>\n<li>Tab<ul>\n<li>Tab<ul>\n<li>Tab</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>'
  - `AC-FR-003-02` given source = '1. First\n2. Second:\n    * Fee\n    * Fie\n    * Foe\n3. Third', when markdown.markdown(source) is called, then The return value equals exactly '<ol>\n<li>First</li>\n<li>Second:<ul>\n<li>Fee</li>\n<li>Fie</li>\n<li>Foe</li>\n</ul>\n</li>\n<li>Third</li>\n</ol>'
  - `AC-FR-003-03` given source = '1. First\n\n2. Second:\n    * Fee\n    * Fie\n    * Foe\n\n3. Third', when markdown.markdown(source) is called, then The return value equals exactly '<ol>\n<li>\n<p>First</p>\n</li>\n<li>\n<p>Second:</p>\n<ul>\n<li>Fee</li>\n<li>Fie</li>\n<li>Foe</li>\n</ul>\n</li>\n<li>\n<p>Third</p>\n</li>\n</ol>'
  - `AC-FR-003-04` given The repository test suite, including tests/basic/ordered-and-unordered-list.txt/.html and tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit, with their expected files unmodified, when python -m unittest discover -s tests -t . is run, then All of these tests pass without any changes to their expected-output files

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/blockprocessors.py` | `OListProcessor.test` | modify: return `bool(self.RE.match(block)) and not util.nearing_recursion_limit()`. `UListProcessor` inherits it, so `-`, `*`, `+` and `1.` are all covered. |
| `markdown/blockprocessors.py` | `ListIndentProcessor.test` | modify: append `and not util.nearing_recursion_limit()` as the last condition, so indented blocks near the limit fall through to the non-recursive `CodeBlockProcessor`. |
| `tests/test_syntax/blocks/test_ul.py` | `(new) TestListNestingLimit` | add: a `markdown.test_tools.TestCase` subclass with tests for AC-FR-001-01..04 (`'- '`, `'1. '`, `'* '`, `'+ '` × 500, and `'- '` × 5000, each followed by `'x'`). Each asserts that no exception is raised, the result is a `str`, the expected `<ul>`/`<ol>` prefix is present, and `'x'` is in the output. Also tests for AC-FR-002-01..03 (300 lines with 4-space steps, the loose `1. x` variant with blank lines, 1-space steps). It also asserts the exact HTML for AC-FR-003-01..03. Like `test_nesting_limit`, it also checks one small case under `recursionlimit(...)` from `markdown.test_tools`: a list nested deeper than the lowered limit allows must render without raising. |
| `docs/changelog.md` | `-` | add: an "Unreleased" bug-fix entry saying that deeply nested lists no longer raise `RecursionError`, and that nesting stops near the recursion limit as it already does for blockquotes. (Only if the file exists in its usual form; if not, skip this row.) |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1189 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/15
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-2`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45423195661
- Result: **PASS** 
