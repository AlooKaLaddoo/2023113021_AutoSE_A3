# Spec: RecursionError on deeply nested lists takes down our server

## 1. Summary and scope

[FACT] Issue #2 reports that `markdown.markdown('- ' * 500 + 'x')` raises `RecursionError: maximum recursion depth exceeded`. The same error happens with `'1. ' * 500 + 'x'`, and with "a few hundred lines that are each indented a bit more than the previous one". The input is about 1 KB, so any user who submits a comment can crash the worker.

[FACT] The reporter's requirements: deeply nested lists "must not raise", a 500-level list does not have to render "correctly", and "normal nested lists (2-3 levels) should of course look exactly like they do today".

[GROUNDED in code] Blockquotes already have this protection. `BlockQuoteProcessor.test` returns `False` when `util.nearing_recursion_limit()` is true (`markdown/blockprocessors.py:290`). That function is defined at `markdown/util.py:177-179` and reports true when the stack is within 100 frames of `sys.getrecursionlimit()`. The test `tests/test_syntax/blocks/test_blockquotes.py:29` (`test_nesting_limit`, using `recursionlimit(120)` from `markdown.test_tools`) covers it. The list processors have no such guard:
- `OListProcessor.test` / `UListProcessor` (`markdown/blockprocessors.py:356-357`, `445-454`)
- `ListIndentProcessor.test` (`markdown/blockprocessors.py:174-179`)

Each of their `run` methods recurses through `self.parser.parseBlocks(...)` / `parseChunk(...)` (`blockprocessors.py:194-220`, `389`, `411`, `415`). The HTML serializer is iterative (`markdown/serializers.py:140-214`) and the inline tree processor uses an explicit stack (`markdown/treeprocessors.py:373-413`). So the recursion comes from block parsing.

**In scope**
- Deeply nested unordered lists, ordered lists and indented nested list items must not raise `RecursionError` from `markdown.markdown()` / `Markdown.convert()`.
- Output for lists with normal nesting depth must stay byte-for-byte the same.

**Out of scope**
- Producing a "correct" or particular HTML structure for nesting depths near the recursion limit. Only "does not raise" and "returns a string" are required.
- Recursion in other block types (blockquotes are already handled) or in inline patterns.
- Changing `sys.getrecursionlimit()` or adding a user-facing configuration option.
- Performance or time limits (the issue does not ask for any).

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Deeply nested list input does not raise RecursionError"
statement: "The system SHALL return a str (not raise RecursionError) from markdown.markdown() when the input contains unordered, ordered, or indentation-nested list items nested deeply enough to reach the interpreter's recursion limit."
epistemic_status: "FACT"
source: "Issue #2: \"markdown.markdown('- ' * 500 + 'x') ... RecursionError\"; \"Same with ordered lists ('1. ' * 500 + 'x') and with a few hundred lines that are each indented a bit more\"; \"it must not raise\". Code: markdown/blockprocessors.py:174-179, 356-416 (no recursion guard); compare markdown/blockprocessors.py:290."
actor: "Application developer rendering untrusted user Markdown (e.g. comments)"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: []
inputs:
  - {name: "source", type: "str", description: "Markdown text containing deeply nested list markers"}
