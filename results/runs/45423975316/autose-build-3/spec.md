# Spec: Wikilinks: allow custom link text with `[[Page Name|link text]]`

## 1. Summary and scope

The `wikilinks` extension (`markdown/extensions/wikilinks.py`) only recognises `[[Label]]`. The pattern is `WIKILINK_RE = r'\[\[([\w0-9_ -]+)\]\]'` (line 62). The label sets both the URL, through `build_url(label, base_url, end_url)`, and the link text (`a.text = label`, line 81). A `|` is not in the allowed character class, so `[[Installation Guide|see the install docs]]` does not match and is left as literal text [FACT, from the issue and the code].

The issue asks for MediaWiki-style piped links. In `[[Page Name|link text]]`, the part before `|` sets the URL in exactly the same way as `[[Page Name]]`. The part after `|` becomes the visible text.

**In scope**
- Recognise `[[Page Name|link text]]` and render it as a link whose `href` and `class` match those of `[[Page Name]]`, and whose text is `link text`.
- The page name goes through the same URL path as plain links: `base_url`, `end_url`, `html_class`, a custom `build_url`, and the `wiki_base_url` / `wiki_end_url` / `wiki_html_class` meta-data overrides.
- Leading and trailing whitespace is ignored around the page name and around the text.
- If the text part is empty or contains only whitespace, the page name is used as the text.
- Plain `[[Page Name]]` links, including the empty `[[ ]]` case, behave exactly as they do now.

**Out of scope**
- Other MediaWiki syntax: namespaces (`[[Help:X]]`), anchors (`[[Page#Section]]`), the pipe trick (`[[Page (x)|]]` stripping), link trails (`[[Page]]s`), templates.
- Widening the character set allowed in the page name (it stays `[\w0-9_ -]`).
- New configuration options.
- Documentation wording. A maintainer may update `docs/extensions/wikilinks.md`, but this spec does not require it.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Render piped wikilinks with custom link text"
statement: "The wikilinks extension SHALL convert `[[<name>|<text>]]` into an `<a>` element whose `href` and `class` attributes are identical to those produced for `[[<name>]]` under the same configuration and meta-data, and whose text content is <text> with leading and trailing whitespace removed."
epistemic_status: "FACT"
source: "Issue #3: 'Could `wikilinks` support `[[Page Name|link text]]`? The link should point exactly where `[[Page Name]]` points (we rely on `base_url`, `end_url`, `html_class`, a custom `build_url` and the `wiki_*` meta-data overrides), just with different text. Whitespace around the name or the text shouldn't matter'. Current behaviour: markdown/extensions/wikilinks.py lines 62, 75-87, 89-101; tests/test_extensions.py TestWikiLinks."
actor: "Document author using the wikilinks extension (e.g. migrating a MediaWiki wiki)"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: []
inputs:
  - {name: "source", type: "str", description: "Markdown containing `[[name|text]]`"}
  - {name: "config", type: "dict", description: "base_url, end_url, html_class, build_url; optional Meta wiki_base_url / wiki_end_url / wiki_html_class"}
