# Spec: Wikilinks: allow custom link text with `[[Page Name|link text]]`

## 1. Summary and scope

The `wikilinks` extension (`markdown/extensions/wikilinks.py`) currently matches only `[[label]]`, using the pattern `WIKILINK_RE = r'\[\[([\w0-9_ -]+)\]\]'` at `markdown/extensions/wikilinks.py:62`. The `|` character is not allowed, so `[[Installation Guide|see the install docs]]` does not match and stays in the output as literal text. [FACT]

The issue asks for a piped form, `[[Page Name|link text]]`. It should build the same link as `[[Page Name]]` but show `link text` as the visible text. [FACT]

**In scope**
- Recognise `[[<page name>|<link text>]]` inside the `wikilinks` extension.
- Build `href` and `class` for the piped form exactly as for `[[<page name>]]`. This covers `base_url`, `end_url`, `html_class`, a custom `build_url`, and the `wiki_base_url`, `wiki_end_url` and `wiki_html_class` meta-data overrides.
- Strip leading and trailing whitespace from the page name and from the link text.
- Use the page name as the link text when the text part is empty or contains only whitespace.
- Leave the behaviour of plain `[[Page Name]]` unchanged.
- Update the documentation in `docs/extensions/wikilinks.md` (INFERRED, COULD_HAVE).

**Out of scope**
- Changing which characters a page name may contain (still `[\w0-9_ -]`).
- Other MediaWiki syntax: namespaces, `#section` anchors, the "pipe trick" `[[Page|]]` with MediaWiki semantics, and link trails such as `[[Page]]s`.
- A guaranteed result when the link text contains inline Markdown such as `*emphasis*` (see Q-003).
- Changes to the `build_url` signature or to the configuration options.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Render piped wikilinks with custom link text"
statement: "The wikilinks extension SHALL convert `[[<page name>|<link text>]]` into an `<a>` element whose `href` and `class` are exactly those produced for `[[<page name>]]` under the same configuration and meta-data, and whose text is <link text> with leading and trailing whitespace removed; when the stripped link text is empty, the element text SHALL be the stripped page name."
epistemic_status: "FACT"
source: "Issue #3: 'Could wikilinks support [[Page Name|link text]]? The link should point exactly where [[Page Name]] points (we rely on base_url, end_url, html_class, a custom build_url and the wiki_* meta-data overrides), just with different text. Whitespace around the name or the text shouldn't matter, and if the text part is empty just use the page name.' Current behaviour: markdown/extensions/wikilinks.py:62 (regex without '|'), :75-87 (handleMatch), :89-101 (_getMeta)."
actor: "Markdown author using the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-002", "ASSUMP-003"]
inputs:
  - {name: "source", type: "str", description: "Markdown containing [[<page name>|<link text>]]"}
  - {name: "config", type: "dict", description: "base_url, end_url, html_class, build_url; optional wiki_* meta-data via the meta extension"}
