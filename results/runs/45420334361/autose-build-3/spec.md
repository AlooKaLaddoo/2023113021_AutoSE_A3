# Spec: Wikilinks: allow custom link text with `[[Page Name|link text]]`

## 1. Summary and scope

The `wikilinks` extension (`markdown/extensions/wikilinks.py`) currently only recognises `[[Page Name]]`. Its pattern is `WIKILINK_RE = r'\[\[([\w0-9_ -]+)\]\]'` at `markdown/extensions/wikilinks.py:62`. Because `|` is not in that character class, `[[Installation Guide|see the install docs]]` does not match and stays as literal text. [FACT] The issue asks for an optional `|link text` part. The link must point to the same place as `[[Page Name]]` but show the custom text.

**In scope**
- Recognising `[[<page name>|<link text>]]` inside the `wikilinks` inline processor.
- Building the URL from the page name only, using the same steps as plain wikilinks: `build_url`, `base_url`, `end_url`, `html_class`, and the `wiki_base_url` / `wiki_end_url` / `wiki_html_class` meta-data overrides (`markdown/extensions/wikilinks.py:75-101`).
- Ignoring whitespace around the page name and the link text.
- Using the page name as the text when the link text is empty or only whitespace.
- Keeping plain `[[Page Name]]` behaviour unchanged, including the empty `[[ ]]` case.
- Updating the user docs (`docs/extensions/wikilinks.md`) to describe the new syntax. [INFERRED]

**Out of scope**
- Any other MediaWiki syntax: namespaces, `#anchors`, the "pipe trick" `[[Page|]]` that strips namespaces and parentheses, and link trails such as `[[Page]]s`.
- Changing which characters are allowed in the page name.
- Changing the signature of the `build_url` callable or the default URL-cleaning rules.
- `[[a|b]]` inside pipe tables, where the `tables` extension splits cells on `|` before inline processing (see Q-004).
- Adding new configuration options.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Render [[Page Name|link text]] as a wikilink with custom text"
statement: "The wikilinks extension SHALL convert `[[<page name>|<link text>]]` into an `<a>` element. Its `href` and `class` SHALL be exactly what `[[<page name>]]` would produce under the same configuration and meta-data, and its text SHALL be the stripped <link text>."
epistemic_status: "FACT"
source: "Issue #3: 'Could wikilinks support [[Page Name|link text]]? The link should point exactly where [[Page Name]] points (we rely on base_url, end_url, html_class, a custom build_url and the wiki_* meta-data overrides), just with different text.' Current behaviour: markdown/extensions/wikilinks.py:62 (regex excludes '|'), :75-101 (URL/class/meta handling); tests/test_extensions.py:158-253."
actor: "Document author using the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-002", "ASSUMP-003"]
inputs:
  - {name: "page name", type: "str", description: "Text before the first '|', made of the characters already allowed today ([\\w0-9_ -])"}
  - {name: "link text", type: "str", description: "Text after the first '|' and before ']]'"}
  - {name: "config / meta-data", type: "dict", description: "base_url, end_url, html_class, build_url, wiki_base_url, wiki_end_url, wiki_html_class"}
