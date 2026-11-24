Closes #5

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45424136585)._

### Requirements (from spec.md)

- **FR-001** Produce readable default anchors for non-Latin headings: With the default `slugify` option, the toc extension SHALL use a slug that keeps the heading's Unicode word characters (lower-cased, whitespace replaced by the separator) whenever the ASCII-only slug would be empty, and SHALL keep the current ASCII slug in every other case.
  - `AC-FR-001-01` given Markdown source '# Введение' and extensions=['toc'] with default config, when markdown.markdown is called, then Output is exactly '<h1 id="введение">Введение</h1>'
  - `AC-FR-001-02` given Markdown source '[TOC]

# Быстрый старт' and extensions=['toc'], when markdown.markdown is called, then Output contains '<h1 id="быстрый-старт">Быстрый старт</h1>' and '<a href="#быстрый-старт">Быстрый старт</a>'
  - `AC-FR-001-03` given Markdown source '# Введение

# Введение' and extensions=['toc'], when markdown.markdown is called, then Output is exactly '<h1 id="введение">Введение</h1>
<h1 id="введение_1">Введение</h1>'
  - `AC-FR-001-04` given Markdown source '# Žlutý kůň

# Hello World' and extensions=['toc'], when markdown.markdown is called, then Output is exactly '<h1 id="zluty-kun">Žlutý kůň</h1>
<h1 id="hello-world">Hello World</h1>'
  - `AC-FR-001-05` given Markdown source '# Setup Настройка' and extensions=['toc'], when markdown.markdown is called, then Output is exactly '<h1 id="setup">Setup Настройка</h1>'
  - `AC-FR-001-06` given Markdown source '# !!!' and extensions=['toc'], when markdown.markdown is called, then Output is exactly '<h1 id="_1">!!!</h1>'
  - `AC-FR-001-07` given Markdown source '# Введение' and extensions=[TocExtension(slugify=lambda value, separator: 'custom')], when markdown.markdown is called, then Output is exactly '<h1 id="custom">Введение</h1>'
- **FR-002** Preserve combining marks in Unicode slugs: When the toc extension produces a Unicode slug (via `slugify_unicode` or the FR-001 fallback), it SHALL keep Unicode combining marks (general categories Mn and Mc) that occur in the heading text, so that words in scripts such as Devanagari are not altered.
  - `AC-FR-002-01` given Markdown source '# परिचय' and extensions=['toc'], when markdown.markdown is called, then Output is exactly '<h1 id="परिचय">परिचय</h1>'
  - `AC-FR-002-02` given Markdown source '# नमस्ते दुनिया' and extensions=[TocExtension(slugify=slugify_unicode)], when markdown.markdown is called, then Output is exactly '<h1 id="नमस्ते-दुनिया">नमस्ते दुनिया</h1>'
  - `AC-FR-002-03` given Markdown source '# Unicode ヘッダー!' and extensions=[TocExtension(slugify=slugify_unicode)], when markdown.markdown is called, then Output is exactly '<h1 id="unicode-ヘッダー">Unicode ヘッダー!</h1>'
  - `AC-FR-002-04` given The function call slugify('Žlutý kůň', '-'), when It is evaluated, then It returns 'zluty-kun'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/toc.py` | `slugify` | modify: keep the original `value`. In ASCII mode, if the ASCII slug is empty, return the Unicode slug of the original value. Replace `re.sub(r'[^\w\s-]', '', value)` with a per-character filter that also keeps characters whose `unicodedata.category` is `Mn` or `Mc`. Then `.strip().lower()` and collapse separators/whitespace as today. Update the docstring to describe the fallback. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add: tests for AC-FR-001-01 to -07 and AC-FR-002-01 to -03, as `assertMarkdownRenders` with default `toc`, `TocExtension(slugify=slugify_unicode)` and `TocExtension(slugify=lambda value, separator: 'custom')`. Also add a direct unit test that `slugify('Žlutý kůň', '-') == 'zluty-kun'` (AC-FR-002-04). |
| `docs/changelog.md` | `-` | modify: add an entry under the unreleased section saying that the default `slugify` now falls back to a Unicode slug when the ASCII slug would be empty, and that Unicode slugs keep combining marks. |
| `docs/extensions/toc.md` | `-` | modify: in the `slugify` option description, explain the non-Latin fallback of the default function (optional, not covered by an AC). |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1183 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/20
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-5-e2_implementer_writes_tests`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45425127841
- Result: **PASS** 