outputs:
  - {name: "html", type: "str", description: "HTML containing <a href=... class=...>text</a>"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Basic piped link with default config"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Installation Guide|see the install docs]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a></p>'"
  - id: "AC-FR-001-02"
    scenario: "Whitespace around name and text is ignored"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[ Installation Guide | see the install docs ]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a></p>'"
  - id: "AC-FR-001-03"
    scenario: "Simple settings apply to piped links"
    given: "WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo')"
    when: "converting 'Some text with a [[WikiLink|a link]].'"
    then: "output is exactly '<p>Some text with a <a class=\"foo\" href=\"/wiki/WikiLink.html\">a link</a>.</p>'"
  - id: "AC-FR-001-04"
    scenario: "Empty html_class omits class attribute"
    given: "extension_configs {'wikilinks': {'base_url': 'http://example.com/', 'end_url': '.html', 'html_class': ''}}"
    when: "converting '[[WikiLink|a link]]'"
    then: "output is exactly '<p><a href=\"http://example.com/WikiLink.html\">a link</a></p>'"
  - id: "AC-FR-001-05"
    scenario: "Meta-data overrides apply to piped links"
    given: "markdown.Markdown(extensions=['meta', 'wikilinks']) and source 'wiki_base_url: http://example.com/\\nwiki_end_url:   .html\\nwiki_html_class:\\n\\nSome text with a [[WikiLink|a link]].'"
    when: "converting the source"
    then: "output is exactly '<p>Some text with a <a href=\"http://example.com/WikiLink.html\">a link</a>.</p>'"
  - id: "AC-FR-001-06"
    scenario: "Custom build_url receives the page name, not the link text"
    given: "WikiLinkExtension(build_url=f) where f(label, base, end) records label and returns '/bar/'"
    when: "converting '[[ foo | some text ]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/bar/\">some text</a></p>' and f was called with label == 'foo', base == '/', end == '/'"
  - id: "AC-FR-001-07"
    scenario: "Internal whitespace in text is preserved, as for plain labels"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[foo|double  spaces]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/foo/\">double  spaces</a></p>'"
  - id: "AC-FR-001-08"
    scenario: "Special characters in link text are HTML-escaped"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[foo|Q&A <docs>]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/foo/\">Q&amp;A &lt;docs&gt;</a></p>' (PROVISIONAL, see ASSUMP-001)"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Fall back to page name for empty link text; keep plain wikilinks unchanged"
statement: "When the text part of `[[<name>|<text>]]` is empty or whitespace-only, the extension SHALL render the same output as `[[<name>]]`. Wikilinks without `|` SHALL render exactly as they do before this change."
epistemic_status: "FACT"
source: "Issue #3: 'if the text part is empty just use the page name. Plain `[[Page Name]]` links must keep working the same way.' Existing behaviour: tests/test_extensions.py TestWikiLinks, tests/extensions/wikilinks.txt/.html (run via tests/test_legacy.py)."
actor: "Document author using the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001"]
inputs:
  - {name: "source", type: "str", description: "Markdown with `[[name|]]`, `[[name|   ]]` or `[[name]]`"}
outputs:
  - {name: "html", type: "str", description: "HTML link using the page name as text"}
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Empty text falls back to page name"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Installation Guide|]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">Installation Guide</a></p>'"
  - id: "AC-FR-002-02"
    scenario: "Whitespace-only text falls back to the stripped page name"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[ Installation Guide |   ]]'"
    then: "output is exactly '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">Installation Guide</a></p>'"
  - id: "AC-FR-002-03"
    scenario: "Plain wikilinks unchanged"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'Some text with a [[WikiLink]].', '[[ foo bar_baz ]]' and 'foo [[ ]] bar'"
    then: "outputs are exactly '<p>Some text with a <a class=\"wikilink\" href=\"/WikiLink/\">WikiLink</a>.</p>', '<p><a class=\"wikilink\" href=\"/foo_bar_baz/\">foo bar_baz</a></p>' and '<p>foo  bar</p>'; all existing TestWikiLinks tests and the legacy tests/extensions/wikilinks.txt -> wikilinks.html test still pass unmodified"
  - id: "AC-FR-002-04"
    scenario: "Empty page name with text produces no link (consistent with `[[ ]]`)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'foo [[ |text]] bar'"
    then: "output contains no '<a' element (PROVISIONAL, see ASSUMP-002 / Q-002); recommended exact output '<p>foo  bar</p>'"
  - id: "AC-FR-002-05"
    scenario: "More than one pipe is not treated as a piped link"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[a|b|c]]'"
    then: "output is exactly '<p>[[a|b|c]]</p>' (PROVISIONAL, see ASSUMP-003 / Q-003)"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: The link text may contain any character on a single line except `[`, `]` and `|`. That includes punctuation such as `&`, `.`, `!`, `,`, `'`. The issue's only example uses letters and spaces, but real MediaWiki link texts often contain punctuation. The page-name character set stays `[\w0-9_ -]`. Impact if invalid: MEDIUM, because some texts would not render as links. Validation: maintainer review (Q-001).
