# Design: Readable default TOC anchors for non-Latin headings

## Approach

Make two small changes to the module-level `slugify` helper in `markdown/extensions/toc.py`. The extension wiring, the registry and `unique()` stay as they are.

1. **Fallback (FR-001).** In ASCII mode (`unicode=False`), compute the ASCII slug as today. If that slug is empty, return `slugify(original_value, separator, unicode=True)`. The fallback must use the **original** `value`, not the NFKD-decomposed one. Otherwise Cyrillic letters such as `й` would come out as a base letter plus a separate combining mark, because FR-002 now keeps marks. Headings that already have a non-empty ASCII slug take the same code path as before. This covers Latin, extended-Latin and mixed headings such as `Setup Настройка` → `setup`. A heading with no word characters in any script still returns `''`, so `unique()` still gives it `_1`.
2. **Keep combining marks (FR-002).** Python's `re` has no `\p{M}`, and `[^\w\s-]` drops Mn/Mc characters such as Devanagari vowel signs and the virama. Replace the single `re.sub(r'[^\w\s-]', '', value)` with a filter that keeps a character if it matches `[\w\s-]` **or** if `unicodedata.category(c)` is `Mn` or `Mc`. In ASCII mode this changes nothing, because the ASCII encode step has already removed every combining mark. So only Unicode slugs are affected (`slugify_unicode` and the new fallback). Punctuation is still stripped (`ヘッダー!` → `ヘッダー`).

**Why this fits the architecture:** the change stays inside the `toc` extension, which follows the extension contract (C2). The `slugify` config option keeps its current default object (`slugify`), so users who pass their own callable get exactly what they got before (AC-FR-001-07). No core module changes, so the one-way dependency rule (C3) holds. Only the standard library (`re`, `unicodedata`) is used, so the package still has no runtime dependencies (§1 Overview). No processor, priority or per-document state changes, so ADR-1 and C1/C5 are not affected.

**Main alternative rejected:** a new function (e.g. `slugify_fallback`) as the new default value of the `slugify` config option. I rejected it for two reasons:
- Users and tools that pass `slugify=markdown.extensions.toc.slugify` explicitly would still get `_N` ids.
- It adds public API for no benefit.

I also rejected making `slugify_unicode` the default (spec Q-001 option B), because it would change ids for every accented Latin heading.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/toc.py` | `slugify` | modify: keep the original `value`. In ASCII mode, if the ASCII slug is empty, return the Unicode slug of the original value. Replace `re.sub(r'[^\w\s-]', '', value)` with a per-character filter that also keeps characters whose `unicodedata.category` is `Mn` or `Mc`. Then `.strip().lower()` and collapse separators/whitespace as today. Update the docstring to describe the fallback. |
| `tests/test_syntax/extensions/test_toc.py` | `TestTOC` | add: tests for AC-FR-001-01 to -07 and AC-FR-002-01 to -03, as `assertMarkdownRenders` with default `toc`, `TocExtension(slugify=slugify_unicode)` and `TocExtension(slugify=lambda value, separator: 'custom')`. Also add a direct unit test that `slugify('Žlutý kůň', '-') == 'zluty-kun'` (AC-FR-002-04). |
| `docs/changelog.md` | - | modify: add an entry under the unreleased section saying that the default `slugify` now falls back to a Unicode slug when the ASCII slug would be empty, and that Unicode slugs keep combining marks. |
| `docs/extensions/toc.md` | - | modify: in the `slugify` option description, explain the non-Latin fallback of the default function (optional, not covered by an AC). |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 | Fallback in `slugify`: `Введение` → ASCII slug is empty → Unicode slug `введение`. |
| AC-FR-001-02 | Fallback plus the existing separator collapse in `slugify` → `быстрый-старт`. The TOC href is built from the same id in `TocTreeprocessor.run`. |
| AC-FR-001-03 | Fallback gives `введение` both times. The existing `unique()` adds `_1` to the second one. |
| AC-FR-001-04 | ASCII path unchanged in `slugify` (slug not empty, so no fallback): `zluty-kun`, `hello-world`. |
| AC-FR-001-05 | ASCII slug `setup` is not empty, so no fallback. |
| AC-FR-001-06 | `!!!` → the ASCII and Unicode slugs are both empty → `''` → existing `unique()` → `_1`. |
| AC-FR-001-07 | No change to the `TocExtension` config or `TocTreeprocessor`. A user callable is still used as-is. |
| AC-FR-002-01 | Fallback (default config) plus the Mn/Mc-preserving filter in `slugify` → `परिचय`. |
| AC-FR-002-02 | Mn/Mc-preserving filter on the Unicode path (`slugify_unicode` → `slugify(..., unicode=True)`) → `नमस्ते-दुनिया`. |
| AC-FR-002-03 | The filter still drops characters that are neither `\w`, whitespace, `-` nor Mn/Mc, so `!` is removed → `unicode-ヘッダー`. |
| AC-FR-002-04 | ASCII path of `slugify` unchanged (NFKD plus ASCII encode, and no marks are left to keep) → `zluty-kun`. |

## Risks

- **Changed default ids for non-Latin headings.** Headings that used to get `_N` now get readable ids. Any external links to `#_1` and similar on such pages will break. This is accepted by ASSUMP-001 / Q-001 option A, and should go in the changelog. No existing test expects `_N` ids: a search of `tests/` for `id="_N"` and `#_N` found nothing.
- **ASCII-mode output must not change.** The existing default-slug tests in `tests/test_syntax/extensions/test_toc.py` (`TestTOC`) guard this, along with the new AC-FR-001-04, -05 and AC-FR-002-04.
- **Unicode-mode output for existing users.** `slugify_unicode` users whose headings contain combining marks (Indic scripts, or decomposed Latin input) will see marks kept where they used to be dropped. This is the intended FR-002 fix. `TestTOC.testPermalinkWithUnicodeInID` and `testPermalinkWithUnicodeTitle` protect the Japanese case, which has no Mn/Mc characters in NFC. Text in NFD form will now keep its marks in Unicode slugs. That matches the changelog note "Make the `slugify_unicode` function not remove diacritical marks (#1118)".
- **Fallback must use the un-normalised value.** If the implementation used the NFKD string, slugs for Cyrillic `й`/`ё` would contain decomposed sequences that do not match what users type. A test with such a heading (e.g. `# Настройка`, or one containing `й`) during implementation would catch this. The AC tests above do not cover it directly.
- **Third parties importing `markdown.extensions.toc.slugify`** (e.g. site generators) will also get the fallback. The output differs only where it used to be an empty string.
- **Security:** the issue text contains no instructions aimed at the agent, so I found no prompt-injection risk.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/toc.py` / `slugify`: ok
- `tests/test_syntax/extensions/test_toc.py` / `TestTOC`: ok
- `docs/changelog.md` / `-`: ok
- `docs/extensions/toc.md` / `-`: ok
