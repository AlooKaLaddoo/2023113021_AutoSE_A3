# Design: Wikilinks piped link text: match the spec on pipes, `]` and HTML escaping

## Approach

Round 1 (commit `c251b62`) already added `[[Page Name|link text]]` support to `markdown/extensions/wikilinks.py`, with tests and docs. Two parts of it do not match the spec:

1. **Multiple pipes (ASSUMP-001, ASSUMP-004, Q-001 option a).** The current regex is `\[\[([\w0-9_ -]+)(?:\|((?:(?!\]\])[^\n])*))?\]\]`. It accepts any `|`, and a single `]`, in the link text, so `[[Page|a|b]]` currently renders a link with the text `a|b`. The test at `tests/test_extensions.py:265-268` and the docs both state this behaviour. The spec says the link text may contain anything except `|` and `]`, and that `[[A|b|c]]` must stay literal text.
   - **Fix:** change the text group to `([^|\]]*)`, giving `WIKILINK_RE = r'\[\[([\w0-9_ -]+)(?:\|([^|\]]*))?\]\]'`.
   - With a second `|`, the optional group fails, and the plain-form branch also fails because `]]` does not follow the name. The construct therefore stays literal, the same way `[[foo.bar]]` does today.
   - The page-name group is unchanged (ASSUMP-002), so input without `|` matches exactly as before (FR-002).

2. **HTML in the link text must be escaped (AC-FR-001-08).** `WikiLinksInlineProcessor` is registered at priority 75. That is below the built-in `html` (90) and `entity` (80) inline patterns, so `<docs>` in `[[Page|Q&A <docs>]]` is already in `md.htmlStash` when the wikilink pattern runs. The text group then holds an `HTML_PLACEHOLDER`, and the `raw_html` postprocessor puts back an unescaped `<docs>`.
   - **Fix:** in `handleMatch`, replace every `util.HTML_PLACEHOLDER_RE` match in the text with the matching string entry of `self.md.htmlStash.rawHtmlBlocks`. Entries that are not strings, or indexes that don't exist, are left unchanged, following the precedent of `toc.stashedHTML2text`.
   - The restored text then goes into `a.text` as ordinary text, and the serializer escapes it. This follows constraint **C4**: never put pre-rendered HTML into element text and rely on the stash. Here the text is meant to be text, so it goes into the tree and the serializer escapes it.
   - The unused stash entry is harmless, because `raw_html` only substitutes placeholders that appear in the output.

