# Spec: Support ~~strikethrough~~ like GitHub

## 1. Summary and scope

Python-Markdown has no strikethrough syntax. `~~text~~` is currently passed through as literal text. The default escapable characters in `markdown/core.py:112-114` do not include `~`, and no built-in processor handles `~` (only `markdown/extensions/fenced_code.py:66` uses it, for `~~~` code fences). The issue asks for a built-in extension, enabled by name with `extensions=['strikethrough']`, that renders `~~text~~` as `<del>text</del>`.

**In scope**
- A new built-in extension that can be loaded by the short name `strikethrough`. Per ARCHITECTURE.md C2 and §ADR on extension loading, built-ins are registered as entry points in `pyproject.toml` (`[project.entry-points.'markdown.extensions']`, lines 73-91).
- Rendering `~~text~~` as `<del>text</del>` when the extension is enabled.
- Inline markup inside the struck text (strong, emphasis, links) keeps working.
- A single `~` and an unclosed `~~` stay literal.
- Behaviour without the extension stays exactly as it is now.

**Out of scope**
- Single-tilde strikethrough (`~text~`). The issue explicitly says a single `~` is left alone.
- Adding the extension to the `extra` bundle (`markdown/extensions/extra.py`).
- Subscript, `<s>` or `<strike>` output, and any configuration options.
- Any change to `~~~` fenced code blocks.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Provide an opt-in built-in strikethrough extension"
statement: "The system SHALL provide a built-in extension that can be loaded with markdown.markdown(text, extensions=['strikethrough']), and SHALL NOT treat '~~' specially when the extension is not enabled."
epistemic_status: "FACT"
source: "Issue #4: 'Could there be a built-in extension for this, so I can write markdown.markdown(text, extensions=['strikethrough'])' ... 'it should be off unless the extension is enabled.' Loading mechanism: markdown/core.py:209-220 (entry-point lookup), pyproject.toml:73-91, ARCHITECTURE.md C2."
actor: "Python developer calling markdown.markdown / markdown.Markdown"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: []
inputs: [{name: "extensions", type: "list[str | Extension]", description: "Extension list containing 'strikethrough', the dotted path 'markdown.extensions.strikethrough', or an extension instance"}]
outputs: [{name: "html", type: "str", description: "Rendered HTML"}]
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Extension loaded by short name"
    given: "Markdown source '~~foo~~'"
    when: "markdown.markdown('~~foo~~', extensions=['strikethrough']) is called"
    then: "No exception is raised and the result is '<p><del>foo</del></p>'"
  - id: "AC-FR-001-02"
    scenario: "Extension loaded by dotted module path"
    given: "Markdown source '~~foo~~'"
    when: "markdown.markdown('~~foo~~', extensions=['markdown.extensions.strikethrough']) is called"
    then: "The result is '<p><del>foo</del></p>'"
  - id: "AC-FR-001-03"
    scenario: "Existing behaviour unchanged when extension is not enabled"
    given: "Markdown source '~~foo~~ and *bar*'"
    when: "markdown.markdown('~~foo~~ and *bar*') is called with no extensions"
    then: "The result is '<p>~~foo~~ and <em>bar</em></p>' (identical to current output)"
  - id: "AC-FR-001-04"
    scenario: "Fenced code still works alongside the extension"
    given: "Markdown source '~~~\n~~foo~~\n~~~'"
    when: "markdown.markdown(source, extensions=['strikethrough', 'fenced_code']) is called"
    then: "The result is '<pre><code>~~foo~~\n</code></pre>' (tildes inside the code block are not converted)"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Render double-tilde spans as <del> with nested inline markup"
