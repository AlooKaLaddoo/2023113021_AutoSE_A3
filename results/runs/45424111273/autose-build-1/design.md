# Design: Generate a TOC slug for headings with a valueless `id` attribute

## Approach

The fix goes in `TocTreeprocessor.run` (`markdown/extensions/toc.py`). The check at line 403, "Do not override pre-existing ids", currently tests whether the `id` key exists. It will test the key's value instead: if `el.attrib.get("id")` is falsy (`None` or `""`), `toc` gives the heading the slug it would have generated anyway, using `unique(self.slugify(...), used_ids, id_counters)`. That assignment overwrites the bare `id` (ASSUMP-002), and lines 417, 424 and 426 then receive a real string. The first loop in `run` that fills `used_ids` (lines 390-392) will also skip falsy id values. Without that, `None` or `""` would end up in the set of used ids. Nothing breaks today because of this, but those values are never real ids, so they don't belong there.

Why this fits the architecture:
- The change stays inside the extension that reads the attribute. Per C3 (dependencies point one way) and C1, no core module or registry changes. Priorities stay the same: `attr_list` (8) still runs before `toc` (5).
- The `attr_list` contract stays as it is (spec ASSUMP-003, Q-002). Valueless attributes keep `None` values, so the `download` case (AC-FR-001-08) and the existing `attr_list` tests are unaffected.
- No new per-document state is added, so C5 is unaffected.

Rejected alternative: changing `AttrListTreeprocessor.assign_attrs` to drop or skip a valueless `id`. That would also change how `attr_list` renders on its own (`<h1 id>`), which is out of scope (Q-002). It would also put knowledge of `toc` into `attr_list`, and it would miss empty or `None` ids set by other extensions (ASSUMP-001).

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| markdown/extensions/toc.py | TocTreeprocessor.run | modify: when collecting `used_ids`, add only truthy `el.attrib.get("id")` values. Change the "pre-existing ids" check from `"id" not in el.attrib` to `not el.attrib.get("id")`, so a `None` or `""` id is replaced with `unique(self.slugify(html.unescape(name), self.sep), used_ids, id_counters)`. Update the comment to say valueless ids count as absent. |
| tests/test_syntax/extensions/test_toc.py | (new) TestTocValuelessId | add: a `TestCase` with one test for each of AC-FR-001-01 to AC-FR-001-08, using `extensions=['toc', 'attr_list']` or `['attr_list', TocExtension(permalink=True / anchorlink=True)]`. Includes a `Markdown` instance check of `md.toc_tokens`. |
| docs/changelog.md | - | add: an entry under `## [Unreleased]` → `### Fixed`: "Fix `TypeError` in `toc` when a heading has a bare (valueless) `{id}` attribute from `attr_list`; a slug is now generated." |

## Acceptance criteria coverage

- **AC-FR-001-01** (`#d {id}` → `<h1 id="d">d</h1>`): the new check in `TocTreeprocessor.run` sees `None` and assigns the slug `d`. Line 417 then gets a string. Overwriting the existing `id` key keeps its position in the attribute order. Test in `TestTocValuelessId`.
- **AC-FR-001-02** (with `[TOC]`): same change. `toc_tokens` now has the id `header-1`, so `build_toc_div` writes `href="#header-1"` and `replace_marker` inserts the div.
- **AC-FR-001-03** (`md.toc_tokens[0]['id'] == 'header-1'`): same change. The token is built from the generated `el.attrib["id"]`.
- **AC-FR-001-04** (`title` / `title_1`): the generated id goes through `unique(..., used_ids, id_counters)`. The first heading already took `title`, so the second gets `title_1`. Leaving `None` out of `used_ids` keeps the set limited to real ids.
- **AC-FR-001-05** (permalink): `add_permalink(el, el.attrib["id"])` now gets `header-1`.
- **AC-FR-001-06** (anchorlink): `add_anchor(el, el.attrib["id"])` now gets `header-1`, which gives `<a class="toclink" href="#header-1">`.
- **AC-FR-001-07** (explicit ids kept): `my-id` is truthy, so the new check doesn't override it. The behaviour is unchanged, and a regression test is added.
- **AC-FR-001-08** (`{download}` kept): `attr_list` is unchanged, so `download=None` stays and is set first. `toc` adds `id` after it, which gives `<h1 download id="heading">`. A regression test is added.

## Risks

- **An explicit id that is empty (`id=""`, e.g. from `{id=""}` or another extension) is now replaced with a slug.** Before, `toc` kept `""`, which meant `href="#"` and an anchor that goes nowhere. This is intended (ASSUMP-001, Q-001). Existing tests guard explicit non-empty ids: the toc tests in `tests/test_syntax/extensions/test_toc.py` (for example the ones for existing ids and `attr_list` together) and `tests/test_extensions.py` (`TestTOC`).
- **Uniqueness and counter behaviour.** Leaving falsy ids out of `used_ids` only removes `None` or `""` from the set. The suffixes that `unique` produces for real ids stay the same. The existing uniqueness tests in `test_toc.py` (repeated headings, `_1`/`_2` suffixes) guard this.
- **Attribute order in the output.** Reassigning an existing key keeps its position in the dict, and new keys are added at the end, as before. The exact-HTML assertions in `test_toc.py` and `tests/test_syntax/extensions/test_attr_list.py` guard this.
- **Not covered: a bare `{data-toc-label}` still crashes** at `toc.py:408` (Q-003, out of scope by the spec). It's worth filing as a separate issue.
- The spec contains no instructions aimed at the pipeline, so there is no injection risk to report.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/toc.py` / `TocTreeprocessor.run`: ok
- `tests/test_syntax/extensions/test_toc.py` / `(new) TestTocValuelessId`: ok
- `docs/changelog.md` / `-`: ok
