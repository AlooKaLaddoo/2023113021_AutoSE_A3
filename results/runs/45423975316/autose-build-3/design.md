# Design: Wikilinks piped link text `[[Page Name|link text]]` (round 2: tighten the text grammar and escape raw HTML in the text)

## Approach

Round 1 (commit `c251b62`) already gives `WIKILINK_RE` an optional second group after `|`, and makes `handleMatch` build the URL from the stripped page name. It uses the stripped text as `a.text`, or the page name when the text is empty. That covers AC-FR-001-01..07 and AC-FR-002-01..04. Two parts of the spec are still not met:

1. **The text grammar is too wide.** The text group is `(?:(?!\]\])[^\n])*`, so `[[a|b|c]]` renders as a link with text `b|c`. This breaks AC-FR-002-05 and ASSUMP-003/Q-003, which say it must stay literal. The existing test `testCustomLinkText` even asserts the wrong behaviour (`[[Page|a|b]]` → link). The text may also contain `[` and `]`, which goes against ASSUMP-001/Q-001 option (a). Fix: change the text group to `([^\[\]|\n]*)`, which means anything except `[`, `]`, `|` and newline. The page-name group stays `[\w0-9_ -]+`, so plain links match exactly as before.
2. **Raw HTML in the text is not escaped (AC-FR-001-08).** The built-in `html` inline pattern (priority 90) runs before `wikilink` (75). It moves `<docs>` into `md.htmlStash` and leaves a `STX wzxhzdk:N ETX` placeholder in its place (ADR-3). That placeholder ends up in `a.text`, and the `raw_html` postprocessor puts `<docs>` back unescaped. So `[[foo|Q&A <docs>]]` gives `Q&amp;A <docs>` instead of `Q&amp;A &lt;docs&gt;`. Fix: in `handleMatch`, replace every HTML-stash placeholder in the *text part* with its stored raw string, when that string is a `str` starting with `<` (a tag, comment, PI or CDATA captured by the `html` pattern). The serializer then escapes it as ordinary element text. This follows constraint **C4**: link text is element text, and the serializer is the one place where escaping happens. Placeholders for entities (`&amp;`, `&copy;`, which `entity` at 80 also stores through `HtmlInlineProcessor`) are left alone, so entities still render as entities. Missing or out-of-range stash keys, and non-`str` stash entries, are left untouched. The orphaned stash entry does no harm because `raw_html` only replaces placeholders that are still in the output.

The other inline Markdown in the text (ASSUMP-004) keeps working. `em_strong` (60) runs after `wikilink` and still processes `a.text`, which is not an `AtomicString`. All wiring still goes through the Registry under the same name and priority (**C1**, **ADR-1**). There are no new config options (**C2**) and no new per-document state (**C5**).

**Rejected alternative:** raise the `wikilink` priority above `html` (e.g. 95) so it sees `<docs>` before it is stashed. That would make wikilinks match *inside* raw inline HTML, e.g. `<span title="[[x]]">`, and corrupt it. That is a regression for plain links, which FR-002 forbids.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify: set `WIKILINK_RE = r'\[\[([\w0-9_ -]+)(?:\|([^\[\]\|\n]*))?\]\]'` and update the comment (group 2 = text after a single `\|`; no `[`, `]`, `\|` or newline). Registration stays `'wikilink'`, 75. |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: compute `text = self._restore_raw_html((m.group(2) or '')).strip()` before falling back to `label`. Everything else stays as it is: label strip, `build_url(label, base_url, end_url)`, `_getMeta`, class handling, `''` for an empty name. |
| `markdown/extensions/wikilinks.py` | `(new) WikiLinksInlineProcessor._restore_raw_html` | add: a method that uses `util.HTML_PLACEHOLDER_RE.sub` to replace each placeholder whose `self.md.htmlStash.rawHtmlBlocks[int(n)]` is a `str` starting with `<` with that raw string. Any other placeholder, or a missing key (`IndexError`/`ValueError`), stays as it is. Add `from .. import util` to the imports. |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkText` | modify: replace the `[[Page\|a\|b]]` assertion with `self.md.convert('[[a\|b\|c]]') == '<p>[[a\|b\|c]]</p>'` (AC-FR-002-05). Add AC-FR-001-07 (`[[foo\|double  spaces]]`) and AC-FR-001-08 (`[[foo\|Q&A <docs>]]` → `Q&amp;A &lt;docs&gt;`). |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkTextSettings` | modify: add the exact spec cases AC-FR-001-03 (`Some text with a [[WikiLink\|a link]].`), AC-FR-001-04 (`extension_configs` with `html_class: ''`), AC-FR-001-05 (meta source with `[[WikiLink\|a link]]`) and AC-FR-001-06 (`[[ foo \| some text ]]` with a recording `build_url` that returns `'/bar/'`; assert `label == 'foo'`, `base == '/'`, `end == '/'`). |
| `tests/test_extensions.py` | `(new) TestWikiLinks.testCustomLinkTextEntityAndBrackets` | add: `[[foo\|&copy; x]]` keeps the entity (`&copy; x`), and `[[foo\|a]b]]` / `[[foo\|a[b]]` produce no wikilink `<a class="wikilink"`. This guards the narrowed grammar and the "entities untouched" rule. |

