Closes #4

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45424130661)._

### Requirements (from spec.md)

- **FR-001** Provide an opt-in built-in 'strikethrough' extension: The system SHALL provide a built-in extension that loads by the short name 'strikethrough' (and by its dotted module path). Its effects SHALL apply only when it is listed in the 'extensions' argument.
  - `AC-FR-001-01` given Markdown source 'This is ~~deleted~~ text.', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p>This is <del>deleted</del> text.</p>'
  - `AC-FR-001-02` given Markdown source 'This is ~~deleted~~ text.', when markdown.markdown(source) is called with no extensions, then The output equals '<p>This is ~~deleted~~ text.</p>'
  - `AC-FR-001-03` given Markdown source '~~gone~~', when markdown.markdown(source, extensions=['markdown.extensions.strikethrough']) is called, then The output equals '<p><del>gone</del></p>'
- **FR-002** Render paired double tildes as <del> with nested inline markup: When the strikethrough extension is enabled, the system SHALL render text enclosed by an opening '~~' and a matching closing '~~' as a <del> element. Other inline markup inside it (strong, emphasis, links, code spans) SHALL still render. A lone '~', an unclosed '~~', and tildes inside code spans or fenced code blocks SHALL be output literally.
  - `AC-FR-002-01` given Markdown source '~~a **bold** and *em* [link](http://example.com)~~', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p><del>a <strong>bold</strong> and <em>em</em> <a href="http://example.com">link</a></del></p>'
  - `AC-FR-002-02` given Markdown source '**bold ~~struck~~**', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p><strong>bold <del>struck</del></strong></p>'
  - `AC-FR-002-03` given Markdown source 'about ~5 minutes and ~text~', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p>about ~5 minutes and ~text~</p>'
  - `AC-FR-002-04` given Markdown source 'this ~~is not closed', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p>this ~~is not closed</p>'
  - `AC-FR-002-05` given Markdown source '~~one~~ and ~~two~~', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p><del>one</del> and <del>two</del></p>'
  - `AC-FR-002-06` given Markdown source '`~~code~~`', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output equals '<p><code>~~code~~</code></p>'
  - `AC-FR-002-07` given Markdown source '~~~\n~~x~~\n~~~', when markdown.markdown(source, extensions=['strikethrough', 'fenced_code']) is called, then The output equals '<pre><code>~~x~~\n</code></pre>'
  - `AC-FR-002-08` given Markdown source '*em* and **strong** and ***both***', when markdown.markdown(source, extensions=['strikethrough']) is called, then The output is identical to markdown.markdown(source) with no extensions

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/strikethrough.py` | `(new) StrikethroughExtension` | new: `Extension` subclass with no config options. `extendMarkdown(md)`: if `md.delimiters is not None`, call `md.delimiters.add('~', 'del', double=True)`; otherwise call `md.inlinePatterns.register(DelimiterProcessor('~', 'del', md, double=True), 'strikethrough', 60)`. The docstring has the registry table, following the `legacy_em.py` style. |
| `markdown/extensions/strikethrough.py` | `(new) makeExtension` | new: module-level factory that returns `StrikethroughExtension(**kwargs)`. Needed for dotted-path loading (AC-FR-001-03). |
| `pyproject.toml` | `-` | add the entry point `strikethrough = 'markdown.extensions.strikethrough:StrikethroughExtension'` under `[project.entry-points.'markdown.extensions']`. |
| `tests/test_syntax/extensions/test_strikethrough.py` | `(new) TestStrikethrough` | new: a `markdown.test_tools.TestCase` subclass with one test per acceptance criterion (AC-FR-001-01..03, AC-FR-002-01..08). It also covers `~~ text ~~` staying literal and a reused `Markdown` instance (`reset()` between conversions). |
| `docs/extensions/strikethrough.md` | `-` | new: documentation page covering the syntax, the `<del>` output, the delimiter rules (exactly `~~`, no inner whitespace at the edges), usage by short name and dotted path, and the fact that `\~` is not an escape. |
| `docs/extensions/index.md` | `-` | add: a row for `strikethrough` in the officially supported extensions table. |
| `mkdocs.yml` | `-` | add: a nav entry for `extensions/strikethrough.md`. |
| `docs/changelog.md` | `-` | add: an "Unreleased" entry for the new `strikethrough` extension. |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1192 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/19
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-4-e2_implementer_writes_tests`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45424930151
- Result: **PASS** 
