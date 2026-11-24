# Design: Built-in `strikethrough` extension (`~~text~~` → `<del>`)

## Approach

Add a new built-in extension module, `markdown/extensions/strikethrough.py`. It follows the extension contract in **C2**: it subclasses `Extension`, does all of its wiring in `extendMarkdown(md)`, provides a module-level `makeExtension(**kwargs)`, and is registered as the `strikethrough` entry point in `pyproject.toml` (**ADR-2**). That entry point is what makes `extensions=['strikethrough']` work. The dotted path `markdown.extensions.strikethrough` works through the `makeExtension` fallback in `Markdown.build_extension`.

`extendMarkdown` makes two changes, both through instance APIs only (**C1**). It does not edit `build_inlinepatterns` or core, which keeps the default behaviour the same (**C3**):

1. It registers `SimpleTagInlineProcessor(STRIKE_RE, 'del')` in `md.inlinePatterns` under the name `'strikethrough'` at priority **65**. That is below `entity` (80) and above `em_strong` (60), as listed in ARCHITECTURE.md §1 under **ADR-1**. The pattern is:
   `STRIKE_RE = r'(?<!~)(~~)(?![\s~])(.+?)(?<![\s~])~~(?!~)'`
   Group 2 is the struck text, which is what `SimpleTagInlineProcessor.handleMatch` puts into the element.
   - **Only a run of exactly two tildes counts** (ASSUMP-003). The `(?<!~)` and `(?!~)` checks around the tildes mean `~~~foo~~~` and `~` never match.
   - **No whitespace inside the delimiters** (ASSUMP-002). The opening `~~` must not be followed by whitespace and the closing `~~` must not be preceded by it. There is no word-boundary check, so intraword `a~~b~~c` is allowed. This is the same as the "dumb" `*` flanking rules in `Delimiter._build_patterns`.
   - **Spans are as short as possible.** The lazy `.+?` makes `~~one~~ and ~~two~~` produce two spans.
   - **An unclosed `~~` does not match.**
2. If `'~'` is not already in `md.ESCAPED_CHARS`, it appends `'~'`. This follows the `tables` precedent (`markdown/extensions/tables.py:248-249`, ASSUMP-004). The `escape` pattern (180) runs first, so `\~` becomes a placeholder that `~~` cannot match. The `unescape` treeprocessor then turns it back into `~`. `ESCAPED_CHARS` belongs to each `Markdown` instance, so other instances are not affected.

**How nesting works.** `treeprocessors.InlineProcessor` runs a new element's text only through patterns with a *lower* priority (`patternIndex + 1`, `markdown/treeprocessors.py:315`). The order of each pattern relative to 65 gives the required results:

- **Strong and emphasis inside `<del>` are rendered.** `em_strong` (60) runs after `<del>` is created, so it still processes the struck text.
- **Links inside `<del>` are rendered.** Links (160) and code spans (`backtick`, 190) are turned into placeholders before 65 runs. The `<del>` element simply contains those placeholders.
- **`<del>` inside `<em>` is rendered** (`*a ~~b~~ c*`). The `<del>` placeholder is created first, then `em_strong` wraps it.
- **Code spans are left alone.** `` `~~code~~` `` is already an `AtomicString` code element before 65 runs.

