Closes #5

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45421953103)._

### Requirements (from spec.md)

- **FR-001** Preserve combining marks in slugify_unicode: The function markdown.extensions.toc.slugify_unicode SHALL keep characters of Unicode categories Mn and Mc in the generated slug, while keeping all its current behaviour for other characters (lowercasing, removal of non-word punctuation, separator collapsing).
  - `AC-FR-001-01` given Markdown source '# नमस्ते दुनिया' and extensions=[TocExtension(slugify=slugify_unicode)], when markdown.markdown is called, then Output is exactly '<h1 id="नमस्ते-दुनिया">नमस्ते दुनिया</h1>'
  - `AC-FR-001-02` given value='हिन्दी', separator='-', when slugify_unicode(value, separator) is called, then Return value is exactly 'हिन्दी'
  - `AC-FR-001-03` given Markdown source '# Привет мир' and extensions=[TocExtension(slugify=slugify_unicode)], when markdown.markdown is called, then Output is exactly '<h1 id="привет-мир">Привет мир</h1>'
  - `AC-FR-001-04` given value='Unicode ヘッダー!?', separator='-', when slugify_unicode(value, separator) is called, then Return value is exactly 'unicode-ヘッダー'; the existing tests testPermalinkWithUnicodeInID and testPermalinkWithUnicodeTitle still pass
  - `AC-FR-001-05` given value='Théâtre', separator='-' and value='Привет мир', separator='-', when markdown.extensions.toc.slugify(value, separator) is called, then Returns exactly 'theatre' and exactly '' respectively; the existing test testPermalinkWithExtendedLatinInID still passes
- **FR-002** Document a concrete non-Latin slugify_unicode example: The `slugify` option entry in docs/extensions/toc.md SHALL contain a usage example that passes slugify_unicode to TocExtension and shows the exact id produced for a Cyrillic heading.
  - `AC-FR-002-01` given The file docs/extensions/toc.md after the change, when Its text is read as UTF-8, then It contains the exact substring 'TocExtension(slugify=slugify_unicode)' and the exact substring 'from markdown.extensions.toc import TocExtension, slugify_unicode'
  - `AC-FR-002-02` given The file docs/extensions/toc.md after the change, when Its text is read as UTF-8, then It contains the exact substring '# Привет мир' and the exact substring '<h1 id="привет-мир">Привет мир</h1>'
  - `AC-FR-002-03` given Markdown source '# Привет мир' and extensions=[TocExtension(slugify=slugify_unicode)], when markdown.markdown is called, then The result equals exactly '<h1 id="привет-мир">Привет мир</h1>', the same string required in AC-FR-002-02
  - `AC-FR-002-04` given The file docs/extensions/toc.md after the change, when Its text is read as UTF-8, then It still contains the exact substring 'Default: `markdown.extensions.toc.slugify`'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/toc.py` | `slugify` | modify: when `unicode=True`, remove characters with a filter that keeps `[\w\s-]` plus characters whose `unicodedata.category` is `Mn` or `Mc`, instead of `re.sub(r'[^\w\s-]', '', value)`. Leave the `unicode=False` path, `.strip().lower()` and separator collapsing unchanged. |
| `markdown/extensions/toc.py` | `slugify_unicode` | modify (docstring only): say that combining marks such as Indic vowel signs and the virama are kept. No change in behaviour beyond what `slugify` provides. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add test methods: `testUnicodeSlugHindiHeading` (AC-FR-001-01), `testSlugifyUnicodeCombiningMarks` (AC-FR-001-02), `testUnicodeSlugCyrillicHeading` (AC-FR-001-03 / AC-FR-002-03), `testSlugifyUnicodeStripsPunctuation` (AC-FR-001-04), `testDefaultSlugifyUnchanged` (AC-FR-001-05: `'Théâtre'` → `'theatre'`, `'Привет мир'` → `''`), `testDocsSlugifyUnicodeExample` (AC-FR-002-01/02/04: reads `docs/extensions/toc.md` as UTF-8 from the repo root and checks for the exact substrings). |
| `docs/extensions/toc.md` | `-` | modify: in the `slugify` option entry, after the sentence about `slugify_unicode`, add a sentence that it keeps non-Latin scripts (for example Cyrillic or Devanagari) in ids, then a `pycon` example containing `from markdown.extensions.toc import TocExtension, slugify_unicode`, `TocExtension(slugify=slugify_unicode)`, the source `# Привет мир` and the output `<h1 id="привет-мир">Привет мир</h1>`. Keep `Default: \`markdown.extensions.toc.slugify\`` unchanged. |
| `docs/changelog.md` | `-` | modify: add a line under `## [Unreleased]` / `### Fixed`: "`slugify_unicode` in the `toc` extension now keeps combining marks (for example Devanagari vowel signs), so ids made from Hindi and other Indic headings stay readable." |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1185 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/14
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-5`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45422870432
- Result: **PASS** 
