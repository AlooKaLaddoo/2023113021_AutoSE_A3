# Spec: TypeError in toc when a heading has a bare `{id}` attribute

## 1. Summary and scope

[FACT] With the `toc` and `attr_list` extensions both enabled, a heading with a bare (valueless) `id` attribute crashes. For example, `markdown.markdown('#d {id}', extensions=['toc', 'attr_list'])` raises `TypeError: expected string or bytes-like object, got 'NoneType'`. The issue says this happens with and without a `[TOC]` marker. The reporter expects the heading to behave as if no id was given and to get the normal slug.

What the code shows (grounded):
- `markdown/extensions/attr_list.py:53-63` (`_handle_word`) turns a word with no value into `(word, None)`. `AttrListTreeprocessor.assign_attrs` (`attr_list.py:201-212`) then calls `elem.set('id', None)`, because `id` is not a boolean attribute.
- `markdown/extensions/toc.py:403` only creates a slug when `"id" not in el.attrib`. Here the key exists but its value is `None`, so no slug is made. Line 417 then calls `unescape(el.attrib["id"])` on `None`, and that raises the `TypeError`. If `anchorlink`/`permalink` are on, `add_anchor` (line 424) gets `None` as well.
- Headings with a real id (`# Title {#my-id}` or `{id=my-id}`) keep their explicit id. That is the "Do not override pre-existing ids" behaviour at `toc.py:402-404`.

**In scope**
- When `toc` runs, a heading whose `id` attribute has no value (`None`) or an empty string gets the same id `toc` would generate if no id had been given. This applies with and without a `[TOC]` marker, and with or without `anchorlink`/`permalink`.
- The `toc` output (`[TOC]` HTML, `md.toc`, `md.toc_tokens`) lists that heading with the generated id.

**Out of scope**
- How `attr_list` alone renders a valueless `id` when `toc` is not enabled (today: `<h1 id>d</h1>`). See Q-002.
- Bare `{data-toc-label}` and other valueless attributes that `toc` reads. See Q-003.
- Valueless `id` on elements that are not headings.
- Any change to how `attr_list` parses valueless attributes in general.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Treat a heading's valueless id as absent when generating TOC ids"
statement: "When the toc extension processes a heading whose id attribute has no value (None) or an empty value, the system SHALL replace it with the id toc would generate for that heading if no id attribute were present, and SHALL NOT raise an exception."
epistemic_status: "FACT"
source: "Issue #1: \"I'd expect it to just behave as if no id was given (generate the normal slug), not crash the whole build.\"; markdown/extensions/toc.py:402-404, 417; markdown/extensions/attr_list.py:53-63, 201-212"
actor: "Document author using markdown.markdown with extensions ['toc', 'attr_list']"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: []
inputs:
  - {name: "source", type: "str", description: "Markdown text containing a heading with a bare `{id}` attribute list"}
  - {name: "extensions", type: "list", description: "['toc', 'attr_list'], optionally with toc config such as permalink/anchorlink"}
