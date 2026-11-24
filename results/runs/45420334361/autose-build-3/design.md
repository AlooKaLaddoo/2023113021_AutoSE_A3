# Design: Wikilinks custom link text with `[[Page Name|link text]]`

## Approach

Add an optional `|link text` group to the wikilink regex. Then extend `WikiLinksInlineProcessor.handleMatch` so that it:

- builds the URL from the stripped page name only, through the same `build_url` / `_getMeta()` path as today;
- uses the stripped link text as `a.text`, or falls back to the page name when the link text is missing, empty or only whitespace.

The extension keeps the same registry entry: one inline processor named `wikilink` at priority 75. So this follows C1 (change the pipeline only through the Registry API) and C2 (the extension contract: no new config options, wiring stays in `extendMarkdown`). It also follows ADR-3 and C4. The link text is plain element text, so the serializer escapes it (`a & b` becomes `a &amp; b`, AC-FR-001-07). No pre-rendered HTML is put into the tree.

New regex, set in `WikiLinkExtension.extendMarkdown`:

```
\[\[([\w0-9_ -]+)(?:\|((?:(?!\]\])[^\n])*))?\]\]
```

- Group 1 is the page name. Its character class is the same as today (ASSUMP-001), so plain `[[...]]` matching does not change.
- Group 2 is the optional link text. It ends at the first `]]` and cannot contain a newline (ASSUMP-002). It uses `[^\n]` instead of `.` because `InlineProcessor` compiles patterns with `re.DOTALL` (`markdown/inlinepatterns.py:274`).
- `|` is not in the group 1 class, so the first `|` is always the separator. Later `|` characters belong to group 2 (`[[Page|a|b]]` gives the text `a|b`, ASSUMP-003).

In `handleMatch`, the existing `if m.group(1).strip():` guard stays. When the page name is empty, it returns `''` whatever the link text is (ASSUMP-004). This keeps the `[[ ]]` case, and `[[ |text]]` behaves the same way. `build_url` is called exactly once, with the stripped page name.

The link text keeps the same inline handling that labels have today: a plain `str`, not wrapped in `AtomicString` (Q-001, option a). The page-name fallback therefore renders exactly as before.

**Rejected alternative:** register a second inline processor, for example `wikilink_text` at priority 76, just for the piped form. It would duplicate the URL, meta-data and class logic. It would add a new registry name that users who replace or deregister `wikilink` would miss. It would also give two patterns that compete for the same `[[` prefix. Extending the one processor keeps a single source of truth for how URLs are built.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify `WIKILINK_RE` to `\[\[([\w0-9_ -]+)(?:\|((?:(?!\]\])[^\n])*))?\]\]`. Add an optional group 2 for the link text after the first `\|` (no `]]`, no newline). The registration name `wikilink` and priority 75 stay the same. |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: keep the `m.group(1).strip()` guard (an empty page name returns `''`). Compute `label = m.group(1).strip()` and pass only `label` to `self.config['build_url'](label, base_url, end_url)`. Compute `text = (m.group(2) or '').strip()` and set `a.text = text or label`. The `href`/`class` handling and `_getMeta()` stay unchanged. |
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension` | modify the module docstring / header comment only if needed to mention the `[[Page|text]]` form. Nothing else changes in this class. |
| `tests/test_extensions.py` | `TestWikiLinks` | add test methods for AC-FR-001-01 to -07 and AC-FR-002-01, -02, -04 (with a `[[ ]]` regression check) and -05. Leave every existing test unmodified. |
| `docs/extensions/wikilinks.md` | - | modify the "Syntax" section to describe `[[Page Name|link text]]`. Cover: the URL is built from the page name only; surrounding whitespace is stripped; empty text falls back to the page name; only the first `\|` separates; link text cannot contain `]]` or a newline; known limitation inside pipe tables (Q-004). Add an `md-render` example. |
| `docs/changelog.md` | - | add an entry under `## [Unreleased]` for wikilink custom link text, in a new `### Changed` subsection. |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 | New regex group 2 matches `\|see the install docs`. `handleMatch` sets `a.text` to the stripped text, and the `href` comes from `build_url('Installation Guide', '/', '/')`, which gives `/Installation_Guide/`. |
| AC-FR-001-02 | `handleMatch` strips both `m.group(1)` and `m.group(2)`. Spaces before `\|` are in group 1's class (`[\w0-9_ -]`), so they are captured and then stripped. |
| AC-FR-001-03 | `handleMatch` keeps the `_getMeta()` / `build_url` / `html_class` path and passes it only the page name. |
| AC-FR-001-04 | `handleMatch` calls `self.config['build_url']` exactly once, with `label` (the page name). The link text is never passed to it. |
| AC-FR-001-05 | `_getMeta()` is unchanged and still reads the `wiki_base_url` / `wiki_end_url` / `wiki_html_class` meta-data. The empty `wiki_html_class` means no `class` attribute, as today. |
| AC-FR-001-06 | Regex: `\|` is excluded from group 1, so the first `\|` separates. Group 2 allows `\|`, so the text is `a\|b`. |
| AC-FR-001-07 | Link text is plain element text, which the serializer escapes (ADR-3 / C4). The `entity` pattern (80) does not match a bare `&`. |
| AC-FR-002-01 | `text = ''`, so `a.text = label`, which is `Installation Guide`. |
| AC-FR-002-02 | Whitespace-only group 2 strips to `''`, so the text falls back to the stripped page name. |
| AC-FR-002-03 | Group 2 is optional (`(?:...)?`), so `[[WikiLink]]` and `[[ foo bar_baz ]]` match as before. With `m.group(2)` as `None`, `a.text = label`. Existing `TestWikiLinks` tests and `tests/extensions/wikilinks.txt` guard this. |
| AC-FR-002-04 | `[[ ]]` still matches (group 1 is a space). The unchanged `m.group(1).strip()` guard returns `''`. |
| AC-FR-002-05 | `[[ \|text]]`: group 1 is a space, so the same guard returns `''` and no `<a>` is created. |

