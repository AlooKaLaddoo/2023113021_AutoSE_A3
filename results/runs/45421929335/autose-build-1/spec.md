# Spec: TypeError in toc when a heading has a bare `{id}` attribute

## 1. Summary and scope

When `toc` and `attr_list` are used together, a heading with a valueless `id` attribute (for example `#d {id}`) makes `markdown.markdown()` raise `TypeError: expected string or bytes-like object, got 'NoneType'`. The issue expects this to work as if no id had been given, so the heading gets the normal generated slug. [FACT]

The cause, confirmed in the code:
- `markdown/extensions/attr_list.py:53-63` (`_handle_word`) turns a valueless word into the attribute pair `(word, None)`.
- `markdown/extensions/attr_list.py:201-212` (`assign_attrs`) sets any valueless attribute other than a known boolean attribute with `elem.set(name, None)`. So the heading gets `id=None`.
- `markdown/extensions/toc.py:403` only creates a slug when the `"id"` key is missing from `el.attrib`, so the `None` value is kept.
- `markdown/extensions/toc.py:417` then calls `unescape(el.attrib["id"])` on that `None` value, which raises the `TypeError`. [INFERRED from code reading]

**In scope**
- The `toc` extension handles a heading whose `id` attribute is valueless (`None`) the same way as a heading with no `id`: it generates the slug, makes it unique and stores it on the heading.
- This applies with and without a `[TOC]` marker in the document.
- Existing behaviour stays the same for headings with an explicit id (`{#my-id}`) or no attribute list.

**Out of scope**
- Changing how `attr_list` parses or serializes valueless attributes in general. The `None` representation is deliberate and covered by `tests/test_syntax/extensions/test_attr_list.py:138-300`.
- Valueless `id` attributes on non-heading elements, such as paragraphs.
- Other valueless attributes that `toc` reads, such as `{data-toc-label}`. See Q-002.
- Empty-string ids, such as `{id=""}`.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Treat a valueless heading id as absent and generate a slug"
statement: "When the toc extension processes a heading element whose `id` attribute is present with value None (a valueless attribute from attr_list), the system SHALL treat the heading as having no id: it SHALL assign the unique slug generated from the heading text, use that slug in the TOC tokens and TOC HTML, and SHALL NOT raise an exception."
epistemic_status: "FACT"
source: "Issue #1: \"markdown.markdown('#d {id}', extensions=['toc', 'attr_list']) ... TypeError ... I'd expect it to just behave as if no id was given (generate the normal slug), not crash\"; markdown/extensions/toc.py:403,417; markdown/extensions/attr_list.py:201-212"
actor: "Python-Markdown user calling markdown.markdown() with the toc and attr_list extensions"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: []
inputs:
  - {name: "source", type: "str", description: "Markdown text containing a heading with a valueless `{id}` attribute list"}
outputs:
  - {name: "html", type: "str", description: "Rendered HTML in which the heading carries the generated slug as its id"}
  - {name: "toc_tokens", type: "list[dict]", description: "Markdown.toc_tokens entries whose 'id' is the generated slug"}
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Reported reproduction renders without error"
    given: "The source text '#d {id}'"
    when: "markdown.markdown('#d {id}', extensions=['toc', 'attr_list']) is called"
    then: "No exception is raised and the return value is exactly '<h1 id=\"d\">d</h1>'"
  - id: "AC-FR-001-02"
    scenario: "Bare id with a [TOC] marker: heading and TOC link use the slug"
    given: "The source text '[TOC]\n\n# Some Title {id}'"
    when: "It is converted with extensions=['toc', 'attr_list']"
    then: "No exception is raised; the output contains '<h1 id=\"some-title\">Some Title</h1>' and the TOC div contains '<a href=\"#some-title\">Some Title</a>'; md.toc_tokens == [{'level': 1, 'id': 'some-title', 'name': 'Some Title', 'html': 'Some Title', 'data-toc-label': '', 'children': []}]"
  - id: "AC-FR-001-03"
    scenario: "Generated slug is unique when it collides with an existing heading"
    given: "The source text '# Title\n\n# Title {id}'"
    when: "It is converted with extensions=['toc', 'attr_list']"
    then: "No exception is raised and the output is exactly '<h1 id=\"title\">Title</h1>\n<h1 id=\"title_1\">Title</h1>'"
  - id: "AC-FR-001-04"
    scenario: "Bare id together with other attributes keeps the other attributes"
    given: "The source text '# Title {id .cls}'"
    when: "It is converted with extensions=['toc', 'attr_list']"
    then: "No exception is raised and the output is exactly '<h1 class=\"cls\" id=\"title\">Title</h1>'"
  - id: "AC-FR-001-05"
    scenario: "Bare id with anchorlink / permalink options"
    given: "The source text '# Title {id}'"
    when: "It is converted with extensions=['attr_list', TocExtension(permalink=True)] and, separately, with extensions=['attr_list', TocExtension(anchorlink=True)]"
    then: "No exception is raised in either case; the heading has id=\"title\" and the permalink/anchor href is '#title'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Preserve existing id handling for explicit and absent ids"
statement: "The system SHALL keep its current output for headings with an explicit id value and for headings without an id attribute when the toc and attr_list extensions are enabled."
epistemic_status: "FACT"
source: "Issue #1: \"Headings with a real id like `# Title {#my-id}` work fine.\"; markdown/extensions/toc.py:402-404 (\"Do not override pre-existing ids\")"
actor: "Python-Markdown user calling markdown.markdown() with the toc and attr_list extensions"
priority: "MUST_HAVE"
readiness_status: "READY_FOR_DEV"
dependencies: ["FR-001"]
inputs:
  - {name: "source", type: "str", description: "Markdown headings with an explicit id or with no attribute list"}