outputs:
  - {name: "anchor", type: "xml.etree.ElementTree.Element", description: "<a> with href from build_url(page name, base, end), optional class, and the link text as its text"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Default configuration"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'See [[Installation Guide|see the install docs]].'"
    then: "output is '<p>See <a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a>.</p>'"
  - id: "AC-FR-001-02"
    scenario: "Whitespace around the page name and the link text is ignored"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[ Installation Guide | see the install docs ]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a></p>'"
  - id: "AC-FR-001-03"
    scenario: "base_url, end_url and html_class are applied"
    given: "WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo')"
    when: "converting '[[WikiLink|the text]]'"
    then: "output is '<p><a class=\"foo\" href=\"/wiki/WikiLink.html\">the text</a></p>'"
  - id: "AC-FR-001-04"
    scenario: "A custom build_url gets the page name, not the link text"
    given: "WikiLinkExtension(build_url=f), where f(label, base, end) returns '/x/' + label + '/' and records the label it received"
    when: "converting '[[foo|bar]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/x/foo/\">bar</a></p>', and f was called exactly once with label 'foo'"
  - id: "AC-FR-001-05"
    scenario: "Meta-data overrides are applied"
    given: "markdown.Markdown(extensions=['meta', 'wikilinks'])"
    when: "converting 'wiki_base_url: http://example.com/\\nwiki_end_url:   .html\\nwiki_html_class:\\n\\nSome text with a [[WikiLink|custom]].'"
    then: "output is '<p>Some text with a <a href=\"http://example.com/WikiLink.html\">custom</a>.</p>'"
  - id: "AC-FR-001-06"
    scenario: "Only the first '|' separates; later '|' characters belong to the link text (PROVISIONAL, Q-002)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Page|a|b]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Page/\">a|b</a></p>'"
  - id: "AC-FR-001-07"
    scenario: "Special HTML characters in the link text are escaped, not passed through as raw HTML"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Page|a & b]]'"
    then: "output is '<p><a class=\"wikilink\" href=\"/Page/\">a &amp; b</a></p>'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Fall back to the page name when the link text is empty, and keep existing behaviour"
statement: "When the link text after '|' is empty or only whitespace, the wikilinks extension SHALL render exactly the output of `[[<page name>]]`. Plain `[[<page name>]]` links, including the empty `[[ ]]` case, SHALL produce the same output as before this change."
epistemic_status: "FACT"
source: "Issue #3: 'if the text part is empty just use the page name. Plain [[Page Name]] links must keep working the same way.' Existing behaviour: tests/test_extensions.py:165-253, tests/extensions/wikilinks.txt / wikilinks.html."
actor: "Document author using the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001", "ASSUMP-004"]
inputs:
  - {name: "wikilink source", type: "str", description: "'[[name|]]', '[[name|   ]]', '[[name]]', '[[ ]]', '[[ |text]]'"}
outputs:
  - {name: "rendered HTML", type: "str", description: "An anchor whose text is the stripped page name, or no anchor when the page name is empty"}
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
    then: "outputs are '<p>Some text with a <a class=\"wikilink\" href=\"/WikiLink/\">WikiLink</a>.</p>' and '<p><a class=\"wikilink\" href=\"/foo_bar_baz/\">foo bar_baz</a></p>', and every existing test in tests/test_extensions.py::TestWikiLinks and the tests/extensions/wikilinks.txt legacy test still passes unmodified"
  - id: "AC-FR-002-04"
    scenario: "Empty plain wikilink still renders nothing"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'foo [[ ]] bar'"
    then: "output is '<p>foo  bar</p>'"
  - id: "AC-FR-002-05"
    scenario: "Empty page name with link text produces no link (PROVISIONAL, Q-003)"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'foo [[ |text]] bar'"
    then: "output contains no '<a' element and no 'href', i.e. the same as the empty [[ ]] case: '<p>foo  bar</p>'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

**Assumptions**

- **ASSUMP-001** [INFERRED] The page name part keeps today's allowed characters (`[\w0-9_ -]`, `markdown/extensions/wikilinks.py:62`) and is cleaned by `build_url` exactly as it is today.
  - *Rationale:* The issue only asks for different text, not different page names.
  - *Impact if invalid:* LOW. A separate change could widen the allowed characters.
- **ASSUMP-002** [INFERRED] The link text may contain any characters except the sequence `]]` and a line break. The issue gives only plain-word examples.
  - *Impact if invalid:* MEDIUM. Inputs that use punctuation or brackets would render differently.
  - *Validation path:* Q-001.
- **ASSUMP-003** [INFERRED] The first `|` separates the page name from the link text. Any later `|` is literal link text. This follows the MediaWiki convention for ordinary page links.
  - *Impact if invalid:* LOW. See Q-002.
