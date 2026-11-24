Closes #1

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45424111273)._

### Requirements (from spec.md)

- **FR-001** Treat a heading's valueless id as absent when generating TOC ids: When the toc extension processes a heading whose id attribute has no value (None) or an empty value, the system SHALL replace it with the id toc would generate for that heading if no id attribute were present, and SHALL NOT raise an exception.
  - `AC-FR-001-01` given source '#d {id}' and extensions ['toc', 'attr_list'], when markdown.markdown(source, extensions=['toc', 'attr_list']) is called, then no exception is raised and the result is exactly '<h1 id="d">d</h1>'
  - `AC-FR-001-02` given source '[TOC]\n\n# Header 1 {id}' and extensions ['toc', 'attr_list'], when the source is converted, then no exception is raised and the result is exactly '<div class="toc">\n<ul>\n<li><a href="#header-1">Header 1</a></li>\n</ul>\n</div>\n<h1 id="header-1">Header 1</h1>'
  - `AC-FR-001-03` given a Markdown instance md = markdown.Markdown(extensions=['toc', 'attr_list']), when md.convert('# Header 1 {id}') is called, then md.toc_tokens[0]['id'] == 'header-1' and md.toc_tokens[0]['name'] == 'Header 1'
  - `AC-FR-001-04` given source '# Title\n\n# Title {id}' and extensions ['toc', 'attr_list'], when the source is converted, then the result is exactly '<h1 id="title">Title</h1>\n<h1 id="title_1">Title</h1>'
  - `AC-FR-001-05` given source '# Header 1 {id}', extensions ['attr_list', toc.TocExtension(permalink=True)], when the source is converted, then no exception is raised, the h1 has id="header-1", and the permalink anchor has href="#header-1"
  - `AC-FR-001-06` given source '# Header 1 {id}', extensions ['attr_list', toc.TocExtension(anchorlink=True)], when the source is converted, then no exception is raised and the result is exactly '<h1 id="header-1"><a class="toclink" href="#header-1">Header 1</a></h1>'
  - `AC-FR-001-07` given sources '# Title {#my-id}' and '# Title {id=my-id}' with extensions ['toc', 'attr_list'], when each source is converted, then each result is exactly '<h1 id="my-id">Title</h1>'
  - `AC-FR-001-08` given source '# Heading {download}' with extensions ['toc', 'attr_list'], when the source is converted, then the result is exactly '<h1 download id="heading">Heading</h1>'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/toc.py` | `TocTreeprocessor.run` | modify: when collecting `used_ids`, add only truthy `el.attrib.get("id")` values. Change the "pre-existing ids" check from `"id" not in el.attrib` to `not el.attrib.get("id")`, so a `None` or `""` id is replaced with `unique(self.slugify(html.unescape(name), self.sep), used_ids, id_counters)`. Update the comment to say valueless ids count as absent. |
| `tests/test_syntax/extensions/test_toc.py` | `(new) TestTocValuelessId` | add: a `TestCase` with one test for each of AC-FR-001-01 to AC-FR-001-08, using `extensions=['toc', 'attr_list']` or `['attr_list', TocExtension(permalink=True / anchorlink=True)]`. Includes a `Markdown` instance check of `md.toc_tokens`. |
| `docs/changelog.md` | `-` | add: an entry under `## [Unreleased]` → `### Fixed`: "Fix `TypeError` in `toc` when a heading has a bare (valueless) `{id}` attribute from `attr_list`; a slug is now generated." |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1182 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/16
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-1-e2_implementer_writes_tests`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45424787681
- Result: **PASS** 