statement: "When the strikethrough extension is enabled, the system SHALL render text enclosed in a matching pair of '~~' delimiters as a <del> element whose content is still processed for other inline markup (strong, emphasis, links)."
epistemic_status: "FACT"
source: "Issue #4: 'It should produce <del>...</del> like GitHub does, and other inline markup inside it (bold, emphasis, links) should still work.'"
actor: "Document author / Python developer"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: ["FR-001"]
inputs: [{name: "text", type: "str", description: "Markdown source containing ~~...~~ spans"}]
outputs: [{name: "html", type: "str", description: "HTML with <del> elements"}]
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Plain strikethrough inside a sentence"
    given: "Markdown source 'This is ~~withdrawn~~ text.'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>This is <del>withdrawn</del> text.</p>'"
  - id: "AC-FR-002-02"
    scenario: "Bold, emphasis and a link inside strikethrough"
    given: "Markdown source '~~**bold** *em* [link](http://example.com)~~'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p><del><strong>bold</strong> <em>em</em> <a href=\"http://example.com\">link</a></del></p>'"
  - id: "AC-FR-002-03"
    scenario: "Strikethrough inside emphasis"
    given: "Markdown source '*a ~~b~~ c*'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p><em>a <del>b</del> c</em></p>'"
  - id: "AC-FR-002-04"
    scenario: "Multiple spans in one paragraph"
    given: "Markdown source '~~one~~ and ~~two~~'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p><del>one</del> and <del>two</del></p>'"
  - id: "AC-FR-002-05"
    scenario: "Code spans are not affected"
    given: "Markdown source '`~~code~~`'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p><code>~~code~~</code></p>'"
verification_method: "TEST"
```

```yaml
id: "FR-003"
title: "Leave single and unmatched tildes literal"
statement: "When the strikethrough extension is enabled, the system SHALL leave a single '~', an unclosed '~~', and '~~' delimiters that cannot form a valid span as literal text in the output."
epistemic_status: "FACT"
source: "Issue #4: 'A single ~ or an unclosed ~~ should be left alone'"
actor: "Document author"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: ["FR-001"]
inputs: [{name: "text", type: "str", description: "Markdown source with stray tildes"}]
outputs: [{name: "html", type: "str", description: "HTML with tildes preserved"}]
acceptance_criteria:
  - id: "AC-FR-003-01"
    scenario: "Single tilde pair is not strikethrough"
    given: "Markdown source 'about ~5 minutes, ~foo~'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>about ~5 minutes, ~foo~</p>'"
  - id: "AC-FR-003-02"
    scenario: "Unclosed double tilde"
    given: "Markdown source 'an ~~unclosed span'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>an ~~unclosed span</p>'"
  - id: "AC-FR-003-03"
    scenario: "Whitespace-flanked delimiters do not open or close a span (PROVISIONAL, see ASSUMP-002)"
    given: "Markdown source 'a ~~ b ~~ c'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>a ~~ b ~~ c</p>'"
  - id: "AC-FR-003-04"
    scenario: "Three or more tildes are not a delimiter (PROVISIONAL, see ASSUMP-003)"
    given: "Markdown source '~~~foo~~~'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>~~~foo~~~</p>'"
  - id: "AC-FR-003-05"
    scenario: "Backslash-escaped tildes are literal (PROVISIONAL, see ASSUMP-004)"
    given: "Markdown source '\\~\\~foo\\~\\~'"
    when: "converted with extensions=['strikethrough']"
    then: "The result is '<p>~~foo~~</p>'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: Output uses exactly the tag `<del>` with no attributes, as GitHub does. Impact if invalid: LOW (only the tag name in tests would change). Validation: maintainer review.
