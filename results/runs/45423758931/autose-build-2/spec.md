# Spec: RecursionError on deeply nested lists takes down our server

## 1. Summary and scope

Calling `markdown.markdown()` on short input made of many nested list markers raises `RecursionError`. The issue gives about 1 KB inputs such as `'- ' * 500 + 'x'`. Any user who can submit Markdown can trigger the error, so it works as a denial-of-service against servers that render untrusted input. [FACT]

Code evidence (current behaviour):
- `markdown/blockprocessors.py` `OListProcessor.run` (lines 359-416, shared with `UListProcessor`) calls `self.parser.parseBlocks(li, [item])` for each item. `ListIndentProcessor.run` (lines 181-215) calls `parseBlocks`/`parseChunk` for each indented child block. Neither has a depth guard, so each nesting level adds Python stack frames. [FACT]
- `BlockQuoteProcessor.test` (line 290) already returns `False` when `util.nearing_recursion_limit()` is true. That function (`markdown/util.py` line 177) is true when the stack is within 100 frames of `sys.getrecursionlimit()`. The test `tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit` covers this. This confirms the issue's statement that "blockquotes already have some protection". [FACT]

**In scope**
- Deeply nested unordered lists (`- `, `* `, `+ ` markers) and ordered lists (`1. `) must not raise.
- Many lines where each line is indented further than the one before must not raise.
- Shallow nested lists (2-3 levels) must render exactly as they do today.

**Out of scope**
- Making lists nested beyond the safe depth render "correctly". The issue says: "I don't care if a 500-level list renders 'correctly'".
- Changing the existing blockquote nesting limit.
- Other nesting constructs that the issue does not mention (for example, extension blocks).
- Performance or time limits (the issue does not ask for any).

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Render deeply nested inline list markers without raising"
statement: "The system SHALL return a string, and SHALL NOT raise RecursionError or any other exception, when markdown.markdown() is given a single line made of many repeated unordered or ordered list markers followed by text."
epistemic_status: "FACT"
source: "Issue #2: \"markdown.markdown('- ' * 500 + 'x') ... RecursionError\"; \"Same with ordered lists ('1. ' * 500 + 'x')\"; \"it must not raise\". Code: markdown/blockprocessors.py OListProcessor.run lines 405-416 (unbounded recursive parseBlocks)."
actor: "Application rendering untrusted user Markdown (e.g. comment rendering server)"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-002"]
inputs: [{name: "source", type: "str", description: "Markdown text with N repeated list markers on one line, followed by 'x'"}]
outputs: [{name: "html", type: "str", description: "Rendered HTML; exact structure beyond the safe depth is not specified"}]
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "500 nested unordered list markers (issue reproduction)"
    given: "The default Python recursion limit (sys.getrecursionlimit() unchanged, 1000 in CPython) and source = '- ' * 500 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str; the return value starts with '<ul>' and contains the character 'x'"
  - id: "AC-FR-001-02"
    scenario: "500 nested ordered list markers (issue reproduction)"
    given: "The default Python recursion limit and source = '1. ' * 500 + 'x'"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str; the return value starts with '<ol>' and contains the character 'x'"
  - id: "AC-FR-001-03"
    scenario: "Edge case: ten times the reported depth"
    given: "The default Python recursion limit and source = '- ' * 5000 + 'x' (10 KB)"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str and contains the character 'x'"
  - id: "AC-FR-001-04"
    scenario: "Edge case: other unordered markers"
    given: "The default Python recursion limit and source = '* ' * 500 + 'x', and separately source = '+ ' * 500 + 'x'"
    when: "markdown.markdown(source) is called for each source"
    then: "No exception is raised in either call; each return value is an instance of str and contains the character 'x'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Render many progressively indented list lines without raising"
statement: "The system SHALL return a string, and SHALL NOT raise RecursionError or any other exception, when markdown.markdown() is given a few hundred list-item lines where each line is indented further than the previous one."
epistemic_status: "FACT"
source: "Issue #2: \"and with a few hundred lines that are each indented a bit more than the previous one\". Code: markdown/blockprocessors.py ListIndentProcessor.run lines 181-215 and OListProcessor.run line 411 (recursive parseBlocks for indented items)."
actor: "Application rendering untrusted user Markdown"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-003"]
inputs: [{name: "source", type: "str", description: "N lines, line i is (4*i) spaces + '- x'"}]
outputs: [{name: "html", type: "str", description: "Rendered HTML; exact structure beyond the safe depth is not specified"}]
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "300 unordered list lines, each indented 4 spaces more than the previous"
    given: "The default Python recursion limit and source = '\\n'.join(' ' * (4 * i) + '- x' for i in range(300))"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str and starts with '<ul>'"
  - id: "AC-FR-002-02"
    scenario: "Ordered variant, with blank lines between items (loose-list path through ListIndentProcessor)"
    given: "The default Python recursion limit and source = '\\n\\n'.join(' ' * (4 * i) + '1. x' for i in range(300))"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str and starts with '<ol>'"
  - id: "AC-FR-002-03"
    scenario: "Edge case: indentation grows by 1 space per line"
    given: "The default Python recursion limit and source = '\\n'.join(' ' * i + '- x' for i in range(300))"
    when: "markdown.markdown(source) is called"
    then: "No exception is raised; the return value is an instance of str"