outputs:
  - {name: "html", type: "str", description: "Rendered HTML, unchanged from current behaviour"}
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Explicit id is not overridden"
    given: "The source text '# Title {#my-id}'"
    when: "It is converted with extensions=['toc', 'attr_list']"
    then: "The output is exactly '<h1 id=\"my-id\">Title</h1>' and md.toc_tokens[0]['id'] == 'my-id'"
  - id: "AC-FR-002-02"
    scenario: "Heading without attributes still gets its slug"
    given: "The source text '# Title'"
    when: "It is converted with extensions=['toc', 'attr_list']"
    then: "The output is exactly '<h1 id=\"title\">Title</h1>'"
  - id: "AC-FR-002-03"
    scenario: "Existing test suite still passes"
    given: "The repository test suite, including tests/test_syntax/extensions/test_toc.py and tests/test_syntax/extensions/test_attr_list.py"
    when: "python -m unittest discover -s tests -t . is run"
    then: "All tests pass"
  - id: "AC-FR-002-04"
    scenario: "Valueless attributes without toc are unchanged"
    given: "The source text '# Title {id}'"
    when: "It is converted with extensions=['attr_list'] only (no toc)"
    then: "The output is the same as before the change: the bare attribute is kept as rendered by the serializer, i.e. '<h1 id>Title</h1>'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: A valueless `id` on a heading counts as "no id given" for `toc`, so the generated slug replaces the bare `id` in the output instead of leaving `<h1 id>`. *Rationale:* the issue explicitly asks for this ("behave as if no id was given"). *Impact if invalid:* LOW. *Validation path:* maintainer review of the pull request.
- **ASSUMP-002** [INFERRED]: In AC-FR-002-04 the output `<h1 id>Title</h1>` is the current serialization of a valueless non-boolean attribute. This is based on `attr_list.py:201-212` and the valueless-attribute tests at `test_attr_list.py:138-300`. *Impact if invalid:* LOW; the test should then record whatever master currently produces. *Validation path:* run it on master.
- **ASSUMP-003** [INFERRED]: The order of attributes in the output for AC-FR-001-04 (`class` before `id`) follows the order in which `attr_list` set them: `id` was inserted first as `None` and then overwritten in place. *Impact if invalid:* LOW; a test may compare attributes without depending on order. *Validation path:* run the test.
- **Q-001**: Should a bare `{id}` on a heading produce a warning or be silently replaced by the slug? Options: (a) silently replace it, which matches the issue; (b) log a warning. **Recommended default:** (a). This affects FR-001, which already adopts (a).
- **Q-002**: A valueless `{data-toc-label}` on a heading probably crashes in the same way, because `toc.py:408` calls `unescape(el.attrib['data-toc-label'])`. Should it be fixed in the same change? Options: (a) leave it out of scope for this issue; (b) treat a valueless `data-toc-label` as absent too. **Recommended default:** (a), with a follow-up for the maintainers to decide. No requirement depends on it.

## 5. Validation

1. **Completeness:** PASS. Both FRs list an actor, inputs and outputs, a normal case and edge cases.
2. **Testability:** PASS. Every acceptance criterion gives an exact Markdown input and an exact or substring-checkable output, and there are no subjective words.
3. **Consistency:** PASS. FR-001 changes only the valueless-id case, and FR-002 keeps every other case as it is, so they do not conflict.
4. **Feasibility:** PASS. The fix is a local change to `markdown/extensions/toc.py` (around lines 403-404), with no new dependencies.
5. **Traceability:** PASS. Each FR cites the issue text and the code locations in `toc.py` and `attr_list.py`. Provisional choices are recorded as ASSUMP-001 to ASSUMP-003, and no prompt-injection content was found in the issue.


---
## Stage 1 check (orchestrator, attempt 1)

Result: **PASS**

- AC-FR-001-01: testable=True (Concrete input, explicit call with extensions, and an exact expected return value plus a no-exception condition give an unambiguous pass/fail.)
- AC-FR-001-02: testable=True (Concrete input and extensions are given, and the expected HTML substrings and md.toc_tokens structure are exact, so a test can assert each one.)
- AC-FR-001-03: testable=True (Duplicate-heading input produces an exact expected output string, so the test is a direct equality assertion.)
- AC-FR-001-04: testable=True (The input attribute list and the exact expected output string allow a deterministic equality assertion.)
- AC-FR-001-05: testable=True (Two concrete extension configurations are specified, with checkable outcomes (no exception, id="title", href '#title'), so each can be asserted.)
- AC-FR-002-01: testable=True (Input with an explicit #my-id attribute gives an exact output string and a specific md.toc_tokens[0]['id'] value to assert.)
- AC-FR-002-02: testable=True (A plain heading with no attributes has a fixed expected output string, so a direct equality test can check it.)
- AC-FR-002-03: testable=True (The command is specified and the outcome is binary (all tests pass), so the criterion can be checked by running the suite, though it is a suite-level check rather than a unit test.)
- AC-FR-002-04: testable=True (Input with only attr_list and an exact expected serialized output '<h1 id>Title</h1>' allow a deterministic equality assertion.)