outputs:
  - {name: "html", type: "str", description: "HTML with an <a> element for each piped wikilink"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Piped link with default configuration"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'See [[Installation Guide|see the install docs]].'"
    then: "output == '<p>See <a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a>.</p>'"
  - id: "AC-FR-001-02"
    scenario: "Whitespace around the page name and the text is ignored"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[  Installation Guide  |  see the install docs  ]]'"
    then: "output == '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">see the install docs</a></p>'"
  - id: "AC-FR-001-03"
    scenario: "Empty text part falls back to the page name"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Installation Guide|]]' and, separately, '[[Installation Guide|   ]]'"
    then: "both outputs == '<p><a class=\"wikilink\" href=\"/Installation_Guide/\">Installation Guide</a></p>'"
  - id: "AC-FR-001-04"
    scenario: "Config options apply to the piped form"
    given: "markdown.markdown(text, extensions=[WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo')])"
    when: "converting 'Some text with a [[WikiLink|custom text]].'"
    then: "output == '<p>Some text with a <a class=\"foo\" href=\"/wiki/WikiLink.html\">custom text</a>.</p>'"
  - id: "AC-FR-001-05"
    scenario: "Empty html_class omits the class attribute"
    given: "markdown.Markdown(extensions=['wikilinks'], extension_configs={'wikilinks': [('base_url', 'http://example.com/'), ('end_url', '.html'), ('html_class', '')]})"
    when: "converting '[[WikiLink|custom text]]'"
    then: "output == '<p><a href=\"http://example.com/WikiLink.html\">custom text</a></p>'"
  - id: "AC-FR-001-06"
    scenario: "Custom build_url receives only the stripped page name"
    given: "a build_url callable that records its `label` argument and returns '/bar/', passed via WikiLinkExtension(build_url=...)"
    when: "converting '[[ foo | some text ]]'"
    then: "output == '<p><a class=\"wikilink\" href=\"/bar/\">some text</a></p>' and the recorded label == 'foo'"
  - id: "AC-FR-001-07"
    scenario: "Meta-data overrides apply to the piped form and do not carry over"
    given: "markdown.Markdown(extensions=['meta', 'wikilinks'])"
    when: "converting 'wiki_base_url: http://example.com/\\nwiki_end_url:   .html\\nwiki_html_class:\\n\\nSome text with a [[WikiLink|custom text]].' and then converting 'No [[MetaData|here]] now.'"
    then: "first output == '<p>Some text with a <a href=\"http://example.com/WikiLink.html\">custom text</a>.</p>' and second output == '<p>No <a class=\"wikilink\" href=\"/MetaData/\">here</a> now.</p>'"
  - id: "AC-FR-001-08"
    scenario: "Special HTML characters in link text are escaped"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[Page|Q&A <docs>]]'"
    then: "output == '<p><a class=\"wikilink\" href=\"/Page/\">Q&amp;A &lt;docs&gt;</a></p>'"
  - id: "AC-FR-001-09"
    scenario: "Empty page name with text does not become a link"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'foo [[ |text]] bar'"
    then: "the output contains no '<a' element (PROVISIONAL, see Q-002)"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Preserve existing behaviour of plain wikilinks"
statement: "The wikilinks extension SHALL produce, for input without a `|` inside `[[...]]`, output identical to the current implementation."
epistemic_status: "FACT"
source: "Issue #3: 'Plain [[Page Name]] links must keep working the same way.' Existing tests: tests/test_extensions.py:158-253 (TestWikiLinks)."
actor: "Existing users of the wikilinks extension"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: ["FR-001"]
inputs:
  - {name: "source", type: "str", description: "Markdown containing only [[<page name>]] wikilinks"}
outputs:
  - {name: "html", type: "str", description: "Unchanged HTML"}
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Basic plain wikilink is unchanged"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting 'Some text with a [[WikiLink]].'"
    then: "output == '<p>Some text with a <a class=\"wikilink\" href=\"/WikiLink/\">WikiLink</a>.</p>'"
  - id: "AC-FR-002-02"
    scenario: "Whitespace and empty plain wikilinks are unchanged"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[ foo bar_baz ]]' and 'foo [[ ]] bar'"
    then: "outputs == '<p><a class=\"wikilink\" href=\"/foo_bar_baz/\">foo bar_baz</a></p>' and '<p>foo  bar</p>' respectively"
  - id: "AC-FR-002-03"
    scenario: "All existing TestWikiLinks tests keep passing"
    given: "the unchanged tests in tests/test_extensions.py::TestWikiLinks"
    when: "running python -m unittest discover -s tests -t ."
    then: "all tests pass with no change to their expected output"
  - id: "AC-FR-002-04"
    scenario: "Text with invalid page-name characters stays literal"
    given: "markdown.Markdown(extensions=['wikilinks'])"
    when: "converting '[[foo.bar]]'"
    then: "output == '<p>[[foo.bar]]</p>' (as it is today)"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: The link text may contain any characters except `|` and `]`. Any `[` in the text is treated as a literal character. Rationale: the issue's example uses only words and spaces, and MediaWiki link text is free-form. Impact if invalid: MEDIUM, because the regex would need to be narrowed or widened. Validation: maintainer review of Q-001.