- **ASSUMP-002** [INFERRED]: `[[ |text]]` (empty page name) renders the same way as the existing `[[ ]]`, i.e. it becomes an empty string and no link (`markdown/extensions/wikilinks.py` lines 76-86). Impact if invalid: LOW.
- **ASSUMP-003** [INFERRED]: Text that itself contains `|` (e.g. `[[a|b|c]]`) is not recognised as a wikilink and stays literal. Impact if invalid: LOW.
- **ASSUMP-004** [INFERRED]: Other inline Markdown inside the text is processed the same way as in plain labels today. Today `[[has _emphasis_ inside]]` renders `has <em>emphasis</em> inside` (`tests/extensions/wikilinks.html` line 4), so `[[Page|see _docs_]]` would show `see <em>docs</em>`. Impact if invalid: LOW.
- **Q-001**: Which characters are allowed in the link text? Options: (a) anything except `[`, `]`, `|` and newline; (b) the same `[\w0-9_ -]` set as the page name; (c) anything except `]]`. Recommended default: (a). Affects FR-001 (AC-FR-001-08).
- **Q-002**: What should `[[ |text]]` render: nothing, the literal text, or `text` without a link? Recommended default: nothing, to match `[[ ]]`. Affects FR-002 (AC-FR-002-04).
- **Q-003**: Should `[[a|b|c]]` follow MediaWiki and show `b|c` as the text, or stay literal? Recommended default: stay literal, which is simpler and less surprising. Affects FR-002 (AC-FR-002-05).
- **Risk note**: The issue text contains no instructions aimed at the pipeline. No prompt-injection attempt was found.

## 5. Validation

1. **Completeness:** PASS. Both FRs have an actor, inputs, outputs, and normal plus edge-case acceptance criteria.
2. **Testability:** PASS. Every acceptance criterion gives exact input Markdown and exact or clearly checkable HTML output. There are no subjective qualifiers.
3. **Consistency:** PASS. There are no contradictions. The empty-name and multiple-pipe behaviour follows the existing `[[ ]]` handling.
4. **Feasibility:** PASS. The change only touches the wikilinks pattern and `handleMatch` in `markdown/extensions/wikilinks.py`.
5. **Traceability:** PASS. FR-001 and FR-002 trace to quotes from issue #3 and to the code and tests cited. The provisional acceptance criteria trace to ASSUMP-001 to 003 and Q-001 to 003.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Gives a concrete input and an exact expected HTML output, so a unit test can assert equality.)
- AC-FR-001-02: testable=True (Gives a concrete input with surrounding whitespace and an exact expected output, so a unit test can assert equality.)
- AC-FR-001-03: testable=True (Specifies the extension configuration, a concrete input sentence, and the exact expected output string.)
- AC-FR-001-04: testable=True (Specifies an extension config with an empty html_class and an exact expected output, so the result is a deterministic equality check.)
- AC-FR-001-05: testable=True (Provides a meta-block source with config keys and the exact expected output, so the conversion result can be asserted directly.)
- AC-FR-001-06: testable=True (A callback that records its arguments gives observable call arguments and an exact output, both of which a test can assert.)
- AC-FR-001-07: testable=True (Gives an input with double spaces and an exact expected output, so the whitespace preservation can be asserted by equality.)
- AC-FR-001-08: testable=True (Gives a concrete input containing HTML-special characters and an exact expected escaped output; the PROVISIONAL marker concerns the spec's status, not whether the outcome is measurable.)
- AC-FR-002-01: testable=True (An empty target after the pipe with a concrete input yields an exact expected output that a test can compare.)
- AC-FR-002-02: testable=True (Whitespace-only target with a concrete input yields an exact expected output that a test can compare.)
- AC-FR-002-03: testable=True (Lists three concrete inputs with exact expected outputs, and the regression requirement (existing TestWikiLinks and wikilinks.txt tests pass unmodified) is a runnable pass/fail check.)
- AC-FR-002-04: testable=True (The criterion asserts a binary, mechanically checkable property (output contains no '<a' element) for a concrete input.)
- AC-FR-002-05: testable=True (Gives a concrete input with an exact expected output, so the result can be asserted by string equality.)
