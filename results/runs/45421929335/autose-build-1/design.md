# Design: Treat a valueless heading `{id}` as absent in the toc extension

## Approach

The fix goes in the `toc` tree processor (`TocTreeprocessor.run` in `markdown/extensions/toc.py`). A heading whose `id` attribute is `None` (a bare `{id}` from `attr_list`) will be handled like a heading with no `id`.

- **Slug check, line 403:** the test changes from `"id" not in el.attrib` to `el.attrib.get("id") is None`. Such a heading then gets the slug from `unique(self.slugify(...), used_ids, id_counters)`. Everything after this line reads the `id`: the `toc_tokens` entry, `add_anchor` and `add_permalink`. All of them now get a real string, so the `TypeError` at line 417 goes away.
- **Used-ids loop, lines 390-392:** this loop now skips `None` values, so `None` never goes into `used_ids`. Leaving it in would not break anything, but `used_ids` is typed as a set of strings (`unique(id: str, ids: MutableSet[str], ...)`).
- **Attribute order:** the slug is written to the existing `id` key in place, so the attribute keeps its position (ASSUMP-003).

**Why this fits the architecture:** the change stays inside one extension's tree processor. No registry, priority or pipeline changes are needed (ADR-1 / C1), and the core does not change (C3). The `toc` processor already owns the rule "do not override pre-existing ids", and this change only sharpens what "pre-existing" means. It works on the `ElementTree` model as ADR-3 describes.

**Rejected alternative:** changing `attr_list.assign_attrs` so it drops valueless `id`s or never sets them. The spec puts that out of scope. The `None` representation is deliberate and tested (`tests/test_syntax/extensions/test_attr_list.py:138-300`), and changing it would also change `attr_list` output when `toc` is not used (this would break AC-FR-002-04).

**Also out of scope:** a valueless `data-toc-label` (Q-002, default (a)) is not touched. The `data-toc-label` branch at lines 406-412 stays as it is.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/toc.py` | `TocTreeprocessor.run` | modify: in the used-ids loop, add `el.attrib["id"]` to `used_ids` only when it is not `None`. In the heading loop, replace `if "id" not in el.attrib:` with `if el.attrib.get("id") is None:` so a valueless id is overwritten with the unique slug. Update the comment to say a valueless id counts as no id. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add: tests for AC-FR-001-01 to AC-FR-001-05 (bare `{id}`, bare `{id}` with `[TOC]` checking the HTML and `md.toc_tokens`, slug collision giving `title_1`, `{id .cls}`, `TocExtension(permalink=True)` and `TocExtension(anchorlink=True)`) and AC-FR-002-01 / AC-FR-002-02 (explicit `{#my-id}` and no attributes, both with `toc` and `attr_list`). |
| `tests/test_syntax/extensions/test_attr_list.py` | - | add: a test that `# Title {id}` with only `attr_list` renders `<h1 id>Title</h1>` (AC-FR-002-04). Put it next to the existing valueless-attribute tests, in the same style as that test class. |
| `docs/changelog.md` | - | modify: add a bullet under `## [Unreleased]` → `### Fixed`: "Fix a `TypeError` in the `toc` extension when a heading has a valueless `{id}` attribute; a slug is now generated as if no id was given." |

## Acceptance criteria coverage

- **AC-FR-001-01** (`#d {id}` → `<h1 id="d">d</h1>`): the `el.attrib.get("id") is None` check in `TocTreeprocessor.run` assigns the slug `d`, so the `unescape` call at line 417 gets a string. Tested by the new test in `TestTOC`.
- **AC-FR-001-02** (`[TOC]` plus a bare id): the same change. The slug is stored before the `toc_tokens` entry is built, so `build_toc_div` writes `href="#some-title"` and `md.toc_tokens` holds `'id': 'some-title'`. Tested in `TestTOC`.
- **AC-FR-001-03** (collision → `title_1`): the slug goes through `unique(..., used_ids, id_counters)`. `used_ids` holds `title` from the first heading and no longer holds `None`, so the second heading gets `title_1`. Tested in `TestTOC`.
- **AC-FR-001-04** (`{id .cls}`): only the `id` value is replaced in place and `class` is left alone. Tested in `TestTOC`; the exact attribute order follows ASSUMP-003.
- **AC-FR-001-05** (permalink / anchorlink): `add_anchor` and `add_permalink` get `el.attrib["id"]`, which is now the slug `title`. Tested in `TestTOC` with both options.
- **AC-FR-002-01** (`{#my-id}` is kept): the condition is false for a non-`None` string, so the existing behaviour stays. Tested in `TestTOC`.
- **AC-FR-002-02** (no attributes): `.get("id")` returns `None` for a missing key, the same as before. Tested in `TestTOC`.
- **AC-FR-002-03** (whole suite passes): the change is minimal and only affects `None`-valued ids. Checked with `python -m unittest discover -s tests -t .`.
- **AC-FR-002-04** (only `attr_list` → `<h1 id>Title</h1>`): `attr_list.py` and the serializer do not change. Locked in by the new test in `test_attr_list.py`.

## Risks

- **Someone relying on `<h1 id>` with `toc` enabled:** the output changes from a crash to a generated slug. Before this fix that input always raised, so no working output can break.
- **Empty-string ids (`{id=""}`):** these must not change (out of scope). `.get("id") is None` is false for `""`, so they keep today's behaviour. The implementer must not use a truthiness test such as `if not el.attrib.get("id")`.
- **Slug uniqueness:** a mistake in the used-ids loop could add duplicate suffixes or drop explicit ids from `used_ids`. Guarded by the existing uniqueness and duplicate-id tests in `tests/test_syntax/extensions/test_toc.py` (`TestTOC`) and the new AC-FR-001-03 test.
- **Valueless-attribute output in `attr_list`:** this is unchanged and guarded by `tests/test_syntax/extensions/test_attr_list.py:138-300` and the new AC-FR-002-04 test.
- **Attribute order in the output (AC-FR-001-04):** this depends on serializer and attribute ordering (ASSUMP-003). If the order turns out to be different, the test should record what the code actually produces, or compare attributes without depending on order.
- **Untrusted input:** no prompt-injection content was seen in the spec.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/toc.py` / `TocTreeprocessor.run`: ok
- `tests/test_syntax/extensions/test_toc.py` / `TestTOC`: ok
- `tests/test_syntax/extensions/test_attr_list.py` / `-`: ok
- `docs/changelog.md` / `-`: ok
