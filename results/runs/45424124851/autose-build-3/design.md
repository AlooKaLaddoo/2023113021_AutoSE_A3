# Design: Wikilinks piped link text `[[Page Name|link text]]`

## Approach

Change one regex and one method in the `wikilinks` extension. Nothing in the pipeline changes.

1. **Extend the pattern.** In `WikiLinkExtension.extendMarkdown`, `WIKILINK_RE` gets an optional second group after a single `|`:
   `r'\[\[([\w0-9_ -]+)(?:\|([^\[\]|\n]*))?\]\]'`
   - Group 1 is the page name. Its character set stays the same, so plain links are unaffected (out of scope to change).
   - Group 2 is the link text. It is "anything except `[`, `]`, `|` and newline" (ASSUMP-001 / Q-001 option a).
   - Group 2 cannot contain `|`, so `[[a|b|c]]` fails to match and stays literal text (ASSUMP-003).
   - Neither class overlaps with `|`, and the optional group is anchored by `]]`, so there is no quadratic backtracking.
2. **Use the link text in `WikiLinksInlineProcessor.handleMatch`.**
   - The guard and `label` stay based on `m.group(1).strip()`. An empty page name still returns `''` (ASSUMP-002).
   - The URL is still `self.config['build_url'](label, base_url, end_url)`, with `base_url`, `end_url` and `html_class` from `_getMeta()`. So `href`, `class`, a custom `build_url` and the `wiki_*` meta-data overrides all come from the page name only (ASSUMP-005: same signature).
   - Only `a.text` changes: `text = (m.group(2) or '').strip()`, then `a.text = text or label`. Empty or whitespace-only text, or a missing pipe, falls back to the page name.
3. **Docs.** Describe the syntax in `docs/extensions/wikilinks.md` and add an entry to `docs/changelog.md` under `[Unreleased]` in a new `### Changed` section, following the existing Keep-a-Changelog layout.

**Why this fits the architecture:**
- It stays inside the extension contract (C2) and keeps the existing registration through the Registry API: name `wikilink`, priority 75 (C1, ADR-1). No new processor, priority or config option is needed.
- The core doesn't change (C3).
- The link text goes into the element as plain `a.text`, which the serializer escapes. That is the channel C4 / ADR-3 prescribes, so punctuation such as `&` or `<` is escaped correctly.
- Link text is not an `AtomicString`, so inline patterns with lower priority (e.g. `em_strong`, 60) still process it, the same as plain labels today (ASSUMP-004).

**Rejected alternative:** a separate inline processor for piped links, registered next to `wikilink`. It would copy the URL, class and meta logic (`_getMeta`), add a second priority to keep in sync, and risk piped and plain links drifting apart. FR-001 requires them to be identical.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify `WIKILINK_RE` to `r'\[\[([\w0-9_ -]+)(?:\|([^\[\]\|\n]*))?\]\]'`: optional `\|` followed by a link-text group that excludes `[`, `]`, `\|` and newline; page-name group unchanged; registration (`wikilink`, 75) unchanged |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: keep URL/class building from stripped group 1 via `build_url` and `_getMeta()`; set `a.text` to stripped group 2, falling back to the page name when group 2 is missing, empty or whitespace-only; empty page name still returns `''` |
| `markdown/extensions/wikilinks.py` | `(new) ` none; module docstring only if needed | modify: no new symbols |
| `tests/test_extensions.py` | `TestWikiLinks` | add test methods for AC-FR-001-01..07 and AC-FR-002-01..04 (piped basic, whitespace, simple settings, custom `build_url` argument capture, meta-data overrides, punctuation, multiple pipes, empty/whitespace text fallback, empty page name); existing methods unchanged |
| `docs/extensions/wikilinks.md` | - | modify: document `[[Page Name\|link text]]`, that URL/class come from the page name, whitespace stripping, fallback to the page name for empty text, and that extra pipes are not supported |
| `docs/changelog.md` | - | modify: add a `### Changed` entry under `## [Unreleased]`: "The `wikilinks` extension supports custom link text with `[[Page Name\|link text]]`." |

