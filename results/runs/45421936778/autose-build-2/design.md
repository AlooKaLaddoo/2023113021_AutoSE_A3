# Design: Stop list nesting near the recursion limit

## Approach

Use the same guard that `BlockQuoteProcessor.test` already uses (`markdown/blockprocessors.py:290`). The two list block processors that recurse will report "not applicable" when the Python stack is close to `sys.getrecursionlimit()`:

- `OListProcessor.test` (which `UListProcessor` inherits) becomes `bool(self.RE.match(block)) and not util.nearing_recursion_limit()`. When the guard trips, the remaining text such as `- - - … x` falls through to lower-priority processors. In practice that is `paragraph` (priority 10), which does not recurse. So the leftover markers and the `x` stay in the deepest `<li>` as literal text. This is option (a)/(b) of Q-001.
- `ListIndentProcessor.test` gets the same `and not util.nearing_recursion_limit()` term, added last. When it trips, the indented block falls through to `code` (priority 80), which does not recurse. This covers the progressively indented inputs of FR-002, where each level passes through `ListIndentProcessor.run`, then `parseBlocks`, then `OListProcessor.run`.

In both `test()` methods the regex or indent check runs first and the stack check last. Normal documents therefore pay for `_get_stack_depth()` only on blocks that really are list blocks. The depth limit follows the recursion limit, as ASSUMP-002 and the Q-002 default require. This is the existing blockquote convention, so no new public symbols, configuration or modules are needed.

**Architecture fit:**
- **C1:** no registry or priority changes. The built-in processors keep their names and priorities. We only tighten their `test()` methods, which is the same pattern as the existing `quote` processor.
- **C3:** `blockprocessors.py` already imports `util`, so no new dependency is added.
- **Later stages:** the parser now stops near the limit, so the tree is shallow enough for them.
  - Tree depth is bounded by parser depth, because each list level uses about 2 parser frames (`parseBlocks` and `run`) and creates 2 elements (`ul`/`ol` and `li`).
  - `PrettifyTreeprocessor._prettifyETree` uses 1 frame per block element. It starts about 2 frames shallower than the parser, so the 100-frame cushion also protects it.
  - `_serialize_html` and `InlineProcessor.run` are iterative, so tree depth does not affect them.

