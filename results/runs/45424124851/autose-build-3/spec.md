# Spec: Wikilinks: allow custom link text with `[[Page Name|link text]]`

## 1. Summary and scope

[FACT] The issue asks the `wikilinks` extension to support MediaWiki-style piped links `[[Page Name|link text]]`. The link must point exactly where `[[Page Name]]` points, and its visible text must be `link text`.

**Current behaviour (from the code):**
- `markdown/extensions/wikilinks.py:62` uses the pattern `WIKILINK_RE = r'\[\[([\w0-9_ -]+)\]\]'`. The character class has no `|`, so `[[Installation Guide|see the install docs]]` does not match. It stays as literal text: `<p>[[Installation Guide|see the install docs]]</p>`. [FACT]
- `WikiLinksInlineProcessor.handleMatch` (`wikilinks.py:75-87`) strips the label. It builds the URL with `config['build_url'](label, base_url, end_url)`, where `base_url`, `end_url` and `html_class` come from `_getMeta()` (`wikilinks.py:89-101`), so the `wiki_*` meta-data overrides apply. It sets `a.text = label` and adds `class` only when `html_class` is non-empty. A label that is only whitespace produces `''`. [FACT]

**In scope**
- Recognising `[[<page name>|<link text>]]` in the `wikilinks` extension.
- Building the URL from the page name only, using the same path as `[[<page name>]]`: `build_url`, `base_url`, `end_url`, `html_class` and the `wiki_base_url`, `wiki_end_url` and `wiki_html_class` meta-data overrides.
- Stripping whitespace around the page name and around the link text.
- Falling back to the page name when the link text is empty or only whitespace.
- Keeping plain `[[Page Name]]` behaviour unchanged.
- [INFERRED] Updating `docs/extensions/wikilinks.md` and `docs/changelog.md` to describe the new syntax, following project convention.

**Out of scope**
- Changing which characters are allowed in the page name. It stays `[\w0-9_ -]` as in `wikilinks.py:62`.
- Other MediaWiki syntax: namespaces (`[[Help:Foo]]`), section anchors (`[[Page#Section]]`), link trails (`[[Page]]s`), and nested or multiple pipes (`[[a|b|c]]`).
- Changing the signature of the `build_url` callable.
- New configuration options.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Render piped wikilinks with custom link text"
statement: "The wikilinks extension SHALL render `[[<page name>|<link text>]]` as an `<a>` element whose `href` and `class` equal those produced for `[[<page name>]]` under the same configuration and meta-data, and whose text is the link text with surrounding whitespace removed."
epistemic_status: "FACT"
source: "Issue #3: 'Could `wikilinks` support `[[Page Name|link text]]`? The link should point exactly where `[[Page Name]]` points (we rely on `base_url`, `end_url`, `html_class`, a custom `build_url` and the `wiki_*` meta-data overrides), just with different text. Whitespace around the name or the text shouldn't matter'; current code markdown/extensions/wikilinks.py:62,75-101"
actor: "Wiki author writing Markdown processed with the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: []
inputs:
  - {name: "page name", type: "string", description: "Text before `|`, using the existing page-name character set [\\w0-9_ -]"}
  - {name: "link text", type: "string", description: "Text after `|` (allowed characters: see ASSUMP-001)"}
