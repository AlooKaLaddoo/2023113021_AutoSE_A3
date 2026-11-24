# Design: Guard list block processors against RecursionError on deep nesting

## Approach

Apply the guard that already protects blockquotes to the list block processors. `BlockQuoteProcessor.test` returns `False` when `util.nearing_recursion_limit()` is true (`markdown/blockprocessors.py:290`). The change adds `and not util.nearing_recursion_limit()` to two places:

- **`OListProcessor.test`** (`markdown/blockprocessors.py:356-357`). `UListProcessor` inherits `test` and only overrides `RE` in `__init__`, so this one edit covers both `-`/`*`/`+` lists and `1.` lists, and mixed nesting.
- **`ListIndentProcessor.test`** (`markdown/blockprocessors.py:174-179`). This covers the "each line indented more" case, which recurses through `ListIndentProcessor.run` → `parseBlocks` → `OListProcessor.run` → ….

Once the stack is within 100 frames of the limit, these processors decline the block, and the lower-priority processors take it. Neither of them recurses:

- A list block falls through to `paragraph` (priority 10). In list state that processor writes the remaining text (for example `- - … x`) as the text of the deepest `li`. No content is lost, which matches Q-001 option A and ASSUMP-001.
- An indented block falls through to `code` (priority 80), which builds a `pre/code` element.

Because the guard is relative to `sys.getrecursionlimit()`, it also works under `markdown.test_tools.recursionlimit(...)` (ASSUMP-003). At normal depths `nearing_recursion_limit()` is false, so `test()` returns the same value as before and shallow output stays byte-for-byte the same (FR-002).

**Fit with ARCHITECTURE.md:**
- This is a bug fix to built-in processors, not optional behaviour, so it goes in the existing classes. No processor is added or reprioritised and no default `build_*` function changes, so C1 / ADR-1 still hold. Registry priorities are untouched.
- `util.py` stays dependency-free (C3).
- The guard is stateless, so nothing new needs resetting (C5). After a deep input the parser `State` stack unwinds normally through each `run`'s `state.reset()`.

**Alternative rejected:** rewriting `BlockParser.parseBlocks` and the list `run` methods to use an explicit stack instead of recursion. That would allow real unlimited nesting, but it is a large, risky rewrite of the core parser and the processors' extension contract (`parseChunk`/`parseBlocks` re-entry), and the reporter does not need correct rendering at extreme depth. A fixed maximum-depth constant was also rejected, because it would ignore lowered limits and differ from the blockquote precedent (ASSUMP-003).

**Downstream recursion check:**
- The serializer is iterative, and `InlineProcessor.run` uses an explicit stack, so neither needs a change.
- `PrettifyTreeprocessor._prettifyETree` is recursive, one frame per block-level element. Block parsing uses at least 2 frames (`parseBlocks` + `run`) per nesting level, and each level adds 2 elements (`ul` + `li`). Prettify also starts from a shallower stack than block parsing, and the guard leaves a 100-frame margin. So the resulting tree depth stays under the limit for prettify, and it needs no change. The Risks section covers this.

## Change plan

| File | Symbol | Change |
|------|--------|--------|
| `markdown/blockprocessors.py` | `OListProcessor.test` | modify: return `bool(self.RE.match(block)) and not util.nearing_recursion_limit()`. `UListProcessor` inherits this. |
| `markdown/blockprocessors.py` | `ListIndentProcessor.test` | modify: add `and not util.nearing_recursion_limit()` to the existing boolean expression, keeping the current conditions and their order. |
| `tests/test_syntax/blocks/test_ul.py` | `(new) TestListNestingLimit` | new: `markdown.test_tools.TestCase` subclass with one test per AC: deep `'- '*500+'x'`, deep `'1. '*500+'x'`, 300 lines indented 4 more spaces each, `'- 1. '*250+'x'`, `'- '*100+'x'` under `recursionlimit(150)`, reuse after `md.reset()`, and exact-output checks for the three shallow FR-002 inputs. |

## Acceptance criteria coverage

