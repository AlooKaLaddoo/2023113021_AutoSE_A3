# Spec: Support ~~strikethrough~~ like GitHub

## 1. Summary and scope

Python-Markdown currently prints `~~text~~` as literal text. In the core inline registry (`markdown/inlinepatterns.py:54-93`) nothing handles `~`, and `~` is not in `Markdown.ESCAPED_CHARS` (`markdown/core.py:112-114`). The issue asks for a built-in, opt-in extension called `strikethrough` that turns `~~text~~` into `<del>text</del>`, as GitHub does.

**In scope**
- A new built-in extension that loads with `markdown.markdown(text, extensions=['strikethrough'])`. Built-in extensions get their short names from entry points in `pyproject.toml:73-91`, which `Markdown.build_extension` resolves through `util.get_installed_extensions()` (`markdown/core.py:218-221`, `markdown/util.py:104-108`).
- Turning a matched pair of `~~` delimiters into a `<del>` element.
- Bold, emphasis and links inside the struck-through text keep working.
- A single `~` and an unclosed `~~` stay as literal text.
- Behaviour without the extension stays exactly as it is now.

**Out of scope**
- Turning the extension on by default, or adding it to the `extra` bundle (`markdown/extensions/extra.py`).
- Single-tilde strikethrough (`~text~`), subscript, or `<s>`/`<strike>` output.
- Changes to fenced code blocks that use `~~~` fences (`markdown/extensions/fenced_code.py`).
- Backslash-escaping of `~` (see Q-002).
- Configuration options for the extension.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Provide an opt-in built-in 'strikethrough' extension"
statement: "The system SHALL provide a built-in extension that loads by the short name 'strikethrough' (and by its dotted module path). Its effects SHALL apply only when it is listed in the 'extensions' argument."
epistemic_status: "FACT"
source: "Issue #4: \"Could there be a built-in extension for this, so I can write `markdown.markdown(text, extensions=['strikethrough'])`?\" and \"it should be off unless the extension is enabled.\" Loading mechanism: markdown/core.py:197-221, pyproject.toml:73-91."
actor: "Python developer calling markdown.markdown / markdown.Markdown"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: []
inputs: [{name: "extensions", type: "list[str | Extension]", description: "Extension list that contains 'strikethrough'"}]
outputs: [{name: "html", type: "str", description: "Rendered HTML"}]
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Extension enabled by short name"
    given: "Markdown source 'This is ~~deleted~~ text.'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p>This is <del>deleted</del> text.</p>'"
  - id: "AC-FR-001-02"
    scenario: "Extension not enabled: existing behaviour unchanged"
    given: "Markdown source 'This is ~~deleted~~ text.'"
    when: "markdown.markdown(source) is called with no extensions"
    then: "The output equals '<p>This is ~~deleted~~ text.</p>'"
  - id: "AC-FR-001-03"
    scenario: "Extension enabled by dotted module path"
    given: "Markdown source '~~gone~~'"
    when: "markdown.markdown(source, extensions=['markdown.extensions.strikethrough']) is called"
    then: "The output equals '<p><del>gone</del></p>'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Render paired double tildes as <del> with nested inline markup"
statement: "When the strikethrough extension is enabled, the system SHALL render text enclosed by an opening '~~' and a matching closing '~~' as a <del> element. Other inline markup inside it (strong, emphasis, links, code spans) SHALL still render. A lone '~', an unclosed '~~', and tildes inside code spans or fenced code blocks SHALL be output literally."
epistemic_status: "FACT"
source: "Issue #4: \"It should produce `<del>...</del>` like GitHub does, and other inline markup inside it (bold, emphasis, links) should still work. A single `~` or an unclosed `~~` should be left alone\". Inline processing: markdown/inlinepatterns.py:54-93 (DelimiterProcessor at 622)."
actor: "Author writing Markdown (e.g. changelogs) rendered with the extension enabled"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001"]
inputs: [{name: "source", type: "str", description: "Markdown text containing '~' characters"}]
outputs: [{name: "html", type: "str", description: "HTML with <del> elements for matched '~~' pairs"}]
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Bold, emphasis and a link inside strikethrough"
    given: "Markdown source '~~a **bold** and *em* [link](http://example.com)~~'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p><del>a <strong>bold</strong> and <em>em</em> <a href=\"http://example.com\">link</a></del></p>'"
  - id: "AC-FR-002-02"
    scenario: "Strikethrough inside emphasis"
    given: "Markdown source '**bold ~~struck~~**'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p><strong>bold <del>struck</del></strong></p>'"
  - id: "AC-FR-002-03"
    scenario: "Single tilde is left alone"
    given: "Markdown source 'about ~5 minutes and ~text~'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p>about ~5 minutes and ~text~</p>'"
  - id: "AC-FR-002-04"
    scenario: "Unclosed double tilde is left alone"
    given: "Markdown source 'this ~~is not closed'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p>this ~~is not closed</p>'"
  - id: "AC-FR-002-05"
    scenario: "Multiple strikethrough spans on one line"
    given: "Markdown source '~~one~~ and ~~two~~'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p><del>one</del> and <del>two</del></p>'"
  - id: "AC-FR-002-06"
    scenario: "Tildes in a code span stay literal (existing behaviour unchanged)"
    given: "Markdown source '`~~code~~`'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output equals '<p><code>~~code~~</code></p>'"
  - id: "AC-FR-002-07"
    scenario: "Tilde-fenced code block still works with both extensions enabled (existing behaviour unchanged)"
    given: "Markdown source '~~~\\n~~x~~\\n~~~'"
    when: "markdown.markdown(source, extensions=['strikethrough', 'fenced_code']) is called"
    then: "The output equals '<pre><code>~~x~~\\n</code></pre>'"
  - id: "AC-FR-002-08"
    scenario: "Emphasis without tildes is unaffected when the extension is enabled (existing behaviour unchanged)"
    given: "Markdown source '*em* and **strong** and ***both***'"
    when: "markdown.markdown(source, extensions=['strikethrough']) is called"
    then: "The output is identical to markdown.markdown(source) with no extensions"
