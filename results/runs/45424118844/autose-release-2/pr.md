Closes #2

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45424118844)._

### Requirements (from spec.md)

- **FR-001** Deeply nested list input does not raise RecursionError: The system SHALL return a str (not raise RecursionError) from markdown.markdown() when the input contains unordered, ordered, or indentation-nested list items nested deeply enough to reach the interpreter's recursion limit.
  - `AC-FR-001-01` given Default recursion limit (sys.getrecursionlimit() unchanged, normally 1000) and source = '- ' * 500 + 'x', when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str and starts with '<ul>'; the character 'x' appears in it
  - `AC-FR-001-02` given Default recursion limit and source = '1. ' * 500 + 'x', when markdown.markdown(source) is called, then No exception is raised; the return value is an instance of str and starts with '<ol>'; the character 'x' appears in it
  - `AC-FR-001-03` given Default recursion limit and source = '\n'.join(' ' * (4 * i) + '- x' for i in range(300)), when markdown.markdown(source) is called, then No exception is raised and the return value is an instance of str that starts with '<ul>'
  - `AC-FR-001-04` given Default recursion limit and source = '- 1. ' * 250 + 'x', when markdown.markdown(source) is called, then No exception is raised and the return value is an instance of str
  - `AC-FR-001-05` given Within markdown.test_tools.recursionlimit(150) and source = '- ' * 100 + 'x', when markdown.markdown(source) is called, then No exception is raised and the return value is an instance of str
  - `AC-FR-001-06` given A single markdown.Markdown() instance md that has just converted '- ' * 500 + 'x', when md.reset(); md.convert('- a\n- b') is called, then The result equals '<ul>\n<li>a</li>\n<li>b</li>\n</ul>'
- **FR-002** Normal list nesting renders exactly as before: The system SHALL produce output for lists nested at depths well below the recursion limit that is identical to the output produced before this change.
  - `AC-FR-002-01` given source = '- a\n    - b\n        - c', when markdown.markdown(source) is called, then The result equals '<ul>\n<li>a<ul>\n<li>b<ul>\n<li>c</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>'
  - `AC-FR-002-02` given source = '- a\n    1. b\n    2. c', when markdown.markdown(source) is called, then The result equals '<ul>\n<li>a<ol>\n<li>b</li>\n<li>c</li>\n</ol>\n</li>\n</ul>'
  - `AC-FR-002-03` given source = '- - - x', when markdown.markdown(source) is called, then The result equals '<ul>\n<li>\n<ul>\n<li>\n<ul>\n<li>x</li>\n</ul>\n</li>\n</ul>\n</li>\n</ul>'
  - `AC-FR-002-04` given The repository test suite, including tests/test_syntax/blocks/test_ul.py and tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit, when python -m unittest discover -s tests -t . is run, then All previously passing tests still pass with no change to their expected output

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/blockprocessors.py` | `OListProcessor.test` | modify: return `bool(self.RE.match(block)) and not util.nearing_recursion_limit()`. `UListProcessor` inherits this. |
| `markdown/blockprocessors.py` | `ListIndentProcessor.test` | modify: add `and not util.nearing_recursion_limit()` to the existing boolean expression, keeping the current conditions and their order. |
| `tests/test_syntax/blocks/test_ul.py` | `(new) TestListNestingLimit` | new: `markdown.test_tools.TestCase` subclass with one test per AC: deep `'- '*500+'x'`, deep `'1. '*500+'x'`, 300 lines indented 4 more spaces each, `'- 1. '*250+'x'`, `'- '*100+'x'` under `recursionlimit(150)`, reuse after `md.reset()`, and exact-output checks for the three shallow FR-002 inputs. |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1176 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/18
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-2-e2_implementer_writes_tests`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45424800212
- Result: **PASS** 