## Acceptance criteria coverage

- **AC-FR-001-01, -02:** the regex group 2 and the `.strip()` of name and text in `handleMatch`. Already implemented in round 1, kept, and tested in `testCustomLinkText`.
- **AC-FR-001-03, -04, -05:** `handleMatch` still builds `href` and `class` only from `label` and `_getMeta()`. Exact spec inputs are added to `testCustomLinkTextSettings`.
- **AC-FR-001-06:** `build_url` is called with the stripped page name (group 1), never the text. Tested with a recording builder in `testCustomLinkTextSettings`.
- **AC-FR-001-07:** text is only stripped at the ends; internal spaces are kept. Test added to `testCustomLinkText`.
- **AC-FR-001-08:** the new `_restore_raw_html` turns the stashed `<docs>` back into text, so the serializer escapes it (and `&` as `&amp;`). Test added to `testCustomLinkText`.
- **AC-FR-002-01, -02:** `a.text = text or label` (round 1, kept). Tested in `testCustomLinkTextEmpty`.
- **AC-FR-002-03:** group 1 is unchanged and group 2 is optional, so plain links match and render as before. Guarded by the existing `testBasicWikilinks`, `testWikilinkWhitespace`, `testSimpleSettings`, `testComplexSettings`, `testWikilinksMetaData`, `testURLCallback` and legacy `tests/extensions/wikilinks.txt`/`.html` (via `tests/test_legacy.py`), all unmodified.
- **AC-FR-002-04:** an empty stripped group 1 still returns `''` (consumes the match, no link) → `<p>foo  bar</p>`. Already asserted in `testCustomLinkTextEmpty`.
- **AC-FR-002-05:** `|` is excluded from group 2, so `[[a|b|c]]` does not match and stays literal. Assertion corrected in `testCustomLinkText`.

## Risks

- **Narrower text grammar:** link texts containing `[`, `]` or `|` no longer render as links. This is intended (ASSUMP-001/003) but needs maintainer sign-off (Q-001, Q-003). Guarded by the new/updated tests.
- **Inline HTML in link text is now shown escaped** (e.g. `[[p|<b>x</b>]]` shows the tags as text). This follows AC-FR-001-08, which is PROVISIONAL. Entities are deliberately kept. If maintainers want raw HTML passed through instead, drop `_restore_raw_html`.
- **Stash handling:** `_restore_raw_html` only reads `htmlStash.rawHtmlBlocks`. It ignores non-`str` entries (e.g. `md_in_html` elements) and bad keys, so it cannot raise. Placeholders left over from other patterns (backtick, escape `INLINE_PLACEHOLDER`) are not touched and are resolved as before by the inline tree processor.
- **Plain-link regression:** group 1 and the priority are unchanged, and that is guarded by all the existing `TestWikiLinks` tests and the legacy wikilinks fixture. Run the full suite with `python -m unittest discover -s tests -t .`.
- **Docs:** `docs/extensions/wikilinks.md` is not changed (the spec leaves this to the maintainer). The module docstring already mentions the piped syntax.
- No prompt-injection attempt in the spec/issue text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/wikilinks.py` / `WikiLinkExtension.extendMarkdown`: ok
- `markdown/extensions/wikilinks.py` / `WikiLinksInlineProcessor.handleMatch`: ok
- `markdown/extensions/wikilinks.py` / `(new) WikiLinksInlineProcessor._restore_raw_html`: ok
- `tests/test_extensions.py` / `TestWikiLinks.testCustomLinkText`: ok
- `tests/test_extensions.py` / `TestWikiLinks.testCustomLinkTextSettings`: ok
- `tests/test_extensions.py` / `(new) TestWikiLinks.testCustomLinkTextEntityAndBrackets`: ok