- **ASSUMP-002** [INFERRED] (default from Q-001): Delimiter flanking follows the same rules as the existing `*` emphasis delimiter in `markdown/inlinepatterns.py:600-609`. An opening `~~` must not be followed by whitespace, and a closing `~~` must not be preceded by whitespace. Intraword use such as `a~~b~~c` → `<p>a<del>b</del>c</p>` is allowed, as in GFM. Impact if invalid: MEDIUM. Affects AC-FR-003-03.
- **ASSUMP-003** [INFERRED] (default from Q-002): Only a run of exactly two tildes acts as a delimiter. Runs of three or more stay literal, as in GFM. Impact if invalid: LOW. Affects AC-FR-003-04.
- **ASSUMP-004** [INFERRED] (default from Q-003): When enabled, the extension adds `~` to `md.ESCAPED_CHARS` so that authors can escape it, following the precedent in `markdown/extensions/tables.py:248-249`. Without the extension, `\~` keeps its current output. Impact if invalid: LOW. Affects AC-FR-003-05.
- **ASSUMP-005** [INFERRED]: The extension takes no configuration options and is not added to `extra`. Impact if invalid: LOW.
- **Q-001**: How should whitespace flanking and intraword tildes work? Options: (a) emphasis-like flanking with intraword allowed (GFM); (b) allow any `~~…~~` pair regardless of spacing; (c) forbid intraword. **Recommended default: (a).** Blocks: AC-FR-003-03 (PROVISIONAL).
- **Q-002**: Should `~~~text~~~` strike through? Options: (a) no, leave literal (GFM); (b) treat it as `~` + `<del>`. **Recommended default: (a).** Blocks: AC-FR-003-04 (PROVISIONAL).
- **Q-003**: Should `\~` become escapable when the extension is enabled? Options: (a) yes, only when the extension is on; (b) always, in core (would change default behaviour, so not recommended); (c) no. **Recommended default: (a).** Blocks: AC-FR-003-05 (PROVISIONAL).
- **Q-004**: Should `strikethrough` be included in the `extra` bundle? **Recommended default: no.** This keeps the change minimal and opt-in, as the issue asks.
- **RISK-001**: The existing `DelimiterProcessor` (`markdown/inlinepatterns.py:622-662`) assumes a single `md.delimiters` registry shared by `*` and `_`. Adding `~` to it could change `*`/`_` pairing when the extension is enabled. Mitigation: the tests above, plus running the existing emphasis tests with the extension enabled.
- No prompt-injection attempt was found in the issue text.

## 5. Validation

1. **Completeness:** PASS. Each FR has an actor, inputs, outputs, a normal-case criterion and edge-case criteria, and each says whether existing behaviour is unchanged.
2. **Testability:** PASS. Every criterion gives exact input Markdown and exact expected HTML, and there are no subjective qualifiers.
3. **Consistency:** PASS. Nothing contradicts. The single `~` rule from the issue is kept (single-tilde strikethrough is out of scope).
4. **Feasibility:** PASS. The extension registry and delimiter infrastructure already exist (`markdown/extensions/legacy_em.py`, `markdown/inlinepatterns.py`).
5. **Traceability:** PASS. FR-001 to FR-003 quote the issue. Provisional criteria map to ASSUMP-002, ASSUMP-003 and ASSUMP-004 and to questions Q-001, Q-002 and Q-003.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Gives a concrete input, a specific call with the 'strikethrough' extension, and an exact expected HTML output, so a unit test can assert no exception and string equality.)
- AC-FR-001-02: testable=True (Specifies the exact call with the 'markdown.extensions.strikethrough' extension path and the exact expected output string, giving an unambiguous pass/fail.)
- AC-FR-001-03: testable=True (Specifies the input, the call with no extensions, and the exact expected output identical to current behavior, which can be asserted against a fixed string.)
- AC-FR-001-04: testable=True (Specifies a fenced code block input, the extensions used, and the exact expected output, so the test can check that tildes inside the code block are left unconverted.)
- AC-FR-002-01: testable=True (Concrete input, extension, and exact expected HTML output for strikethrough within a sentence.)
- AC-FR-002-02: testable=True (Concrete nested-formatting input and an exact expected HTML string that a test can compare directly.)
- AC-FR-002-03: testable=True (Concrete emphasis-wrapping-strikethrough input with an exact expected HTML output.)
- AC-FR-002-04: testable=True (Concrete input with two strikethrough spans and an exact expected HTML output.)
- AC-FR-002-05: testable=True (Concrete inline-code input and exact expected output showing tildes inside code spans are not converted.)
- AC-FR-003-01: testable=True (Concrete input with single-tilde cases and an exact expected output showing no conversion.)
- AC-FR-003-02: testable=True (Concrete unclosed-span input and exact expected output that leaves the tildes as literal text.)
- AC-FR-003-03: testable=True (Concrete input with whitespace-padded tildes and an exact expected unconverted output.)
- AC-FR-003-04: testable=True (Concrete triple-tilde input and exact expected literal output, which a test can assert directly.)
- AC-FR-003-05: testable=True (Concrete input with backslash-escaped tildes and an exact expected output of literal tildes, so a string comparison is unambiguous.)