verification_method: "TEST"
```

```yaml
id: "FR-003"
title: "Keep rendering of shallow nested lists unchanged"
statement: "The system SHALL render nested lists of 3 or fewer levels to exactly the same HTML as before the change."
epistemic_status: "FACT"
source: "Issue #2: \"Normal nested lists (2-3 levels) should of course look exactly like they do today.\" Expected strings taken from existing fixture tests/basic/ordered-and-unordered-list.html lines 110-146 (input tests/basic/ordered-and-unordered-list.txt lines 100-120; tabs there are expanded to 4 spaces with the default tab_length=4)."
actor: "Any existing Python-Markdown user"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: []
inputs: [{name: "source", type: "str", description: "Markdown with 2-3 levels of list nesting"}]
outputs: [{name: "html", type: "str", description: "HTML identical to the literal strings below"}]
acceptance_criteria:
  - id: "AC-FR-003-01"
    scenario: "Three-level tight unordered list"
    given: "source = '* Tab\\n    * Tab\\n        * Tab'"
    when: "markdown.markdown(source) is called"
    then: "The return value equals exactly '<ul>\\n<li>Tab<ul>\\n<li>Tab<ul>\\n<li>Tab</li>\\n</ul>\\n</li>\\n</ul>\\n</li>\\n</ul>'"
  - id: "AC-FR-003-02"
    scenario: "Ordered list with a nested unordered list (two levels, tight)"
    given: "source = '1. First\\n2. Second:\\n    * Fee\\n    * Fie\\n    * Foe\\n3. Third'"
    when: "markdown.markdown(source) is called"
    then: "The return value equals exactly '<ol>\\n<li>First</li>\\n<li>Second:<ul>\\n<li>Fee</li>\\n<li>Fie</li>\\n<li>Foe</li>\\n</ul>\\n</li>\\n<li>Third</li>\\n</ol>'"
  - id: "AC-FR-003-03"
    scenario: "Loose ordered list with nested unordered list (paragraph wrapping path)"
    given: "source = '1. First\\n\\n2. Second:\\n    * Fee\\n    * Fie\\n    * Foe\\n\\n3. Third'"
    when: "markdown.markdown(source) is called"
    then: "The return value equals exactly '<ol>\\n<li>\\n<p>First</p>\\n</li>\\n<li>\\n<p>Second:</p>\\n<ul>\\n<li>Fee</li>\\n<li>Fie</li>\\n<li>Foe</li>\\n</ul>\\n</li>\\n<li>\\n<p>Third</p>\\n</li>\\n</ol>'"
  - id: "AC-FR-003-04"
    scenario: "Existing regression suite and blockquote nesting limit unchanged"
    given: "The repository test suite, including tests/basic/ordered-and-unordered-list.txt/.html and tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit, with their expected files unmodified"
    when: "python -m unittest discover -s tests -t . is run"
    then: "All of these tests pass without any changes to their expected-output files"
verification_method: "TEST"
```

## 3. Non-functional requirements

```yaml
id: "NFR-001"
category: "RELIABILITY"
title: "No exception on small hostile list input"
statement: "The system SHALL complete markdown.markdown() without raising any exception for every list-nesting input of up to 10 KB covered by FR-001 and FR-002."
target_metric:
  metric_name: "Exceptions raised per call"
  target_value: "0 exceptions for inputs <= 10 KB (10240 characters) of the forms in AC-FR-001-01..04 and AC-FR-002-01..03"
  measurement_condition: "CPython >= 3.9 (the project's supported versions), default sys.getrecursionlimit(), default extensions, single-threaded unittest run"