outputs:
  - {name: "html", type: "str", description: "Rendered HTML in which the heading has the generated slug id"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Issue reproduction without a [TOC] marker"
    given: "source '#d {id}' and extensions ['toc', 'attr_list']"
    when: "markdown.markdown(source, extensions=['toc', 'attr_list']) is called"
    then: "no exception is raised and the result is exactly '<h1 id=\"d\">d</h1>'"
  - id: "AC-FR-001-02"
    scenario: "Issue reproduction with a [TOC] marker"
    given: "source '[TOC]\\n\\n# Header 1 {id}' and extensions ['toc', 'attr_list']"
    when: "the source is converted"
    then: "no exception is raised and the result is exactly '<div class=\"toc\">\\n<ul>\\n<li><a href=\"#header-1\">Header 1</a></li>\\n</ul>\\n</div>\\n<h1 id=\"header-1\">Header 1</h1>'"
  - id: "AC-FR-001-03"
    scenario: "toc_tokens carry the generated id"
    given: "a Markdown instance md = markdown.Markdown(extensions=['toc', 'attr_list'])"
    when: "md.convert('# Header 1 {id}') is called"
    then: "md.toc_tokens[0]['id'] == 'header-1' and md.toc_tokens[0]['name'] == 'Header 1'"
  - id: "AC-FR-001-04"
    scenario: "Generated id stays unique next to an identical heading"
    given: "source '# Title\\n\\n# Title {id}' and extensions ['toc', 'attr_list']"
    when: "the source is converted"
    then: "the result is exactly '<h1 id=\"title\">Title</h1>\\n<h1 id=\"title_1\">Title</h1>'"
  - id: "AC-FR-001-05"
    scenario: "Edge case: permalink enabled"
    given: "source '# Header 1 {id}', extensions ['attr_list', toc.TocExtension(permalink=True)]"
    when: "the source is converted"
    then: "no exception is raised, the h1 has id=\"header-1\", and the permalink anchor has href=\"#header-1\""
  - id: "AC-FR-001-06"
    scenario: "Edge case: anchorlink enabled"
    given: "source '# Header 1 {id}', extensions ['attr_list', toc.TocExtension(anchorlink=True)]"
    when: "the source is converted"
    then: "no exception is raised and the result is exactly '<h1 id=\"header-1\"><a class=\"toclink\" href=\"#header-1\">Header 1</a></h1>'"
  - id: "AC-FR-001-07"
    scenario: "Existing behaviour unchanged: explicit ids are not overridden"
    given: "sources '# Title {#my-id}' and '# Title {id=my-id}' with extensions ['toc', 'attr_list']"
    when: "each source is converted"
    then: "each result is exactly '<h1 id=\"my-id\">Title</h1>'"
  - id: "AC-FR-001-08"
    scenario: "Existing behaviour unchanged: other valueless attributes on a heading are preserved"
    given: "source '# Heading {download}' with extensions ['toc', 'attr_list']"
    when: "the source is converted"
    then: "the result is exactly '<h1 download id=\"heading\">Heading</h1>'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: An `id` attribute whose value is an empty string (for example, an element created by another extension with `id=""`) should also get a generated slug, the same as `None`. An empty id is not a usable anchor, so this matches the reporter's intent. Impact if invalid: LOW. No AC depends on the empty-string case. Validation path: maintainer review (Q-001).
- **ASSUMP-002** [INFERRED]: When `toc` is enabled, the generated id replaces the bare `id`. It is not kept alongside the bare `id`, because an element can only have one `id` attribute. Impact if invalid: LOW.
- **ASSUMP-003** [INFERRED]: The bug comes from `attr_list` now keeping valueless attributes as `None` (`attr_list.py:58-62`; tests in `tests/test_syntax/extensions/test_attr_list.py:149-303`). That `attr_list` behaviour stays unchanged for every attribute except, through `toc`, a heading's `id`. Impact if invalid: MEDIUM. If maintainers would rather fix this in `attr_list`, AC-FR-001-08 still applies.
- **Q-001**: Should an empty-string id (`id=""`) on a heading be replaced as well? Options: (a) treat it like `None` and generate a slug; (b) keep the empty id. **Recommended default:** (a), adopted as ASSUMP-001. No FR is blocked.
- **Q-002**: Without `toc`, should `attr_list` still render `# d {id}` as `<h1 id>d</h1>` (a valueless id, which is invalid HTML)? Options: (a) keep the current behaviour; (b) drop the valueless `id`; (c) emit `id="id"`. **Recommended default:** (a), and leave it out of scope for this issue. No FR is blocked.
- **Q-003**: A bare `{data-toc-label}` on a heading reaches `unescape(el.attrib['data-toc-label'])` at `toc.py:408` with `None`. Code reading suggests it crashes the same way. Should the same fix cover it? **Recommended default:** handle it in a separate issue. Possible behaviour: ignore the label and use the heading text. It is out of scope here. No FR is blocked.

## 5. Validation

1. Completeness: PASS. FR-001 has an actor, inputs, outputs, normal ACs (01-04), edge ACs (05-06) and unchanged-behaviour ACs (07-08).
2. Testability: PASS. Every AC has exact input Markdown and exact or directly assertable output. There are no subjective qualifiers.
3. Consistency: PASS. There are no contradictions. FR-001 keeps the existing rule that explicit ids are not overridden (AC-FR-001-07).
4. Feasibility: PASS. This is a local change in how `toc` handles existing ids (`markdown/extensions/toc.py:402-404`), with no new dependencies.
5. Traceability: PASS. FR-001 traces to the issue quote and to `toc.py:402-417` and `attr_list.py:53-63, 201-212`. The assumptions trace to Q-001 to Q-003.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Concrete input source and extensions are given, and the expected output is an exact string plus a no-exception condition, so a unit test can assert pass/fail directly.)
- AC-FR-001-02: testable=True (Concrete source with [TOC] marker and an exact expected HTML string are specified, allowing an unambiguous equality assertion.)
- AC-FR-001-03: testable=True (Given a specific Markdown instance, a triggering convert call, and exact expected values for toc_tokens[0]['id'] and ['name'], the result is a definite pass/fail.)
- AC-FR-001-04: testable=True (Two-heading source with an exact expected output string, including the deduplicated id 'title_1', gives a precise equality check.)
- AC-FR-001-05: testable=True (Specific extension configuration and checkable attributes (h1 id and permalink href) are stated, so the assertions are objective.)
- AC-FR-001-06: testable=True (The criterion gives a concrete source, configuration, and exact expected HTML string, enabling a deterministic equality test.)
- AC-FR-001-07: testable=True (Two specific inputs and an exact expected output for each are given, so both cases can be asserted with equality checks.)
- AC-FR-001-08: testable=True (A concrete source and an exact expected output string are provided, making the result verifiable by a single equality assertion.)