## Acceptance criteria coverage

- **AC-FR-001-01** (basic piped link): the new `WIKILINK_RE` matches. `handleMatch` builds `/Installation_Guide/` from group 1 and sets the text from group 2.
- **AC-FR-001-02** (whitespace around name and text): the `.strip()` on group 1 (existing) and on group 2 (new) in `handleMatch`. The leading spaces in the page name are already in its character set.
- **AC-FR-001-03** (`base_url`, `end_url`, `html_class` settings): the unchanged `_getMeta()` / `build_url` path in `handleMatch`, fed by group 1.
- **AC-FR-001-04** (custom `build_url` gets the page name): `handleMatch` passes `label` (stripped group 1), never the link text, to `self.config['build_url']`.
- **AC-FR-001-05** (`wiki_*` meta-data overrides): the unchanged `_getMeta()` call in `handleMatch`. An empty `wiki_html_class` still means no `class` attribute.
- **AC-FR-001-06** (punctuation in link text): the link-text class `[^\[\]|\n]` in `WIKILINK_RE` allows `,`, `.` and `!`.
- **AC-FR-001-07** (`[[a|b|c]]` stays literal): the link-text class excludes `|`, so the closing `]]` cannot be reached and there is no match.
- **AC-FR-002-01** (empty link text): group 2 is `''`, so `a.text` falls back to `label`.
- **AC-FR-002-02** (whitespace-only link text): group 2 strips to `''`, so it falls back to the stripped `label`.
- **AC-FR-002-03** (plain links unchanged): group 2 is `None`, so `a.text = label`, and the page-name group and the rest of the logic are unchanged. Guarded by the existing `TestWikiLinks` tests and `tests/extensions/wikilinks.txt`/`.html`.
- **AC-FR-002-04** (empty page name): the existing guard `if m.group(1).strip()` applies to both `[[ |some text]]` and `[[ ]]`, giving `''` and so `<p>foo  bar</p>`.
- The new tests in `TestWikiLinks` check each AC above.

## Risks

- **Plain wikilinks regress through the regex change.** The page-name group is unchanged and the new group is optional. Guards: `TestWikiLinks.testBasicWikilinks`, `testWikilinkWhitespace`, `testSimpleSettings`, `testComplexSettings`, `testWikilinksMetaData`, `testURLCallback`, and the legacy `tests/extensions/wikilinks.txt` → `wikilinks.html` (which includes the emphasis-inside-label case for ASSUMP-004).
- **Text that wasn't a link before now becomes one.** Example: `[[foo|bar]]` written as literal text, or an earlier short-reference interaction with `[foo|bar]`. This change in behaviour is intended. Patterns with higher priority (`link` 160, `reference` 170, `short_reference` 130) still run before `wikilink` (75), so their interaction with `[[...]]` is the same as for plain wikilinks today.
- **Placeholders from earlier inline patterns inside the link text.** The `escape` pattern (180) turns backslash escapes such as `\]` into `STX`/`ETX` placeholders. The `unescape` tree processor restores these inside `a.text`, so they render correctly. `[`, `]`, `|` and newline are still excluded.
- **Regex performance.** The page-name and link-text classes are disjoint around `|`, and `]]` is a fixed terminator, so matching is linear. No new ReDoS risk.
- **Security.** The link text is plain element text, so the serializer escapes it (C4). It cannot inject HTML. The issue text contained no instructions aimed at the pipeline.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/wikilinks.py` / `WikiLinkExtension.extendMarkdown`: ok
- `markdown/extensions/wikilinks.py` / `WikiLinksInlineProcessor.handleMatch`: ok
- `markdown/extensions/wikilinks.py` / `(new) ` none; module docstring only if needed`: ok
- `tests/test_extensions.py` / `TestWikiLinks`: ok
- `docs/extensions/wikilinks.md` / `-`: ok
- `docs/changelog.md` / `-`: ok