epistemic_status: "FACT"
readiness_status: "PROVISIONAL"
verification_method: "TEST"
```

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: List items nested past a safe depth may render differently from "infinite" nesting. For example, the remaining markers may appear as literal paragraph text. Acceptance only requires that no exception is raised, that the output is a `str`, and that the text `x` is kept where stated. *Rationale:* the issue explicitly does not care how a 500-level list renders. *Impact if invalid:* LOW. Only the looseness of the checks in FR-001 and FR-002 is affected. *Validation path:* Q-001.
- **ASSUMP-002** [INFERRED]: The safe depth should follow the existing blockquote approach, which stops nesting when the stack is near `sys.getrecursionlimit()` (`util.nearing_recursion_limit()`). A fixed numeric cap is not assumed. *Rationale:* consistency with `BlockQuoteProcessor.test` (`markdown/blockprocessors.py:290`). *Impact if invalid:* MEDIUM. A fixed cap would need its own value and its own tests. *Validation path:* Q-002.
- **ASSUMP-003** [INFERRED]: The issue's "a few hundred lines that are each indented a bit more than the previous one" is represented by the 300-line inputs in AC-FR-002-01..03 (4-space and 1-space steps). *Impact if invalid:* LOW. Other indentation patterns can be added as extra test cases.
- **ASSUMP-004** [INFERRED]: The expected strings in FR-003 are copied from the committed fixture `tests/basic/ordered-and-unordered-list.html`. Those inputs use tabs, and the FR-003 inputs use 4 spaces instead; this is assumed to give identical output with the default `tab_length=4`. *Impact if invalid:* LOW. In that case, use the fixture's exact tab-indented input.
- **Q-001**: What should a list nested beyond the safe depth render as? Options: (a) unspecified fallback, only no exception required; (b) the remaining markers as literal text in the deepest `<li>`; (c) cut off silently. **Recommended default:** (a). This affects FR-001 and FR-002 (PROVISIONAL).
- **Q-002**: Should the depth limit depend on the recursion limit (like blockquotes) or be a fixed, documented number of levels? **Recommended default:** depend on the recursion limit, for consistency with the blockquote approach. This affects FR-001, FR-002 and NFR-001 (PROVISIONAL).
- **RISK-001**: The issue text contained no instructions aimed at the agent, so no prompt-injection attempt was detected.

## 5. Validation

1. **Completeness:** PASS. Each FR has an actor, inputs, outputs, and normal plus edge-case criteria, and FR-003 covers unchanged behaviour.
2. **Testability:** PASS. Every criterion gives an exact Python input and either an exact expected string or a checkable property (no exception, `str` type, prefix or substring). The NFR has a numeric threshold of 0 exceptions for inputs of 10 KB or less.
3. **Consistency:** PASS. The relaxed rendering rule for deep nesting (FR-001, FR-002) applies only beyond the safe depth. It does not conflict with the exact output required for 3 or fewer levels (FR-003).
4. **Feasibility:** PASS. A similar guard already exists for blockquotes (`markdown/util.py:177`, `markdown/blockprocessors.py:290`).
5. **Traceability:** PASS. Every requirement cites an issue quote and the relevant file and line numbers. Provisional items link to ASSUMP-001..004 and Q-001..002.


---
## Stage 1 check (orchestrator, attempt 2)

Result: **PASS**

- AC-FR-001-01: testable=True (Concrete input, default recursion limit, and observable outcomes (no exception, return type str, prefix '<ul>', contains 'x') give an unambiguous pass/fail.)
- AC-FR-001-02: testable=True (Concrete input and observable outcomes (no exception, str type, prefix '<ol>', contains 'x') give an unambiguous pass/fail.)
- AC-FR-001-03: testable=True (Concrete 10 KB input with observable outcomes (no exception, str type, contains 'x') gives an unambiguous pass/fail.)
- AC-FR-001-04: testable=True (Two concrete inputs ('* ' and '+ ' repeated 500 times) with observable outcomes (no exception, str type, contains 'x') are directly assertable.)
- AC-FR-002-01: testable=True (Concrete generated nested-list input with observable outcomes (no exception, str type, prefix '<ul>') is assertable.)
- AC-FR-002-02: testable=True (Concrete generated nested ordered-list input with observable outcomes (no exception, str type, prefix '<ol>') is assertable.)
- AC-FR-002-03: testable=True (Concrete generated input with the observable outcome of no exception and a str return type is assertable.)
- AC-FR-003-01: testable=True (Concrete input and an exact expected output string allow a precise equality assertion.)
- AC-FR-003-02: testable=True (Concrete input and an exact expected output string allow a precise equality assertion.)
- AC-FR-003-03: testable=True (Concrete input and an exact expected output string (including <p> wrapping for loose lists) allow a precise equality assertion.)
- AC-FR-003-04: testable=True (The command and named tests give a clear exit-status pass/fail, though it is a suite-level regression check rather than a pure unit test, and verifying the expected files are unmodified requires a separate git diff check.)
