Closes #4

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45421944976)._

### Requirements (from spec.md)

- **FR-001** Provide an opt-in built-in strikethrough extension: The system SHALL provide a built-in extension that can be loaded with markdown.markdown(text, extensions=['strikethrough']), and SHALL NOT treat '~~' specially when the extension is not enabled.
  - `AC-FR-001-01` given Markdown source '~~foo~~', when markdown.markdown('~~foo~~', extensions=['strikethrough']) is called, then No exception is raised and the result is '<p><del>foo</del></p>'
  - `AC-FR-001-02` given Markdown source '~~foo~~', when markdown.markdown('~~foo~~', extensions=['markdown.extensions.strikethrough']) is called, then The result is '<p><del>foo</del></p>'
  - `AC-FR-001-03` given Markdown source '~~foo~~ and *bar*', when markdown.markdown('~~foo~~ and *bar*') is called with no extensions, then The result is '<p>~~foo~~ and <em>bar</em></p>' (identical to current output)
  - `AC-FR-001-04` given Markdown source '~~~
~~foo~~
~~~', when markdown.markdown(source, extensions=['strikethrough', 'fenced_code']) is called, then The result is '<pre><code>~~foo~~
</code></pre>' (tildes inside the code block are not converted)
- **FR-002** Render double-tilde spans as <del> with nested inline markup: When the strikethrough extension is enabled, the system SHALL render text enclosed in a matching pair of '~~' delimiters as a <del> element whose content is still processed for other inline markup (strong, emphasis, links).
  - `AC-FR-002-01` given Markdown source 'This is ~~withdrawn~~ text.', when converted with extensions=['strikethrough'], then The result is '<p>This is <del>withdrawn</del> text.</p>'
  - `AC-FR-002-02` given Markdown source '~~**bold** *em* [link](http://example.com)~~', when converted with extensions=['strikethrough'], then The result is '<p><del><strong>bold</strong> <em>em</em> <a href="http://example.com">link</a></del></p>'
  - `AC-FR-002-03` given Markdown source '*a ~~b~~ c*', when converted with extensions=['strikethrough'], then The result is '<p><em>a <del>b</del> c</em></p>'
  - `AC-FR-002-04` given Markdown source '~~one~~ and ~~two~~', when converted with extensions=['strikethrough'], then The result is '<p><del>one</del> and <del>two</del></p>'
  - `AC-FR-002-05` given Markdown source '`~~code~~`', when converted with extensions=['strikethrough'], then The result is '<p><code>~~code~~</code></p>'
- **FR-003** Leave single and unmatched tildes literal: When the strikethrough extension is enabled, the system SHALL leave a single '~', an unclosed '~~', and '~~' delimiters that cannot form a valid span as literal text in the output.
  - `AC-FR-003-01` given Markdown source 'about ~5 minutes, ~foo~', when converted with extensions=['strikethrough'], then The result is '<p>about ~5 minutes, ~foo~</p>'
  - `AC-FR-003-02` given Markdown source 'an ~~unclosed span', when converted with extensions=['strikethrough'], then The result is '<p>an ~~unclosed span</p>'
  - `AC-FR-003-03` given Markdown source 'a ~~ b ~~ c', when converted with extensions=['strikethrough'], then The result is '<p>a ~~ b ~~ c</p>'
  - `AC-FR-003-04` given Markdown source '~~~foo~~~', when converted with extensions=['strikethrough'], then The result is '<p>~~~foo~~~</p>'
  - `AC-FR-003-05` given Markdown source '\~\~foo\~\~', when converted with extensions=['strikethrough'], then The result is '<p>~~foo~~</p>'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/strikethrough.py` | `(new) STRIKE_RE` | new: module-level regex `r'(?<!~)(~~)(?![\s~])(.+?)(?<![\s~])~~(?!~)'`; group 2 is the content |
| `markdown/extensions/strikethrough.py` | `(new) StrikethroughExtension` | new: `Extension` subclass with no config options. `extendMarkdown(md)` registers `SimpleTagInlineProcessor(STRIKE_RE, 'del')` as `'strikethrough'` at priority 65 and appends `'~'` to `md.ESCAPED_CHARS` if it is missing. The docstring includes a registry table like `legacy_em.py`. Includes the module header and docstring in the style of the other built-ins. |
| `markdown/extensions/strikethrough.py` | `(new) makeExtension` | new: `return StrikethroughExtension(**kwargs) |
| `pyproject.toml` | `-` | add: `strikethrough = 'markdown.extensions.strikethrough:StrikethroughExtension'` under `[project.entry-points.'markdown.extensions'] |
| `tests/test_syntax/extensions/test_strikethrough.py` | `(new) TestStrikethrough` | new: `markdown.test_tools.TestCase` tests, one per AC (the AC ids are in the test names or comments), plus intraword `a~~b~~c` and a check that `'~' not in markdown.Markdown().ESCAPED_CHARS |
| `docs/extensions/strikethrough.md` | `-` | new: user documentation (summary, syntax, the escaping note, usage with `extensions=['strikethrough']`) |
| `docs/extensions/index.md` | `-` | add: a row for `strikethrough` / `markdown.extensions.strikethrough` and its link reference |
| `docs/reference/markdown.extensions.strikethrough.md` | `-` | new: `::: markdown.extensions.strikethrough` API reference stub |
| `mkdocs.yml` | `-` | add: nav entries for the extension page and the reference page |
| `docs/changelog.md` | `-` | add: an "Unreleased" entry announcing the new `strikethrough` extension |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1200 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/13
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-4`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45422783954
- Result: **PASS** 
