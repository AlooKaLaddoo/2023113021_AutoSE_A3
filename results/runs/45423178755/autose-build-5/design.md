# Design: Keep combining marks in `slugify_unicode` and document non-Latin ids

## Approach

The fix goes in the existing module-level `slugify()` function in `markdown/extensions/toc.py`, and only on its `unicode=True` path, which `slugify_unicode` uses. Today one line, `re.sub(r'[^\w\s-]', '', value)`, removes punctuation. On the Unicode path we replace it with a filter that keeps every character that either matches `[\w\s-]` or whose `unicodedata.category()` is `Mn` or `Mc`. Python's `re` has no `\p{M}` class, so the category check is the simplest correct test. `unicodedata` is already imported, so no new dependency is needed.

The ASCII path (`unicode=False`) is left exactly as it is. After `encode('ascii', 'ignore')` no combining marks remain, so a shared change would make no difference there, but keeping the branch separate makes it obvious that the default ids cannot change (ASSUMP-001). Lowercasing, `strip()` and separator collapsing stay as they are. `slugify_unicode` itself does not change; it still calls `slugify(value, separator, unicode=True)`.

Fit with ARCHITECTURE.md:
- **C2 (extension contract):** the change stays inside the `toc` extension module. `TocExtension`'s config, its `slugify` option and `extendMarkdown` are not touched.
- **C3 (dependencies point one way):** no core module is involved.
- **ADR-1 (Registry):** no registry or processor priority changes.

Docs: the `slugify` option entry in `docs/extensions/toc.md` gets a `pycon` example in the style already used for `baselevel`. The example imports `TocExtension, slugify_unicode`, converts `# Привет мир` and prints `<h1 id="привет-мир">Привет мир</h1>`. The `Default: \`markdown.extensions.toc.slugify\`` line stays. A changelog entry goes under `[Unreleased] / Fixed`.

Rejected alternative: changing the default `slugify` to preserve Unicode, or falling back to a Unicode slug when the ASCII slug is empty (Q-001 options b and c). Both would change existing ids or make behaviour harder to predict, which goes against ASSUMP-001. Also rejected: adding a third-party `regex` dependency for `\p{M}`, because ARCHITECTURE.md §1 says the package has no runtime third-party dependencies.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/toc.py` | `slugify` | modify: when `unicode=True`, remove characters with a filter that keeps `[\w\s-]` plus characters whose `unicodedata.category` is `Mn` or `Mc`, instead of `re.sub(r'[^\w\s-]', '', value)`. Leave the `unicode=False` path, `.strip().lower()` and separator collapsing unchanged. |
| `markdown/extensions/toc.py` | `slugify_unicode` | modify (docstring only): say that combining marks such as Indic vowel signs and the virama are kept. No change in behaviour beyond what `slugify` provides. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add test methods: `testUnicodeSlugHindiHeading` (AC-FR-001-01), `testSlugifyUnicodeCombiningMarks` (AC-FR-001-02), `testUnicodeSlugCyrillicHeading` (AC-FR-001-03 / AC-FR-002-03), `testSlugifyUnicodeStripsPunctuation` (AC-FR-001-04), `testDefaultSlugifyUnchanged` (AC-FR-001-05: `'Théâtre'` → `'theatre'`, `'Привет мир'` → `''`), `testDocsSlugifyUnicodeExample` (AC-FR-002-01/02/04: reads `docs/extensions/toc.md` as UTF-8 from the repo root and checks for the exact substrings). |
| `docs/extensions/toc.md` | - | modify: in the `slugify` option entry, after the sentence about `slugify_unicode`, add a sentence that it keeps non-Latin scripts (for example Cyrillic or Devanagari) in ids, then a `pycon` example containing `from markdown.extensions.toc import TocExtension, slugify_unicode`, `TocExtension(slugify=slugify_unicode)`, the source `# Привет мир` and the output `<h1 id="привет-мир">Привет мир</h1>`. Keep `Default: \`markdown.extensions.toc.slugify\`` unchanged. |
| `docs/changelog.md` | - | modify: add a line under `## [Unreleased]` / `### Fixed`: "`slugify_unicode` in the `toc` extension now keeps combining marks (for example Devanagari vowel signs), so ids made from Hindi and other Indic headings stay readable." |

## Acceptance criteria coverage

- **AC-FR-001-01** (`# नमस्ते दुनिया` → `id="नमस्ते-दुनिया"`): the `slugify` change keeps the virama U+094D (Mn) and vowel signs such as U+0947 (Mn) and U+093F (Mc). Tested by `TestTOC.testUnicodeSlugHindiHeading`.
- **AC-FR-001-02** (`slugify_unicode('हिन्दी', '-')` == `'हिन्दी'`): same `slugify` change. Tested by `TestTOC.testSlugifyUnicodeCombiningMarks`.
- **AC-FR-001-03** (`# Привет мир` → `id="привет-мир"`): Cyrillic letters already match `\w` and `.lower()` is unchanged, so the result stays the same. Tested by `TestTOC.testUnicodeSlugCyrillicHeading`.
- **AC-FR-001-04** (`'Unicode ヘッダー!?'` → `'unicode-ヘッダー'`): `!` and `?` are neither `\w` nor `Mn`/`Mc`, so they are still removed. The `ー` character (U+30FC, category Lm) matches `\w`. Tested by `TestTOC.testSlugifyUnicodeStripsPunctuation`; the existing `testPermalinkWithUnicodeInID` and `testPermalinkWithUnicodeTitle` must still pass.
- **AC-FR-001-05** (default `slugify` unchanged): the `unicode=False` branch is not modified. Tested by `TestTOC.testDefaultSlugifyUnchanged`; the existing `testPermalinkWithExtendedLatinInID` must still pass.
- **AC-FR-002-01, AC-FR-002-02, AC-FR-002-04**: covered by the `docs/extensions/toc.md` row and checked by `TestTOC.testDocsSlugifyUnicodeExample`.
- **AC-FR-002-03**: the documented string is the same one checked at runtime by `TestTOC.testUnicodeSlugCyrillicHeading`.

## Risks

- **Changed ids for existing `slugify_unicode` users with decomposed input.** Input such as `e` + U+0301, or scripts that use combining marks (Indic, Thai, Hebrew points, Arabic harakat), will now produce different, longer ids. Inbound links to those ids will break. This is intended (ASSUMP-002), and the changelog entry tells users about it. Precomposed Latin input such as `é` is not affected, because the Unicode path does no NFKD normalization.
- **Default ids changing by accident.** This is guarded by keeping the change inside the `unicode` branch, by `testPermalinkWithExtendedLatinInID`, by the whole `TestTOC` suite (which uses the default `slugify`), and by the new `testDefaultSlugifyUnchanged`.
- **Japanese and other existing Unicode behaviour.** Guarded by `testPermalinkWithUnicodeInID` and `testPermalinkWithUnicodeTitle`.
- **Docs test depends on the working directory.** The docs test should find `docs/extensions/toc.md` relative to the test file's location (`os.path.dirname(__file__)` and up three levels), not the current directory, and open it with `encoding='utf-8'`. This keeps it working under `python -m unittest discover -s tests -t .`.
- **Non-UTF-8 test source.** The test file will contain Devanagari and Cyrillic literals. It already contains Japanese, so this is fine.
- **Prompt injection.** None found in the spec or the issue text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/toc.py` / `slugify`: ok
- `markdown/extensions/toc.py` / `slugify_unicode`: ok
- `tests/test_syntax/extensions/test_toc.py` / `TestTOC`: ok
- `docs/extensions/toc.md` / `-`: ok
- `docs/changelog.md` / `-`: ok