outputs:
  - {name: "anchor", type: "HTML <a> element", description: "href/class derived from the page name; text = stripped link text"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Basic piped link with default configuration"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'Read [[Installation Guide|see the install docs]] first.'"
    then: "output is '<p>Read <a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a> first.</p>'"
  - id: "AC-FR-001-02"
    scenario: "Whitespace around page name and link text is ignored"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[  Installation Guide  |  see the install docs  ]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a></p>'"
  - id: "AC-FR-001-03"
    scenario: "Extension settings base_url, end_url, html_class apply to piped links"
    given: "markdown.Markdown(extensions=[WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo')])"
    when: "converting '[[Installation Guide|see the install docs]]'"
    then: "output is '<p><a class=\"foo\" href=\"/wiki/Installation_Guide.html\">see the install docs</a></p>'"
  - id: "AC-FR-001-04"
    scenario: "Custom build_url receives the page name, not the link text"
    given: "a build_url callable that records its `label` argument and returns '/bar/', passed as WikiLinkExtension(build_url=...)"
    when: "converting '[[foo|Some Text]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/bar/\">Some Text</a></p>' and the callable was called with label == 'foo', base == '/', end == '/'"
  - id: "AC-FR-001-05"
    scenario: "wiki_* meta-data overrides apply to piped links"
    given: "markdown.Markdown(extensions=['meta', 'wikilinks']) and the document 'wiki_base_url: http://example.com/\\nwiki_end_url:   .html\\nwiki_html_class:\\n\\nSee [[Installation Guide|the docs]].'"
    when: "converting the document"
    then: "output is '<p>See <a href=\"http://example.com/Installation_Guide.html\">the docs</a>.</p>' (no class attribute)"
  - id: "AC-FR-001-06"
    scenario: "Link text containing punctuation (ASSUMP-001)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Installation Guide|the install docs, v2.0!]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">the install docs, v2.0!</a></p>'"
  - id: "AC-FR-001-07"
    scenario: "More than one pipe is not a wikilink (ASSUMP-003)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[a|b|c]]'"
    then: "output contains no '<a' element and is '<p>[[a|b|c]]</p>'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Fall back to page name for empty link text; preserve plain wikilinks"
statement: "When the link text after `|` is empty or whitespace-only, the wikilinks extension SHALL render the link exactly as `[[<page name>]]` would be rendered; plain `[[<page name>]]` links and the existing empty-link behaviour SHALL remain unchanged."
epistemic_status: "FACT"
source: "Issue #3: 'if the text part is empty just use the page name. Plain `[[Page Name]]` links must keep working the same way.'; existing tests tests/test_extensions.py:158-253 (TestWikiLinks), tests/extensions/wikilinks.txt/.html"
actor: "Wiki author writing Markdown processed with the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001"]
inputs:
  - {name: "page name", type: "string", description: "Text before `|`, or the whole label when there is no `|`"}
  - {name: "link text", type: "string", description: "Empty or whitespace-only text after `|`, or absent"}
outputs:
  - {name: "anchor or empty string", type: "HTML <a> element | ''", description: "Same output as the equivalent plain wikilink"}
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Empty link text falls back to the page name"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Installation Guide|]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">Installation Guide</a></p>'"
  - id: "AC-FR-002-02"
    scenario: "Whitespace-only link text falls back to the stripped page name"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[ Installation Guide |   ]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">Installation Guide</a></p>'"
  - id: "AC-FR-002-03"
    scenario: "Plain wikilinks are unchanged"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'Some text with a [[WikiLink]].' and '[[ foo bar_baz ]]'"
    then: "outputs are '<p>Some text with a <a class=\"wikilink\" href=\"/WikiLink/\">WikiLink</a>.</p>' and '<p><a class=\"wikilink\" href=\"/foo_bar_baz/\">foo bar_baz</a></p>'; all existing TestWikiLinks tests and the tests/extensions/wikilinks.txt -> wikilinks.html legacy test still pass unmodified"
  - id: "AC-FR-002-04"
    scenario: "Empty page name with link text produces no link (ASSUMP-002)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'foo [[ |some text]] bar' and 'foo [[ ]] bar'"
    then: "both outputs are '<p>foo  bar</p>' (same as the existing empty-wikilink behaviour)"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: Link text may contain any characters except `[`, `]`, `|` and newline. This includes punctuation such as `,`, `.`, `!`, `'`, `(`, `)`.
  - **Rationale:** Real wiki link texts often contain punctuation. The issue's example only uses letters and spaces.
  - **Impact if invalid:** MEDIUM. AC-FR-001-06 would change.
  - **Validation path:** maintainer answers Q-001.
- **ASSUMP-002** [INFERRED]: An empty or whitespace-only page name with non-empty link text (`[[ |text]]`) renders as `''`, which is what `[[ ]]` does today (`wikilinks.py:85-86`, `tests/test_extensions.py:180-183`).
  - **Impact if invalid:** LOW. Only AC-FR-002-04 changes.
  - **Validation path:** maintainer answers Q-002.