- **AC-FR-001-01** (`'- '*500+'x'`): satisfied by the `OListProcessor.test` guard, inherited by `UListProcessor`. Near the limit, the paragraph processor writes the remaining markers plus `x` into the deepest `li`. Output starts with `<ul>` and contains `x`. Tested in `TestListNestingLimit`.
- **AC-FR-001-02** (`'1. '*500+'x'`): satisfied by the same `OListProcessor.test` guard. Output starts with `<ol>` and contains `x`. Tested.
- **AC-FR-001-03** (300 lines, 4 more spaces each): satisfied by the `ListIndentProcessor.test` guard together with the `OListProcessor.test` guard. Both paths in the `ListIndentProcessor.run` ↔ `OListProcessor.run` recursion check the limit, and the remainder falls through to `CodeBlockProcessor`. Output starts with `<ul>`. Tested.
- **AC-FR-001-04** (`'- 1. '*250+'x'`): satisfied by the `OListProcessor.test` guard, which is shared by both list processors. Tested.
- **AC-FR-001-05** (`recursionlimit(150)`, `'- '*100+'x'`): satisfied because `util.nearing_recursion_limit()` reads the current `sys.getrecursionlimit()`. Tested with `markdown.test_tools.recursionlimit`.
- **AC-FR-001-06** (reuse after a deep input): satisfied because the guard keeps no state, and every `run` still calls `parser.state.reset()` as the recursion unwinds. A new `BlockParser` state is used on the next `convert`. Tested with `md.reset(); md.convert('- a\n- b')`.
- **AC-FR-002-01 / 02 / 03** (shallow nesting, exact output): satisfied because `nearing_recursion_limit()` is false at these depths, so `test()` results do not change. Tested with exact expected strings.
- **AC-FR-002-04** (existing suite unchanged): no expected outputs are changed. The full `python -m unittest discover -s tests -t .` run guards this.
- **NFR-001** (0 exceptions for inputs of 1500 bytes or less at the default limit): covered by the tests for AC-FR-001-01, 02 and 04.

## Risks

- **Prettify recursion:** `PrettifyTreeprocessor._prettifyETree` recurses once per block-level element. If some list path built more than one element per frame of block-parser recursion, the tree could be deep enough for prettify to hit the limit after parsing succeeds. The frame analysis in the Approach section says it will not, and the AC-FR-001-01..05 tests would expose it if it did. If they fail there, the fallback is to make `_prettifyETree` iterative (same file, `markdown/treeprocessors.py`) without changing its output.
- **Shallow output regression:** the guard is only an extra `and` clause on `test()`, so behaviour changes only within 100 frames of the limit. Guarded by `tests/test_syntax/blocks/test_ul.py`, the legacy list fixtures under `tests/basic`, `tests/extensions`, and the `tests/test_legacy.py` suites, plus the new FR-002 exact-output tests.
- **Interaction with extensions that subclass list processors** (e.g. `sane_lists` overrides `OListProcessor`/`UListProcessor` attributes, and `def_list`/`admonition` call `parseChunk`): subclasses that do not override `test` inherit the guard. Those that do override it keep their current behaviour, which is out of scope. Guarded by `tests/test_syntax/extensions/` (sane_lists, def_list, admonition).
- **Blockquote/list interplay:** blockquotes inside lists already check the same function, so both degrade at the same threshold. Guarded by `tests/test_syntax/blocks/test_blockquotes.py::test_nesting_limit`.
- **Cost of the stack-depth check:** `nearing_recursion_limit()` walks the frame stack on every list `test()` call. The work is linear in the current depth, which is small for normal documents, and it is the same cost blockquotes already pay. No performance target is in scope.
- **Prompt injection:** none found in the spec or the issue text.


---
## Stage 2 check (orchestrator, attempt 1)

Result: **PASS**

- `markdown/blockprocessors.py` / `OListProcessor.test`: ok
- `markdown/blockprocessors.py` / `ListIndentProcessor.test`: ok
- `tests/test_syntax/blocks/test_ul.py` / `(new) TestListNestingLimit`: ok
