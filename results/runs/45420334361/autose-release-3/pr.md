Closes #3

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45420334361)._

### Requirements (from spec.md)

- **FR-001** Render [[Page Name|link text]] as a wikilink with custom text: The wikilinks extension SHALL convert `[[<page name>|<link text>]]` into an `<a>` element. Its `href` and `class` SHALL be exactly what `[[<page name>]]` would produce under the same configuration and meta-data, and its text SHALL be the stripped <link text>.
  - `AC-FR-001-01` given markdown.Markdown(extensions=['wikilinks']), when converting 'See [[Installation Guide|see the install docs]].', then output is '<p>See <a class="wikilink" href="/Installation_Guide/">see the install docs</a>.</p>'
  - `AC-FR-001-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[ Installation Guide | see the install docs ]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">see the install docs</a></p>'
  - `AC-FR-001-03` given WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo'), when converting '[[WikiLink|the text]]', then output is '<p><a class="foo" href="/wiki/WikiLink.html">the text</a></p>'
  - `AC-FR-001-04` given WikiLinkExtension(build_url=f), where f(label, base, end) returns '/x/' + label + '/' and records the label it received, when converting '[[foo|bar]]', then output is '<p><a class="wikilink" href="/x/foo/">bar</a></p>', and f was called exactly once with label 'foo'
  - `AC-FR-001-05` given markdown.Markdown(extensions=['meta', 'wikilinks']), when converting 'wiki_base_url: http://example.com/\nwiki_end_url:   .html\nwiki_html_class:\n\nSome text with a [[WikiLink|custom]].', then output is '<p>Some text with a <a href="http://example.com/WikiLink.html">custom</a>.</p>'
  - `AC-FR-001-06` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Page|a|b]]', then output is '<p><a class="wikilink" href="/Page/">a|b</a></p>'
  - `AC-FR-001-07` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Page|a & b]]', then output is '<p><a class="wikilink" href="/Page/">a &amp; b</a></p>'
- **FR-002** Fall back to the page name when the link text is empty, and keep existing behaviour: When the link text after '|' is empty or only whitespace, the wikilinks extension SHALL render exactly the output of `[[<page name>]]`. Plain `[[<page name>]]` links, including the empty `[[ ]]` case, SHALL produce the same output as before this change.
  - `AC-FR-002-01` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Installation Guide|]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[ Installation Guide |   ]]', then output is '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-03` given markdown.Markdown(extensions=['wikilinks']), when converting 'Some text with a [[WikiLink]].' and '[[ foo bar_baz ]]', then outputs are '<p>Some text with a <a class="wikilink" href="/WikiLink/">WikiLink</a>.</p>' and '<p><a class="wikilink" href="/foo_bar_baz/">foo bar_baz</a></p>', and every existing test in tests/test_extensions.py::TestWikiLinks and the tests/extensions/wikilinks.txt legacy test still passes unmodified
  - `AC-FR-002-04` given markdown.Markdown(extensions=['wikilinks']), when converting 'foo [[ ]] bar', then output is '<p>foo  bar</p>'
  - `AC-FR-002-05` given markdown.Markdown(extensions=['wikilinks']), when converting 'foo [[ |text]] bar', then output contains no '<a' element and no 'href', i.e. the same as the empty [[ ]] case: '<p>foo  bar</p>'

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify `WIKILINK_RE` to `\[\[([\w0-9_ -]+)(?:\ |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: keep the `m.group(1).strip()` guard (an empty page name returns `''`). Compute `label = m.group(1).strip()` and pass only `label` to `self.config['build_url'](label, base_url, end_url)`. Compute `text = (m.group(2) or '').strip()` and set `a.text = text or label`. The `href`/`class` handling and `_getMeta()` stay unchanged. |
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension` | modify the module docstring / header comment only if needed to mention the `[[Page |
| `tests/test_extensions.py` | `TestWikiLinks` | add test methods for AC-FR-001-01 to -07 and AC-FR-002-01, -02, -04 (with a `[[ ]]` regression check) and -05. Leave every existing test unmodified. |
| `docs/extensions/wikilinks.md` | `-` | modify the "Syntax" section to describe `[[Page Name |
| `docs/changelog.md` | `-` | add an entry under `## [Unreleased]` for wikilink custom link text, in a new `### Changed` subsection. |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1183 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/11
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-3`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45421094007
- Result: **PASS** 