Everything else stays as it is: `build_url` gets only the stripped page name, `_getMeta` gives the per-document meta-data overrides (C5 is already satisfied by the `meta` extension's reset), and the processor keeps its name and priority in the Registry (ADR-1, C1).

**Rejected alternative:** raising the `wikilink` priority above `html` (90), for example to 95, so that it runs before raw HTML is stashed. That would change a documented priority (the `extendMarkdown` docstring table says `75`). It would also change the ordering relative to `entity` for every user, including plain `[[...]]` links, and third-party extensions that place themselves relative to 75 could break. That is more risk to FR-002 than a local change in `handleMatch`.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify: set `WIKILINK_RE` to `r'\[\[([\w0-9_ -]+)(?:\|([^|\]]*))?\]\]'` and update the comment above it (group 2 is the text after `|`; it may not contain `|` or `]`). Keep the name `wikilink` and priority 75. |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: take `text = m.group(2) or ''`, pass it through the new helper `_restore_raw_html`, then `.strip()`. Set `a.text = text or label`. Leave the label, URL, class and empty-name (`''`) branches unchanged. |
| `markdown/extensions/wikilinks.py` | `(new) WikiLinksInlineProcessor._restore_raw_html` | add: a method that returns `util.HTML_PLACEHOLDER_RE.sub(...)`. It replaces each placeholder with `self.md.htmlStash.rawHtmlBlocks[int(n)]` when that entry exists and is a `str`, and otherwise leaves the match unchanged. Add `from .. import util` (extension imports core; C3). |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkText` | modify: change the `[[Page|a|b]]` expectation to `'<p>[[Page|a|b]]</p>'` (ASSUMP-004). Add AC-FR-001-02 with double spaces (`'[[  Installation Guide  |  see the install docs  ]]'`), AC-FR-001-08 (`'[[Page|Q&A <docs>]]'` → `'<p><a class="wikilink" href="/Page/">Q&amp;A &lt;docs&gt;</a></p>'`) and AC-FR-002-04 (`'[[foo.bar]]'` stays literal). |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkTextEmpty` | modify: also assert that `'foo [[ |text]] bar'` contains no `<a` (AC-FR-001-09; the exact output `'<p>foo  bar</p>'` stays, Q-002 option a). |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkTextSettings` | modify: use the exact AC inputs and outputs. AC-FR-001-04 with `'Some text with a [[WikiLink|custom text]].'`. Add AC-FR-001-05: `extension_configs` with empty `html_class`, then `'[[WikiLink|custom text]]'`. AC-FR-001-06: the recording builder returns `'/bar/'` for `'[[ foo | some text ]]'` and records `['foo']`. AC-FR-001-07: add the second conversion `'No [[MetaData|here]] now.'` → `'<p>No <a class="wikilink" href="/MetaData/">here</a> now.</p>'`. |
| `docs/extensions/wikilinks.md` | - | modify: replace "Only the first `|` separates … any later `|` is part of the link text. The link text cannot contain `]]` or a line break" with: the link text cannot contain `|` or `]`, and input with more than one `|` is left as literal text. Add that HTML characters in the link text are shown literally (escaped). Keep the note about tables. |
| `docs/changelog.md` | - | modify: adjust the existing wikilinks entry (line 19) only if its wording mentions multiple pipes; otherwise leave it unchanged. |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 | Regex group 2 plus `handleMatch` (`a.text = text`). Tested in `testCustomLinkText`. |
| AC-FR-001-02 | `.strip()` on the label and the text in `handleMatch`. Spaces are in the name character set, and `[^|\]]` allows them in the text. Tested in `testCustomLinkText`. |
| AC-FR-001-03 | `a.text = text or label` after stripping. Tested in `testCustomLinkTextEmpty`. |
| AC-FR-001-04 | URL from `build_url(label, base_url, end_url)` and class from `_getMeta`, both unchanged. Tested in `testCustomLinkTextSettings`. |
| AC-FR-001-05 | The `if html_class:` guard in `handleMatch`. New assertion in `testCustomLinkTextSettings`. |
| AC-FR-001-06 | `build_url` receives `m.group(1).strip()` only. Tested in `testCustomLinkTextSettings`. |
| AC-FR-001-07 | `_getMeta` reads `md.Meta`, which `meta` resets per document. Tested in `testCustomLinkTextSettings` (both documents). |
| AC-FR-001-08 | `_restore_raw_html` in `handleMatch`, then serializer escaping. Tested in `testCustomLinkText`. |
| AC-FR-001-09 | The empty-name branch returns `''` (Q-002 option a, consistent with `[[ ]]`). Tested in `testCustomLinkTextEmpty`. |
| AC-FR-002-01 | Page-name group and plain-form logic unchanged. Covered by `testBasicWikilinks`. |
| AC-FR-002-02 | Same as AC-FR-002-01. Covered by `testWikilinkWhitespace`. |
| AC-FR-002-03 | No existing `TestWikiLinks` test before `testCustomLinkText` is edited. Run the full suite. |
| AC-FR-002-04 | `.` is not in the name character set, and there is no `|` branch to fall into. New assertion in `testCustomLinkText`. |

## Risks

- **Behaviour change from round 1:** `[[A|b|c]]` and text containing a single `]` (e.g. `[[Page|a]b]]`) are now literal instead of links. This is intended (ASSUMP-001, ASSUMP-004). Guarded by the updated `testCustomLinkText`.
- **Placeholder restoration is wider than AC-08.** Entities such as `[[Page|&copy;]]` are stashed by `entity` (80) and would now come out as `&amp;copy;` (shown literally) rather than as ©. This fits "link text is plain text" and Q-003, but it is a visible change; it should be mentioned in the docs and the PR. Placeholders from inline patterns with higher priority (`klzzwxh`: links, autolinks, code spans, escapes) are left alone, so inline Markdown in the text keeps today's unspecified behaviour (Q-003).
- **Coupling to `HtmlStash` internals** (`rawHtmlBlocks`, `HTML_PLACEHOLDER_RE`). `toc.py` and `md_in_html.py` already use the same pattern. Non-`str` entries and indexes that don't exist are skipped. Guarded by the AC-08 test and the full suite.
- **Text may now span lines,** since `[^|\]]` allows `\n` where the old regex excluded it. Inline patterns already work on multi-line paragraph text, and no existing test relies on the old exclusion. The docs sentence about line breaks will be removed.
- **Plain wikilinks (FR-002):** the page-name group, the priority and the plain branch are unchanged. Guarded by `testBasicWikilinks`, `testWikilinkWhitespace`, `testSimpleSettings`, `testComplexSettings`, `testWikilinksMetaData` and `testURLCallback`.
- **Prompt injection:** none found in the spec text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/wikilinks.py` / `WikiLinkExtension.extendMarkdown`: ok
- `markdown/extensions/wikilinks.py` / `WikiLinksInlineProcessor.handleMatch`: ok
- `markdown/extensions/wikilinks.py` / `(new) WikiLinksInlineProcessor._restore_raw_html`: ok
- `tests/test_extensions.py` / `TestWikiLinks.testCustomLinkText`: ok
- `tests/test_extensions.py` / `TestWikiLinks.testCustomLinkTextEmpty`: ok
- `tests/test_extensions.py` / `TestWikiLinks.testCustomLinkTextSettings`: ok
- `docs/extensions/wikilinks.md` / `-`: ok
- `docs/changelog.md` / `-`: ok