- **ASSUMP-003** [INFERRED]: A label with more than one `|` is not treated as a wikilink and stays literal text.
  - **Impact if invalid:** LOW. Only AC-FR-001-07 changes.
  - **Validation path:** maintainer answers Q-003.
- **ASSUMP-004** [INFERRED]: Inline Markdown inside the link text, such as `_emphasis_`, is processed the same way it is in plain wikilink labels today (`tests/extensions/wikilinks.html:4`). This spec has no acceptance criterion that pins this down.
- **ASSUMP-005** [FACT]: The `build_url(label, base, end)` callable keeps its signature. `label` is the stripped page name.
- **Q-001**: Which characters are allowed in the link text?
  - **Options:** (a) anything except `[`, `]`, `|` and newline; (b) the same character set as the page name, `[\w0-9_ -]`; (c) anything except `]`.
  - **Trade-offs:** (b) is the most conservative, but common text like "docs, v2" would not link. (c) makes `[[a|b|c]]` ambiguous.
  - **Recommended default:** (a).
  - **Blocks:** FR-001 (AC-FR-001-06, AC-FR-001-07).
- **Q-002**: What should `[[ |text]]` (empty page name) render?
  - **Options:** (a) `''`, matching `[[ ]]`; (b) literal text; (c) the text without a link.
  - **Recommended default:** (a).
  - **Blocks:** FR-002 (AC-FR-002-04).
- **Q-003**: Should `[[a|b|c]]` be supported, for example with the text `b|c`?
  - **Recommended default:** no; leave it as literal text.
  - **Blocks:** FR-001 (AC-FR-001-07).
- **Risk:** None. The issue text contains no instructions aimed at the pipeline.

## 5. Validation

1. **Completeness:** PASS. Both FRs define an actor, inputs and outputs, and have normal and edge-case acceptance criteria, including criteria that existing behaviour stays unchanged (AC-FR-002-03, AC-FR-002-04).
2. **Testability:** PASS. Every acceptance criterion gives exact input Markdown and exact expected HTML, or an exact `build_url` argument check. There are no subjective qualifiers and no NFRs.
3. **Consistency:** PASS. There are no contradictions. FR-002's fallback and FR-001's stripping rules match the issue text and the current code.
4. **Feasibility:** PASS. This is a local change to `markdown/extensions/wikilinks.py` (the pattern and `handleMatch`), plus docs.
5. **Traceability:** PASS. Each FR cites an issue quote and code or test paths. The parts that go beyond the issue are tied to ASSUMP-001 to ASSUMP-003 and Q-001 to Q-003, so both FRs are PROVISIONAL.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Given a fixed extension config and input string, the exact expected HTML output is stated, so a unit test can assert equality.)
- AC-FR-001-02: testable=True (The input with surrounding whitespace in the label and link text has an exact expected output, so a unit test can assert the trimmed result.)
- AC-FR-001-03: testable=True (WikiLinkExtension is configured with explicit base_url, end_url and html_class, and the exact expected output string is given.)
- AC-FR-001-04: testable=True (A stub build_url callable can record its arguments, and the test can assert both the recorded label/base/end values and the rendered output.)
- AC-FR-001-05: testable=True (The meta-supplied base URL, end URL and empty html_class are fixed in the document, and the exact output without a class attribute is specified.)
- AC-FR-001-06: testable=True (The label with punctuation and the link target have a concrete input and exact expected output, so equality can be asserted.)
- AC-FR-001-07: testable=True (The input '[[a|b|c]]' has an exact expected literal output with no anchor element, which a test can check by equality.)
- AC-FR-002-01: testable=True (An empty target after the pipe has a concrete input and exact expected output that falls back to the label text.)
- AC-FR-002-02: testable=True (Whitespace-only target and whitespace-padded label have a concrete input and exact expected output, so a test can assert it.)
- AC-FR-002-03: testable=True (Both example outputs are exact, and the regression requirement (existing TestWikiLinks and the legacy wikilinks.txt test pass unmodified) is a deterministic pass/fail check by running the suite, though it is a suite-level rather than a single unit assertion.)
- AC-FR-002-04: testable=True (Two concrete inputs with empty wikilink targets have an exact expected output string '<p>foo  bar</p>', so a test can assert equality for both.)