**Rejected alternative:** a fixed numeric depth cap, for example a `max_list_depth` counter on `parser.state`. It would add a new configuration value with its own tests and docs. It would also be inconsistent with blockquotes, and it would still fail when an embedding application calls `markdown()` from an already deep stack or with a lowered recursion limit. Guarding inside `run()` instead of `test()` was also rejected, because `run()` has already consumed the block by then, and the fallback would mean re-implementing paragraph or code handling.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/blockprocessors.py` | `OListProcessor.test` | modify: return `bool(self.RE.match(block)) and not util.nearing_recursion_limit()`. `UListProcessor` inherits it, so `-`, `*`, `+` and `1.` are all covered. |
| `markdown/blockprocessors.py` | `ListIndentProcessor.test` | modify: append `and not util.nearing_recursion_limit()` as the last condition, so indented blocks near the limit fall through to the non-recursive `CodeBlockProcessor`. |
| `tests/test_syntax/blocks/test_ul.py` | `(new) TestListNestingLimit` | add: a `markdown.test_tools.TestCase` subclass with tests for AC-FR-001-01..04 (`'- '`, `'1. '`, `'* '`, `'+ '` × 500, and `'- '` × 5000, each followed by `'x'`). Each asserts that no exception is raised, the result is a `str`, the expected `<ul>`/`<ol>` prefix is present, and `'x'` is in the output. Also tests for AC-FR-002-01..03 (300 lines with 4-space steps, the loose `1. x` variant with blank lines, 1-space steps). It also asserts the exact HTML for AC-FR-003-01..03. Like `test_nesting_limit`, it also checks one small case under `recursionlimit(...)` from `markdown.test_tools`: a list nested deeper than the lowered limit allows must render without raising. |
| `docs/changelog.md` | - | add: an "Unreleased" bug-fix entry saying that deeply nested lists no longer raise `RecursionError`, and that nesting stops near the recursion limit as it already does for blockquotes. (Only if the file exists in its usual form; if not, skip this row.) |

## Acceptance criteria coverage

| AC | Satisfied by |
|----|--------------|
| AC-FR-001-01 (`'- '*500+'x'`) | `OListProcessor.test` guard, inherited by `UListProcessor`. Recursion stops about 100 frames below the limit. The outer levels are already `<ul>`, so the output starts with `<ul>`, and the remaining text including `x` becomes the text of the deepest `<li>`. Tested in `TestListNestingLimit`. |
| AC-FR-001-02 (`'1. '*500+'x'`) | Same guard on `OListProcessor.test`. The output starts with `<ol>`. Tested in `TestListNestingLimit`. |
| AC-FR-001-03 (`'- '*5000+'x'`) | Same guard. The stopping depth does not depend on input length. The leftover text, about 10 KB, is handled once by `ParagraphProcessor` without recursion. Tested in `TestListNestingLimit`. |
| AC-FR-001-04 (`*` and `+` markers) | `UListProcessor.RE` matches `[*+-]`, and the inherited guarded `test`. Tested in `TestListNestingLimit`. |
| AC-FR-002-01 (300 lines, 4-space steps) | The `OListProcessor.test` guard, plus the `ListIndentProcessor.test` guard for indented items reached through `OListProcessor.run`'s `parseBlocks(lst[-1], [item])`. Past the limit, blocks become code blocks or paragraphs. Tested in `TestListNestingLimit`. |
| AC-FR-002-02 (loose ordered, blank lines) | `ListIndentProcessor.test` guard. This is the loose path `ListIndentProcessor.run` → `parseChunk`/`parseBlocks`. `OListProcessor.test` guards the nested list starts. Tested in `TestListNestingLimit`. |
| AC-FR-002-03 (1-space steps) | Indents under 4 spaces are sibling items. Deeper ones go through the same two guarded `test` methods. Tested in `TestListNestingLimit`. |
| AC-FR-003-01..03 (exact shallow output) | At 2–3 levels the stack is far below the limit, so `nearing_recursion_limit()` is `False` and both `test()` methods return exactly what they return today. The exact strings are asserted in `TestListNestingLimit`. |
| AC-FR-003-04 (suite unchanged) | No expected-output files change. `BlockQuoteProcessor` is untouched. The existing `tests/basic/ordered-and-unordered-list`, `test_ul.py` and `test_blockquotes.py::test_nesting_limit` must pass as they are. |
| NFR-001 | Covered together by the FR-001 and FR-002 tests, which include the 10 KB case in AC-FR-001-03. They run under the default recursion limit. |

## Risks

- **A blockquote inside a list near the limit:** these interact. The two guards use the same threshold, so whichever construct reaches the limit first stops nesting. `test_blockquotes.py::test_nesting_limit` runs under `recursionlimit(120)` with no lists, so its output does not change. It guards against regressions in the shared `util.nearing_recursion_limit()`.
- **Changed output near the limit:** behaviour changes only when the stack is within 100 frames of the limit, which previously meant a crash. In normal documents the guard is never true. The existing list fixtures guard this: `tests/basic/ordered-and-unordered-list`, `tests/misc/*list*`, `tests/test_syntax/blocks/test_ul.py`, `tests/test_syntax/extensions/test_*` (e.g. `def_list`, `admonition` nested lists), and `tests/test_legacy.py`.
- **Performance:** `_get_stack_depth()` walks the frame chain, which costs O(depth) per call. The regex or indent check runs first, so the walk only happens for blocks that really are lists or list-indented. With deep nesting the total cost is about O(depth²) frames, at most around 1000² pointer hops, which is negligible. No timing tests exist or are required.
- **Prettify recursion:** `PrettifyTreeprocessor._prettifyETree` is still recursive. It is safe because the tree depth is bounded by the parser depth (about 1 element per frame for lists) and it starts from a shallower base. The 5000-marker test in AC-FR-001-03, run under the default limit, would catch a regression here.
- **Extensions that subclass these processors** (e.g. third-party `OListProcessor` subclasses like `sane_lists`-style ones) and override `test()` will not get the guard. That is acceptable and out of scope. The built-in `sane_lists` extension subclasses without overriding `test`, so it inherits the guard. `tests/test_syntax/extensions/test_sane_lists.py` guards its unchanged behaviour.
- **Prompt injection:** none detected in the spec or issue text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/blockprocessors.py` / `OListProcessor.test`: ok
- `markdown/blockprocessors.py` / `ListIndentProcessor.test`: ok
- `tests/test_syntax/blocks/test_ul.py` / `(new) TestListNestingLimit`: ok
- `docs/changelog.md` / `-`: ok
