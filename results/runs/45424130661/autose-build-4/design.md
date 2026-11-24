# Design: Opt-in `strikethrough` extension that renders `~~text~~` as `<del>`

## Approach

Add a new built-in extension module, `markdown/extensions/strikethrough.py`. Its `extendMarkdown(md)` adds a `~` delimiter to the existing shared `DelimiterProcessor`, the `em_strong` inline processor at priority 60 that `md.delimiters` points to. The call is `md.delimiters.add('~', 'del', smart=False, double=True)`. With one tag (`'del'`) and `double=True`, `Delimiter` sets `max_size = 2` and `double = True`. The paired region therefore always becomes `<del>`. A run of a single `~` is rejected ("Double needs at least a size of 2" in `DelimiterProcessor.handleMatch`), and an unpaired `~~` falls through to the "failed to pair" path, so it stays literal. The boundary regexes do not allow whitespace after an opening run or before a closing run, so `~~ text ~~` stays literal (ASSUMP-002 / Q-001 option A). `smart=False` keeps intraword `a~~b~~c` working, as in GFM.

`~` lives in the same processor as `*` and `_`. That lets one stack-based pairing pass handle nesting in both directions, such as `~~a **bold**~~` and `**bold ~~struck~~**` (AC-FR-002-01/02). Links are already turned into placeholders at priority 160. Code spans become `AtomicString` at 190, so they are never seen. Fenced code is stashed by a preprocessor before inline processing.

When `md.delimiters is None` (another extension removed `em_strong`), the extension follows the precedent in `legacy_em.py`. It registers a fresh `DelimiterProcessor('~', 'del', md, double=True)` as `'strikethrough'` at priority 60.

How this fits the architecture:
- **C1 / ADR-1:** behaviour is added only through the instance's registries and the delimiter API. `build_inlinepatterns` is not edited, so the default pipeline is unchanged (ASSUMP-001).
- **C2 / ADR-2:** the extension uses the standard `Extension` subclass plus `makeExtension`. It is declared as an entry point in `pyproject.toml`. The dotted path `markdown.extensions.strikethrough` works without reinstalling. The short name needs the package metadata to be reinstalled (ASSUMP-003).
- **C3:** the extension imports `DelimiterProcessor` from the core. The core never imports the extension.
- **C5:** there is no new per-document state. Delimiter stacks are already cleared by `DelimiterProcessor.reset()` from `Markdown.reset()`.
- `ESCAPED_CHARS` is not touched (ASSUMP-004).