**Alternative rejected:** registering `~` in the shared `DelimiterProcessor` with `md.delimiters.add('~', 'del', double=True)`, as `legacy_em` does for `_`. That handler keeps one set of state for all delimiters. Its pairing loop checks the stacks of the *other* delimiters (`any(d.stack ...)`, `markdown/inlinepatterns.py:931,961`), so adding `~` could change how `*` and `_` pair (RISK-001). It would also turn `~~~foo~~~` into `~<del>foo</del>~`, which breaks AC-FR-003-04. A standalone, self-contained regex processor at its own priority does not touch the emphasis code at all.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| markdown/extensions/strikethrough.py | (new) STRIKE_RE | new: module-level regex `r'(?<!~)(~~)(?![\s~])(.+?)(?<![\s~])~~(?!~)'`; group 2 is the content |
| markdown/extensions/strikethrough.py | (new) StrikethroughExtension | new: `Extension` subclass with no config options. `extendMarkdown(md)` registers `SimpleTagInlineProcessor(STRIKE_RE, 'del')` as `'strikethrough'` at priority 65 and appends `'~'` to `md.ESCAPED_CHARS` if it is missing. The docstring includes a registry table like `legacy_em.py`. Includes the module header and docstring in the style of the other built-ins. |
| markdown/extensions/strikethrough.py | (new) makeExtension | new: `return StrikethroughExtension(**kwargs)` |
| pyproject.toml | - | add: `strikethrough = 'markdown.extensions.strikethrough:StrikethroughExtension'` under `[project.entry-points.'markdown.extensions']` |
| tests/test_syntax/extensions/test_strikethrough.py | (new) TestStrikethrough | new: `markdown.test_tools.TestCase` tests, one per AC (the AC ids are in the test names or comments), plus intraword `a~~b~~c` and a check that `'~' not in markdown.Markdown().ESCAPED_CHARS` |
| docs/extensions/strikethrough.md | - | new: user documentation (summary, syntax, the escaping note, usage with `extensions=['strikethrough']`) |
| docs/extensions/index.md | - | add: a row for `strikethrough` / `markdown.extensions.strikethrough` and its link reference |
| docs/reference/markdown.extensions.strikethrough.md | - | new: `::: markdown.extensions.strikethrough` API reference stub |
| mkdocs.yml | - | add: nav entries for the extension page and the reference page |
| docs/changelog.md | - | add: an "Unreleased" entry announcing the new `strikethrough` extension |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 | The `pyproject.toml` entry point plus `StrikethroughExtension` (the short-name lookup in `Markdown.build_extension`) |
| AC-FR-001-02 | `makeExtension` in `markdown/extensions/strikethrough.py` (the dotted-path fallback) |
| AC-FR-001-03 | No change to core or `build_inlinepatterns`. The pattern and the `~` escape are added only inside `StrikethroughExtension.extendMarkdown`. |
| AC-FR-001-04 | `fenced_code` turns the fence into a placeholder in the `htmlStash` during preprocessing, so the inline pattern never sees the tildes. The `(?<!~)`/`(?!~)` checks in `STRIKE_RE` are a second guard. |
| AC-FR-002-01 | `STRIKE_RE` plus `SimpleTagInlineProcessor(..., 'del')` |
| AC-FR-002-02 | Priority 65: link (160) has already become a placeholder, and `em_strong` (60) processes the `<del>` text afterwards |
| AC-FR-002-03 | Priority 65 > 60: `<del>` becomes a placeholder before `em_strong` wraps it in `<em>` |
| AC-FR-002-04 | The lazy `(.+?)` in `STRIKE_RE` makes two separate matches |
| AC-FR-002-05 | `backtick` (190) runs before 65 and produces `AtomicString` code text |
| AC-FR-003-01 | `STRIKE_RE` needs exactly `~~`. A single `~` never matches. |
| AC-FR-003-02 | `STRIKE_RE` needs a closing `~~`. With no match, the text stays literal. |
| AC-FR-003-03 | The `(?![\s~])` check after the opener and the `(?<![\s~])` check before the closer |
| AC-FR-003-04 | The `(?<!~)` check before the opener and the `(?!~)` check after the closer |
| AC-FR-003-05 | `extendMarkdown` appends `'~'` to `md.ESCAPED_CHARS`. `escape` (180) runs before 65, and `unescape` restores the literal `~`. |

## Risks

- **The short name needs reinstalled metadata (ADR-2).** `extensions=['strikethrough']` (AC-FR-001-01) only works after the distribution is reinstalled (`pip install -e .`). Without that, `build_extension` treats `strikethrough` as a module path and raises `ImportError`. The test environment or CI must reinstall the package before running the tests. The dotted-path AC does not depend on this.
- **Priority interactions.** Priority 65 relies on the built-in order in ARCHITECTURE.md §1. If a third-party pattern registered between 60 and 80 also consumes `~`, it could conflict. The existing emphasis tests guard against regressions in `*`/`_` handling: `tests/test_syntax/inline/test_emphasis.py` and `tests/test_syntax/extensions/test_legacy_em.py`. The new tests cover the interaction with `*`.
- **The added `ESCAPED_CHARS` entry stays on the instance.** Like `tables`, it is not removed on `reset()`. That is fine, because it belongs to the extension's configuration of the instance, not to the state of one document (C5). `tests/test_apis.py` (around lines 946-949, which check that `ESCAPED_CHARS` is per instance) guards against leaking it into other instances.
- **Fenced code.** `tests/test_syntax/extensions/test_fenced_code.py` guards `~~~` fences. AC-FR-001-04 adds a test with both extensions enabled.
- **Placeholder text.** The `STX`/`ETX` placeholders contain no `~` or whitespace. Placeholders right next to `~~` (for example `~~[link](x)~~`) still meet the flanking checks, and AC-FR-002-02 tests this.
- **Untrusted input.** No prompt-injection attempt was found in the spec or the issue text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/strikethrough.py` / `(new) STRIKE_RE`: ok
- `markdown/extensions/strikethrough.py` / `(new) StrikethroughExtension`: ok
- `markdown/extensions/strikethrough.py` / `(new) makeExtension`: ok
- `pyproject.toml` / `-`: ok
- `tests/test_syntax/extensions/test_strikethrough.py` / `(new) TestStrikethrough`: ok
- `docs/extensions/strikethrough.md` / `-`: ok
- `docs/extensions/index.md` / `-`: ok
- `docs/reference/markdown.extensions.strikethrough.md` / `-`: ok
- `mkdocs.yml` / `-`: ok
- `docs/changelog.md` / `-`: ok