verification_method: "TEST"
```

## 3. Non-functional requirements

None. The issue does not state or imply any measurable quality requirement.

## 4. Assumptions and open questions

**ASSUMP-001** [INFERRED]: The extension adds no `<del>` output from the default pipeline and does not change it in any way. Instances created without the extension behave exactly as before (AC-FR-001-02, AC-FR-002-08).
- Rationale: the issue says "it should be off unless the extension is enabled".
- Impact if invalid: HIGH. Existing documents would render differently.
- Validation: the full existing test suite passes unchanged.

**ASSUMP-002** [INFERRED]: Delimiter rules follow the existing `*`/`_` handling as closely as possible. Exactly two tildes open and close a span. Text between them must be non-empty, and a span may not start or end with whitespace. So `~~ text ~~` stays literal.
- Rationale: GitHub requires the delimiters to sit against the text, and the fork already has delimiter handling (`markdown/inlinepatterns.py:622`).
- Impact if invalid: LOW. Only edge cases change.
- Validation: maintainer review (Q-001).

**ASSUMP-003** [INFERRED]: The short name `strikethrough` is registered through a new entry point in `pyproject.toml`, like the other built-ins. Tests that use the short name need the package metadata to be current, i.e. an editable install that is re-run after the change.
- Impact if invalid: MEDIUM. AC-FR-001-01 would fail with an import error even if the extension works.
- Validation: run AC-FR-001-01 and AC-FR-001-03 in CI.

**ASSUMP-004** [INFERRED]: The extension does not add `~` to `ESCAPED_CHARS`.
- Rationale: the issue doesn't ask for it, and adding it would change how `\~` renders.
- Impact if invalid: LOW.
- Validation: Q-002.

**Q-001**: How should runs of three or more tildes (`~~~text~~~`) and whitespace-flanked delimiters (`~~ text ~~`) be treated?
- Option A: follow GitHub Flavored Markdown (GFM). Only matched `~~` runs strike through, and whitespace-flanked delimiters do not.
- Option B: strike through any `~~…~~`.
- Recommended default: A. It is adopted as ASSUMP-002.
- Affects: FR-002 (PROVISIONAL).

**Q-002**: Should `\~` become a supported escape when the extension is enabled, so that users can write a literal `~~`?
- Option A: no, as in the current behaviour.
- Option B: yes, like `tables` adds `|` (`markdown/extensions/tables.py:248-249`).
- Recommended default: A. It is adopted as ASSUMP-004.
- Affects: FR-002.

**Q-003**: Should `strikethrough` be added to the `extra` bundle or documented in `docs/extensions/`?
- Recommended default: add a documentation page; do not add it to `extra`.
- Affects: none of the FRs (out of scope).

## 5. Validation

1. **Completeness:** PASS. Each FR has an actor, inputs, outputs, and both normal and edge-case criteria.
2. **Testability:** PASS. Every criterion gives an exact input string and an exact or comparative expected output that a unit test can check.
3. **Consistency:** PASS. No contradictions. "Off by default" and "built-in" are compatible through an opt-in entry point.
4. **Feasibility:** PASS. The existing inline-processor and extension APIs support this (`markdown/inlinepatterns.py`, `markdown/extensions/__init__.py`).
5. **Traceability:** PASS. FR-001 and FR-002 trace to quoted text in issue #4, and every inferred detail traces to ASSUMP-001…004 or Q-001…003.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (A concrete input and the `strikethrough` extension name produce a fully specified exact HTML string to compare against.)
- AC-FR-001-02: testable=True (With no extensions, the input and the exact expected output (literal `~~` preserved) are specified, so an equality assertion decides pass or fail.)
- AC-FR-001-03: testable=True (The full dotted extension path `markdown.extensions.strikethrough` is given with an exact expected HTML string, so the assertion is unambiguous.)
- AC-FR-002-01: testable=True (Nested inline formatting with a specified input and exact expected HTML output allows a direct string equality check.)
- AC-FR-002-02: testable=True (Strikethrough nested inside strong emphasis has a concrete input and an exact expected output string.)
- AC-FR-002-03: testable=True (Single-tilde inputs are given with the exact expected output, which shows that single tildes are not converted to del tags.)
- AC-FR-002-04: testable=True (An unclosed delimiter has a concrete input and an exact expected output showing the markers are left as literal text.)
- AC-FR-002-05: testable=True (Two adjacent strikethrough spans have a concrete input and an exact expected output, so the test is a plain equality assertion.)
- AC-FR-002-06: testable=True (Tildes inside a code span have a concrete input and an exact expected `<code>` output, so the check is deterministic.)
- AC-FR-002-07: testable=True (The fenced block input, the extensions list and the exact expected `<pre><code>` output are all specified, making the assertion unambiguous.)
- AC-FR-002-08: testable=True (The expected result is a byte-for-byte comparison against the output of the same library call without extensions, which a test can run and assert.)