**Rejected alternative:** a separate regex `SimpleTagInlineProcessor` such as `(~~)(.+?)~~` registered at its own priority. It would run before or after `em_strong` instead of being paired together with it. That causes wrong results when the delimiters interleave, such as `**a ~~b** c~~`. It would also duplicate the flanking rules that `Delimiter` already applies, which goes against ASSUMP-002's "follow the existing `*`/`_` handling".

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/extensions/strikethrough.py` | (new) StrikethroughExtension | new: `Extension` subclass with no config options. `extendMarkdown(md)`: if `md.delimiters is not None`, call `md.delimiters.add('~', 'del', double=True)`; otherwise call `md.inlinePatterns.register(DelimiterProcessor('~', 'del', md, double=True), 'strikethrough', 60)`. The docstring has the registry table, following the `legacy_em.py` style. |
| `markdown/extensions/strikethrough.py` | (new) makeExtension | new: module-level factory that returns `StrikethroughExtension(**kwargs)`. Needed for dotted-path loading (AC-FR-001-03). |
| `pyproject.toml` | - | add the entry point `strikethrough = 'markdown.extensions.strikethrough:StrikethroughExtension'` under `[project.entry-points.'markdown.extensions']`. |
| `tests/test_syntax/extensions/test_strikethrough.py` | (new) TestStrikethrough | new: a `markdown.test_tools.TestCase` subclass with one test per acceptance criterion (AC-FR-001-01..03, AC-FR-002-01..08). It also covers `~~ text ~~` staying literal and a reused `Markdown` instance (`reset()` between conversions). |
| `docs/extensions/strikethrough.md` | - | new: documentation page covering the syntax, the `<del>` output, the delimiter rules (exactly `~~`, no inner whitespace at the edges), usage by short name and dotted path, and the fact that `\~` is not an escape. |
| `docs/extensions/index.md` | - | add: a row for `strikethrough` in the officially supported extensions table. |
| `mkdocs.yml` | - | add: a nav entry for `extensions/strikethrough.md`. |
| `docs/changelog.md` | - | add: an "Unreleased" entry for the new `strikethrough` extension. |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 | The `pyproject.toml` entry point resolves `'strikethrough'` (once the package is reinstalled). `StrikethroughExtension.extendMarkdown` adds the `~`→`del` delimiter. |
| AC-FR-001-02 | No change to `build_inlinepatterns` or `core.py`. `~` is only added inside `extendMarkdown`, so without the extension `~~deleted~~` stays literal. |
| AC-FR-001-03 | Module-level `makeExtension` in `markdown/extensions/strikethrough.py`, used by the dotted-path fallback in `Markdown.build_extension`. |
| AC-FR-002-01 | The shared `DelimiterProcessor` pairs `~` and `*` in one pass, so `<strong>` and `<em>` nest inside `<del>`. The link has already been turned into a placeholder by `link` (160) and is restored inside the `<del>`. |
| AC-FR-002-02 | The same shared pairing pass nests `<del>` inside `<strong>`. |
| AC-FR-002-03 | `double=True`: a run of length 1 returns no element. A lone closing `~` with an empty stack is skipped. |
| AC-FR-002-04 | An unpaired start stays on the stack. The "failed to pair" path returns `None`, so the text stays literal. |
| AC-FR-002-05 | Cached regions in `DelimiterProcessor` (`get_cached_result`) produce both `<del>` elements. |
| AC-FR-002-06 | `backtick` (190) wraps code-span content as an `AtomicString`, which inline processing skips. No change needed. |
| AC-FR-002-07 | `fenced_code` stashes the block in a preprocessor before inline patterns run. No change needed. |
| AC-FR-002-08 | `*` and `_` delimiter definitions are untouched. Adding `~` only extends the token alternation and the `self.delimiters` dict. |

## Risks

- **Interaction with `*`/`_` pairing.** `~` shares the stack logic of `DelimiterProcessor`. If something goes wrong, it could change emphasis output in documents that mix `~` and `*`, but only when the extension is enabled. Without the extension the code path is identical. Guarded by `tests/test_syntax/inline/` (emphasis and strong tests), `tests/test_syntax/extensions/test_legacy_em.py`, the legacy suites under `tests/basic`, `tests/extensions`, `tests/misc`, and the new AC-FR-002-08 test.
- **Short-name loading depends on installed metadata (ADR-2).** AC-FR-001-01 fails with an import error until the package is reinstalled (`pip install -e .`). The dotted-path test (AC-FR-001-03) does not depend on this. CI must reinstall before running tests.
- **`md.delimiters is None` fallback.** If another extension later registers its own `DelimiterProcessor`, `md.delimiters` is overwritten and the processors would not share pairing. This mirrors the existing `legacy_em` behaviour. `Markdown.reset()` already clears stale references (`core.py:275-278`).
- **Triple tildes (`~~~x~~~`)** in inline text pair as one `<del>` plus a leftover literal `~` on each side, or similar, depending on the stack logic. That is an edge case under Q-001 and is not tied to any AC. Tilde fences are block-level and stay unaffected (AC-FR-002-07; `tests/test_syntax/extensions/test_fenced_code.py`).
- **Escaping.** `\~` is not added to `ESCAPED_CHARS`, so users cannot escape a literal `~~` pair (Q-002, accepted).
- **Untrusted input.** The issue text in the spec contains no instructions aimed at the agent. No risk was found.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/extensions/strikethrough.py` / `(new) StrikethroughExtension`: ok
- `markdown/extensions/strikethrough.py` / `(new) makeExtension`: ok
- `pyproject.toml` / `-`: ok
- `tests/test_syntax/extensions/test_strikethrough.py` / `(new) TestStrikethrough`: ok
- `docs/extensions/strikethrough.md` / `-`: ok
- `docs/extensions/index.md` / `-`: ok
- `mkdocs.yml` / `-`: ok
- `docs/changelog.md` / `-`: ok
