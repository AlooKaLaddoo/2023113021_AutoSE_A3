Closes #1

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45421929335)._

### Requirements (from spec.md)

- **FR-001** Treat a valueless heading id as absent and generate a slug: When the toc extension processes a heading element whose `id` attribute is present with value None (a valueless attribute from attr_list), the system SHALL treat the heading as having no id: it SHALL assign the unique slug generated from the heading text, use that slug in the TOC tokens and TOC HTML, and SHALL NOT raise an exception.
  - `AC-FR-001-01` given The source text '#d {id}', when markdown.markdown('#d {id}', extensions=['toc', 'attr_list']) is called, then No exception is raised and the return value is exactly '<h1 id="d">d</h1>'
  - `AC-FR-001-02` given The source text '[TOC]

# Some Title {id}', when It is converted with extensions=['toc', 'attr_list'], then No exception is raised; the output contains '<h1 id="some-title">Some Title</h1>' and the TOC div contains '<a href="#some-title">Some Title</a>'; md.toc_tokens == [{'level': 1, 'id': 'some-title', 'name': 'Some Title', 'html': 'Some Title', 'data-toc-label': '', 'children': []}]
  - `AC-FR-001-03` given The source text '# Title

# Title {id}', when It is converted with extensions=['toc', 'attr_list'], then No exception is raised and the output is exactly '<h1 id="title">Title</h1>
<h1 id="title_1">Title</h1>'
  - `AC-FR-001-04` given The source text '# Title {id .cls}', when It is converted with extensions=['toc', 'attr_list'], then No exception is raised and the output is exactly '<h1 class="cls" id="title">Title</h1>'
  - `AC-FR-001-05` given The source text '# Title {id}', when It is converted with extensions=['attr_list', TocExtension(permalink=True)] and, separately, with extensions=['attr_list', TocExtension(anchorlink=True)], then No exception is raised in either case; the heading has id="title" and the permalink/anchor href is '#title'
- **FR-002** Preserve existing id handling for explicit and absent ids: The system SHALL keep its current output for headings with an explicit id value and for headings without an id attribute when the toc and attr_list extensions are enabled.
  - `AC-FR-002-01` given The source text '# Title {#my-id}', when It is converted with extensions=['toc', 'attr_list'], then The output is exactly '<h1 id="my-id">Title</h1>' and md.toc_tokens[0]['id'] == 'my-id'
  - `AC-FR-002-02` given The source text '# Title', when It is converted with extensions=['toc', 'attr_list'], then The output is exactly '<h1 id="title">Title</h1>'
  - `AC-FR-002-03` given The repository test suite, including tests/test_syntax/extensions/test_toc.py and tests/test_syntax/extensions/test_attr_list.py, when python -m unittest discover -s tests -t . is run, then All tests pass
  - `AC-FR-002-04` given The source text '# Title {id}', when It is converted with extensions=['attr_list'] only (no toc), then The output is the same as before the change: the bare attribute is kept as rendered by the serializer, i.e. '<h1 id>Title</h1>'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/toc.py` | `TocTreeprocessor.run` | modify: in the used-ids loop, add `el.attrib["id"]` to `used_ids` only when it is not `None`. In the heading loop, replace `if "id" not in el.attrib:` with `if el.attrib.get("id") is None:` so a valueless id is overwritten with the unique slug. Update the comment to say a valueless id counts as no id. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add: tests for AC-FR-001-01 to AC-FR-001-05 (bare `{id}`, bare `{id}` with `[TOC]` checking the HTML and `md.toc_tokens`, slug collision giving `title_1`, `{id .cls}`, `TocExtension(permalink=True)` and `TocExtension(anchorlink=True)`) and AC-FR-002-01 / AC-FR-002-02 (explicit `{#my-id}` and no attributes, both with `toc` and `attr_list`). |
| `tests/test_syntax/extensions/test_attr_list.py` | `-` | add: a test that `# Title {id}` with only `attr_list` renders `<h1 id>Title</h1>` (AC-FR-002-04). Put it next to the existing valueless-attribute tests, in the same style as that test class. |
| `docs/changelog.md` | `-` | modify: add a bullet under `## [Unreleased]` → `### Fixed`: "Fix a `TypeError` in the `toc` extension when a heading has a valueless `{id}` attribute; a slug is now generated as if no id was given." |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1185 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/12
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-1`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45422650298
- Result: **PASS** 