outputs:
  - {name: "html", type: "str", description: "Rendered HTML; structure beyond the recursion-safe depth is unspecified"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Deeply nested unordered list markers on one line"
    given: "Default recursion limit (sys.getrecursionlimit() unchanged, normally 1000) and source = '- ' * 500 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str and starts with '<ul>'; the character 'x' appears in it"
  - id: "AC-FR-001-02"
    scenario: "Deeply nested ordered list markers on one line"
    given: "Default recursion limit and source = '1. ' * 500 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str and starts with '<ol>'; the character 'x' appears in it"
  - id: "AC-FR-001-03"
    scenario: "Many lines, each indented one level (4 spaces) more than the previous"
    given: "Default recursion limit and source = '\\n'.join(' ' * (4 * i) + '- x' for i in range(300))"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised and the return value is an instance of str that starts with '<ul>'"
  - id: "AC-FR-001-04"
    scenario: "Mixed deep nesting of '- ' and '1. ' markers"
    given: "Default recursion limit and source = '- 1. ' * 250 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised and the return value is an instance of str"
  - id: "AC-FR-001-05"
    scenario: "Guard applies relative to a lowered recursion limit, like the blockquote guard"
    given: "Within markdown.test_tools.recursionlimit(150) and source = '- ' * 100 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised and the return value is an instance of str"
  - id: "AC-FR-001-06"
    scenario: "Converter remains usable after a deep input"
    given: "A single markdown.Markdown() instance md that has just converted '- ' * 500 + 'x'"
    when: "md.reset(); md.convert('- a\\n- b') is called"
    then: "The result equals '<ul>\\n<li>a</li>\\n<li>b</li>\\n</ul>'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Normal list nesting renders exactly as before"
statement: "The system SHALL produce output for lists nested at depths well below the recursion limit that is identical to the output produced before this change."
epistemic_status: "FACT"
source: "Issue #2: \"Normal nested lists (2-3 levels) should of course look exactly like they do today.\" Existing tests: tests/test_syntax/blocks/test_ul.py, tests/test_syntax/blocks/test_blockquotes.py:29."
actor: "Application developer / end users reading rendered Markdown"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: ["FR-001"]
inputs:
  - {name: "source", type: "str", description: "Markdown with 1-3 levels of list nesting"}
outputs:
  - {name: "html", type: "str", description: "Unchanged HTML output"}
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Three-level nested unordered list via indentation"
    given: "source = '- a\\n    - b\\n        - c'"
    when: "markdown.markdown(source) is called"
    then: "The result equals '<ul>\\n<li>a<ul>\\n<li>b<ul>\\n<li>c</li>\\n</ul>\\n</li>\\n</ul>\\n</li>\\n</ul>'"
  - id: "AC-FR-002-02"
    scenario: "Nested ordered list inside unordered list"
    given: "source = '- a\\n    1. b\\n    2. c'"
    when: "markdown.markdown(source) is called"
    then: "The result equals '<ul>\\n<li>a<ol>\\n<li>b</li>\\n<li>c</li>\\n</ol>\\n</li>\\n</ul>'"
  - id: "AC-FR-002-03"
    scenario: "Shallow same-line nested markers"
    given: "source = '- - - x'"
    when: "markdown.markdown(source) is called"
    then: "The result equals '<ul>\\n<li>\\n<ul>\\n<li>\\n<ul>\\n<li>x</li>\\n</ul>\\n</li>\\n</ul>\\n</li>\\n</ul>'"
  - id: "AC-FR-002-04"
    scenario: "Existing test suite unchanged"
    given: "The repository test suite, including tests/test_syntax/blocks/test_ul.py and tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit"
    when: "python -m unittest discover -s tests -t . is run"
    then: "All previously passing tests still pass with no change to their expected output"
verification_method: "TEST"
```

## 3. Non-functional requirements

```yaml
id: "NFR-001"
category: "RELIABILITY"
title: "Small hostile list input does not crash the converter"
statement: "The system SHALL complete markdown.markdown() without raising any exception for list-nesting inputs of up to 1 KB, at the default recursion limit."
target_metric:
  metric_name: "Unhandled exceptions raised by markdown.markdown()"
  target_value: "0 exceptions for each input in AC-FR-001-01, AC-FR-001-02 and AC-FR-001-04 (each <= 1500 bytes)"
  measurement_condition: "CPython, sys.getrecursionlimit() at its default value, run with the repository unittest suite"
epistemic_status: "FACT"
readiness_status: "READY_FOR_DEV"
verification_method: "TEST"
```

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: The rendered HTML for nesting beyond the safe depth is unspecified. For example, the remaining markers may be emitted as literal paragraph text instead of further nested lists, matching how blockquotes degrade past `nearing_recursion_limit()`. Rationale: the reporter says "I don't care if a 500-level list renders 'correctly'". Impact if invalid: LOW. Validation path: maintainer review (Q-001).
- **ASSUMP-002** [INFERRED]: "Each indented a bit more than the previous one" means each line is indented one `tab_length` (4 spaces) more than the previous one. AC-FR-001-03 uses 300 such lines. Impact if invalid: MEDIUM, because a different indentation step could take a different code path (e.g. lazy continuation or code blocks). Validation path: Q-002.
- **ASSUMP-003** [INFERRED]: Tests run at the default recursion limit, or at a limit lowered through `markdown.test_tools.recursionlimit`. The guard should be relative to the current recursion limit, like `util.nearing_recursion_limit()`, and not a fixed depth constant. Impact if invalid: LOW.
- **Q-001**: How should list content past the safe nesting depth render?
  - Option A: stop nesting and render the remainder as text in the deepest item or a paragraph.
  - Option B: drop the excess content.
  - Recommended default: A, because it loses no user content and matches the blockquote behaviour.
  - Affects: FR-001 (PROVISIONAL).
- **Q-002**: What exact indentation pattern does the third reported reproduction use?
  - Recommended default: 4 additional spaces per line (ASSUMP-002).
  - Affects: AC-FR-001-03.
- **Risk note**: The issue text contains no instructions aimed at the pipeline, so no prompt-injection attempt was found.

## 5. Validation

1. **Completeness**: PASS. Both FRs have an actor, inputs, outputs, and normal plus edge/error acceptance criteria.
2. **Testability**: PASS. Every criterion uses exact input strings and checks either exact output or no exception plus `isinstance(str)`. The NFR has a numeric target (0 exceptions, inputs of 1500 bytes or less).
3. **Consistency**: PASS. FR-001 applies only near the recursion limit and FR-002 only to shallow depths, so they do not conflict.
4. **Feasibility**: PASS. The blockquote guard (`markdown/blockprocessors.py:290`) already shows this approach works in the codebase.
5. **Traceability**: PASS. Every FR and NFR cites the issue text and the code locations, and the provisional parts trace to ASSUMP-001/002 and Q-001/002.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Gives a concrete input, a single call, and checkable outcomes (no exception, return type str, prefix '<ul>', contains 'x') under a fixed recursion limit.)
- AC-FR-001-02: testable=True (Gives a concrete input, a single call, and checkable outcomes (no exception, return type str, prefix '<ol>', contains 'x') under a fixed recursion limit.)
- AC-FR-001-03: testable=True (Gives a concrete generated input and checkable outcomes (no exception, return type str, prefix '<ul>') with a fixed default recursion limit.)
- AC-FR-001-04: testable=True (Gives a concrete input and checkable outcomes (no exception, return type str), though the assertion is weak, it is still a clear pass/fail.)
- AC-FR-001-05: testable=True (Specifies the recursion limit via markdown.test_tools.recursionlimit(150), a concrete input, and checkable outcomes (no exception, return type str).)
- AC-FR-001-06: testable=True (After a reset on a used instance, the exact expected output string for the given input is specified, allowing an exact equality assertion.)
- AC-FR-002-01: testable=True (Provides a concrete nested-list input and the exact expected HTML string, allowing an equality assertion.)
- AC-FR-002-02: testable=True (Provides a concrete mixed unordered/ordered nested input and the exact expected HTML string, allowing an equality assertion.)
- AC-FR-002-03: testable=True (Provides a concrete input '- - - x' and the exact expected nested HTML string, allowing an equality assertion.)
- AC-FR-002-04: testable=True (Names a concrete command and a binary outcome (all previously passing tests still pass with unchanged expectations), checkable by running the suite against a recorded baseline.)