- **ASSUMP-004** [INFERRED] If the page name is empty or only whitespace, the whole construct renders as an empty string, even when link text is present. This matches the current `[[ ]]` handling (`markdown/extensions/wikilinks.py:76,85-86`).
  - *Impact if invalid:* LOW. See Q-003.
- **ASSUMP-005** [INFERRED] The link text is handled the same way the label is today. It is placed as element text, the serializer escapes it, and the extension does not process it in any special way for Markdown.
  - *Impact if invalid:* LOW. See Q-001.

**Open questions**

- **Q-001** What characters may the link text contain, and should inline Markdown (for example `*emphasis*`) inside it be rendered?
  - *Options:* (a) any characters except `]]` and newline, with inline handling the same as labels today; (b) the same restricted character class as page names; (c) full inline Markdown.
  - *Recommended default:* (a). Real MediaWiki link text contains punctuation, and (a) does not change how labels are handled.
  - *Blocks:* FR-001 (PROVISIONAL).
- **Q-002** How should `[[Page|a|b]]` render?
  - *Options:* (a) text `a|b`; (b) text `b`; (c) do not match.
  - *Recommended default:* (a), as in MediaWiki.
  - *Blocks:* AC-FR-001-06.
- **Q-003** How should `[[ |text]]` render?
  - *Options:* (a) nothing, consistent with `[[ ]]`; (b) leave the source as literal text; (c) a link to an empty page name.
  - *Recommended default:* (a).
  - *Blocks:* AC-FR-002-05.
- **Q-004** Should `[[Page|text]]` work inside pipe tables, where `|` is a cell separator?
  - *Recommended default:* Out of scope for now. Users can escape the pipe or avoid tables.
  - *Note:* A maintainer should know this as a known limitation.

**Risks**

- The issue text contained no instructions aimed at the pipeline. No injection attempt was detected.

## 5. Validation

1. **Completeness:** PASS. Both FRs define the actor, inputs and outputs, and have normal and edge-case Gherkin criteria with exact input and output.
2. **Testability:** PASS. Every criterion is an exact string comparison or a recorded-call check that a unit test can run. There are no subjective qualifiers and no NFRs.
3. **Consistency:** PASS. There are no contradictions. Plain-link behaviour is kept explicitly (AC-FR-002-03 and AC-FR-002-04).
4. **Feasibility:** PASS. The change is limited to the existing inline processor in `markdown/extensions/wikilinks.py`.
5. **Traceability:** PASS. Each FR cites the issue text and the current code and tests. Each provisional detail traces to ASSUMP-001 to ASSUMP-005 and Q-001 to Q-003.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (A concrete input and an exact expected HTML string give an unambiguous pass/fail comparison.)
- AC-FR-001-02: testable=True (The input with surrounding whitespace and the exact expected output allow a direct equality assertion.)
- AC-FR-001-03: testable=True (The constructor parameters, input, and exact expected output define a deterministic equality check.)
- AC-FR-001-04: testable=True (A stub build_url can be mocked to assert the exact output and that it was called exactly once with label 'foo'.)
- AC-FR-001-05: testable=True (The meta-driven configuration, input, and exact expected output form a deterministic equality assertion.)
- AC-FR-001-06: testable=True (The input '[[Page|a|b]]' and exact expected output allow a direct equality assertion.)
- AC-FR-001-07: testable=True (The input containing '&' and the exact escaped expected output allow a direct equality assertion.)
- AC-FR-002-01: testable=True (An empty label after the pipe with an exact expected output gives a deterministic equality check.)
- AC-FR-002-02: testable=True (Whitespace-only label input with an exact expected output allows a direct equality assertion.)
- AC-FR-002-03: testable=True (The two exact outputs are assertable, and the regression clause is pass/fail by running the named existing tests unmodified.)
- AC-FR-002-04: testable=True (The empty-link input '[[ ]]' with an exact expected output gives a deterministic equality check.)
- AC-FR-002-05: testable=True (The input '[[ |text]]' with an exact expected output, including absence of an anchor or href, is a deterministic assertion.)