## Risks

- **The extension is in maintenance mode.** `docs/extensions/wikilinks.md:16-24` says "no new features or changes in behavior will be made". This change is a new feature, so a maintainer may reject it on policy grounds even if the code is correct. The reviewer or PR description should point this out.
- **Plain-link regressions.** Group 1 is unchanged, and group 2 is optional and only follows a literal `\|`. Existing inputs never contained `\|` because it was outside the old character class, so any input that matched before still matches the same way. This is guarded by `tests/test_extensions.py::TestWikiLinks` (lines 158-253) and the legacy `tests/extensions/wikilinks.txt` / `wikilinks.html` test.
- **Higher-priority inline patterns run first.** `wikilink` is at 75, after `link` (160), `autolink`, `html` (90), `entity` (80) and others. Link text containing `[x](y)`, `<tag>` or backslash escapes is changed by those patterns before the wikilink regex sees it. For example, raw HTML becomes stash placeholders inside the link text, or an inner `[x](y)` becomes a nested element, and the wikilink then may not match. This is outside the ACs, which use plain text and `&`. The docs should say link text is intended to be plain text.
- **Inline Markdown in link text.** The link text is not an `AtomicString`, the same as labels today (Q-001, option a). So lower-priority patterns such as `em_strong` (60) can still format it, e.g. `*x*` becomes `<em>`. Wrapping it in `AtomicString` was not chosen, because the page-name fallback must render exactly as it does today (AC-FR-002-03).
- **Pipe tables (Q-004).** Inside `tables`, `\|` splits cells before inline processing, so `[[a\|b]]` in a cell breaks apart. This is a known limitation, to be documented. It is not a regression, because the form did not work before either.
- **Prompt injection.** The spec and issue text contained no instructions aimed at the pipeline, so I found no injection attempt.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/wikilinks.py` / `WikiLinkExtension.extendMarkdown`: ok
- `markdown/extensions/wikilinks.py` / `WikiLinksInlineProcessor.handleMatch`: ok
- `markdown/extensions/wikilinks.py` / `WikiLinkExtension`: ok
- `tests/test_extensions.py` / `TestWikiLinks`: ok
- `docs/extensions/wikilinks.md` / `-`: ok
- `docs/changelog.md` / `-`: ok
