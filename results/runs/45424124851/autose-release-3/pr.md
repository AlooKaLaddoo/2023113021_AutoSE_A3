Closes #3

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45424124851)._

### Requirements (from spec.md)

- **FR-001** Render piped wikilinks with custom link text: The wikilinks extension SHALL render `[[<page name>|<link text>]]` as an `<a>` element whose `href` and `class` equal those produced for `[[<page name>]]` under the same configuration and meta-data, and whose text is the link text with surrounding whitespace removed.
  - `AC-FR-001-01` given markdown.Markdown(extensions=['wikilinks']), when converting 'Read [[Installation Guide|see the install docs]] first.', then output is '<p>Read <a class="wikilink" href="/Installation_Guide/">see the install docs</a> first.</p>'
  - `AC-FR-001-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[  Installation Guide  |  see the install docs  ]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">see the install docs</a></p>'
  - `AC-FR-001-03` given markdown.Markdown(extensions=[WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo')]), when converting '[[Installation Guide|see the install docs]]', then output is '<p><a class="foo" href="/wiki/Installation_Guide.html">see the install docs</a></p>'
  - `AC-FR-001-04` given a build_url callable that records its `label` argument and returns '/bar/', passed as WikiLinkExtension(build_url=...), when converting '[[foo|Some Text]]', then output is '<p><a class="wikilink" href="/bar/">Some Text</a></p>' and the callable was called with label == 'foo', base == '/', end == '/'
  - `AC-FR-001-05` given markdown.Markdown(extensions=['meta', 'wikilinks']) and the document 'wiki_base_url: http://example.com/\nwiki_end_url:   .html\nwiki_html_class:\n\nSee [[Installation Guide|the docs]].', when converting the document, then output is '<p>See <a href="http://example.com/Installation_Guide.html">the docs</a>.</p>' (no class attribute)
  - `AC-FR-001-06` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Installation Guide|the install docs, v2.0!]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">the install docs, v2.0!</a></p>'
  - `AC-FR-001-07` given markdown.Markdown(extensions=['wikilinks']), when converting '[[a|b|c]]', then output contains no '<a' element and is '<p>[[a|b|c]]</p>'
- **FR-002** Fall back to page name for empty link text; preserve plain wikilinks: When the link text after `|` is empty or whitespace-only, the wikilinks extension SHALL render the link exactly as `[[<page name>]]` would be rendered; plain `[[<page name>]]` links and the existing empty-link behaviour SHALL remain unchanged.
  - `AC-FR-002-01` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Installation Guide|]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[ Installation Guide |   ]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-03` given markdown.Markdown(extensions=['wikilinks']), when converting 'Some text with a [[WikiLink]].' and '[[ foo bar_baz ]]', then outputs are '<p>Some text with a <a class="wikilink" href="/WikiLink/">WikiLink</a>.</p>' and '<p><a class="wikilink" href="/foo_bar_baz/">foo bar_baz</a></p>'; all existing TestWikiLinks tests and the tests/extensions/wikilinks.txt -> wikilinks.html legacy test still pass unmodified
  - `AC-FR-002-04` given markdown.Markdown(extensions=['wikilinks']), when converting 'foo [[ |some text]] bar' and 'foo [[ ]] bar', then both outputs are '<p>foo  bar</p>' (same as the existing empty-wikilink behaviour)

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify `WIKILINK_RE` to `r'\[\[([\w0-9_ -]+)(?:\ |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: keep URL/class building from stripped group 1 via `build_url` and `_getMeta()`; set `a.text` to stripped group 2, falling back to the page name when group 2 is missing, empty or whitespace-only; empty page name still returns `'' |
| `markdown/extensions/wikilinks.py` | `(new) ` none; module docstring only if needed` | modify: no new symbols |
| `tests/test_extensions.py` | `TestWikiLinks` | add test methods for AC-FR-001-01..07 and AC-FR-002-01..04 (piped basic, whitespace, simple settings, custom `build_url` argument capture, meta-data overrides, punctuation, multiple pipes, empty/whitespace text fallback, empty page name); existing methods unchanged |
| `docs/extensions/wikilinks.md` | `-` | modify: document `[[Page Name\ |
| `docs/changelog.md` | `-` | modify: add a `### Changed` entry under `## [Unreleased]`: "The `wikilinks` extension supports custom link text with `[[Page Name\ |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1177 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/17
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-3-e2_implementer_writes_tests`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45424789546
- Result: **PASS** 