- **ASSUMP-002** [INFERRED]: The page name before `|` uses the same character set as today, `[\w0-9_ -]`. If the page name has any other character, the whole construct stays literal text. Impact if invalid: LOW.
- **ASSUMP-003** [INFERRED]: If the page name is empty or whitespace-only and the text is not empty (`[[ |text]]`), no link is produced. Impact if invalid: LOW. See Q-002.
- **ASSUMP-004** [INFERRED]: Input with more than one `|`, such as `[[A|b|c]]`, does not become a link and stays literal text. Impact if invalid: LOW. See Q-001.
- **Q-001**: Which characters may the link text contain, and how are multiple `|` handled?
  - Options:
    - (a) Anything except `|` and `]`. Multiple pipes stay literal.
    - (b) Anything except `]`, with everything after the first `|` used as the text (MediaWiki-like).
    - (c) The same character set as page names. This is too narrow for text like "Q&A".
  - **Recommended default: (a).** Affects FR-001.
- **Q-002**: What should `[[ |text]]` (empty page name, non-empty text) produce?
  - Options:
    - (a) No link: the construct is removed, as `[[ ]]` is today.
    - (b) No link: the source is left as literal text.
    - (c) A link to `base_url + end_url`.
  - **Recommended default: (a) or (b).** Both satisfy AC-FR-001-09 ("no `<a>` element"). The maintainer should pick one. Affects FR-001.
- **Q-003**: Should inline Markdown in the link text, such as `[[Page|*important*]]`, be rendered or kept literal?
  - Options:
    - (a) Leave it unspecified and untested (default pipeline behaviour).
    - (b) Treat the text as atomic/literal.
    - (c) Explicitly process inline markup.
  - **Recommended default: (a).** The issue does not ask for either. Out of scope.

## 5. Validation

1. **Completeness:** PASS. Both FRs list an actor, inputs and outputs, and have normal and edge-case criteria.
2. **Testability:** PASS. Every criterion names an exact input string and an exact or checkable output. There are no subjective qualifiers.
3. **Consistency:** PASS. FR-001 applies only to input containing `|`, and FR-002 only to input without it, so they do not conflict.
4. **Feasibility:** PASS. This is a local change to the regex and `handleMatch` in `markdown/extensions/wikilinks.py`, and it reuses the existing `_getMeta` and `build_url`.
5. **Traceability:** PASS. FR-001 and FR-002 quote issue #3 and cite code and test locations. The provisional parts trace to ASSUMP-001–004 and Q-001–003.

Risk note: the issue text contained no instructions aimed at the agent, so no prompt-injection attempt was found.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (A concrete input and an exact expected HTML string give an unambiguous pass/fail comparison.)
- AC-FR-001-02: testable=True (Whitespace-padded input has a single exact expected output, so equality can be asserted directly.)
- AC-FR-001-03: testable=True (Two concrete inputs with empty or whitespace-only text each map to one exact expected output.)
- AC-FR-001-04: testable=True (Specific constructor arguments and input produce one exact expected string that can be compared.)
- AC-FR-001-05: testable=True (Extension configs and input are fully specified, yielding an exact expected output string.)
- AC-FR-001-06: testable=True (A recording callable lets the test assert both the exact output and the exact label argument received.)
- AC-FR-001-07: testable=True (Meta-data input and a follow-up conversion have exact expected outputs, so the test checks per-document config reset and application.)
- AC-FR-001-08: testable=True (Input containing special characters has an exact expected escaped output string.)
- AC-FR-001-09: testable=True (The assertion (no '<a' element in output) is a clear pass/fail check, though it is marked PROVISIONAL pending Q-002 and may change.)
- AC-FR-002-01: testable=True (A bare wikilink input has one exact expected HTML output to compare against.)
- AC-FR-002-02: testable=True (Two concrete inputs with exact expected outputs for label-to-URL slugging and empty-link handling are directly assertable.)
- AC-FR-002-03: testable=True (Running the named test suite gives a definitive pass/fail result, though it is a regression run rather than a single unit test.)
- AC-FR-002-04: testable=True (Input '[[foo.bar]]' has an exact expected literal output, so the non-link behavior is assertable.)
