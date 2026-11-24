Closes #3

_Opened by the AutoSE workflow (round 1). All stage artifacts (spec.md, design.md, diff.patch, test_report.md, agent transcripts) are on the [workflow run](https://github.com/AlooKaLaddoo/markdown/actions/runs/45423975316)._

### Requirements (from spec.md)

- **FR-001** Render piped wikilinks with custom link text: The wikilinks extension SHALL convert `[[<name>|<text>]]` into an `<a>` element whose `href` and `class` attributes are identical to those produced for `[[<name>]]` under the same configuration and meta-data, and whose text content is <text> with leading and trailing whitespace removed.
  - `AC-FR-001-01` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Installation Guide|see the install docs]]', then output is exactly '<p><a class="wikilink" href="/Installation_Guide/">see the install docs</a></p>'
  - `AC-FR-001-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[ Installation Guide | see the install docs ]]', then output is exactly '<p><a class="wikilink" href="/Installation_Guide/">see the install docs</a></p>'
  - `AC-FR-001-03` given WikiLinkExtension(base_url='/wiki/', end_url='.html', html_class='foo'), when converting 'Some text with a [[WikiLink|a link]].', then output is exactly '<p>Some text with a <a class="foo" href="/wiki/WikiLink.html">a link</a>.</p>'
  - `AC-FR-001-04` given extension_configs {'wikilinks': {'base_url': 'http://example.com/', 'end_url': '.html', 'html_class': ''}}, when converting '[[WikiLink|a link]]', then output is exactly '<p><a href="http://example.com/WikiLink.html">a link</a></p>'
  - `AC-FR-001-05` given markdown.Markdown(extensions=['meta', 'wikilinks']) and source 'wiki_base_url: http://example.com/\nwiki_end_url:   .html\nwiki_html_class:\n\nSome text with a [[WikiLink|a link]].', when converting the source, then output is exactly '<p>Some text with a <a href="http://example.com/WikiLink.html">a link</a>.</p>'
  - `AC-FR-001-06` given WikiLinkExtension(build_url=f) where f(label, base, end) records label and returns '/bar/', when converting '[[ foo | some text ]]', then output is exactly '<p><a class="wikilink" href="/bar/">some text</a></p>' and f was called with label == 'foo', base == '/', end == '/'
  - `AC-FR-001-07` given markdown.Markdown(extensions=['wikilinks']), when converting '[[foo|double  spaces]]', then output is exactly '<p><a class="wikilink" href="/foo/">double  spaces</a></p>'
  - `AC-FR-001-08` given markdown.Markdown(extensions=['wikilinks']), when converting '[[foo|Q&A <docs>]]', then output is exactly '<p><a class="wikilink" href="/foo/">Q&amp;A &lt;docs&gt;</a></p>' (PROVISIONAL, see ASSUMP-001)
- **FR-002** Fall back to page name for empty link text; keep plain wikilinks unchanged: When the text part of `[[<name>|<text>]]` is empty or whitespace-only, the extension SHALL render the same output as `[[<name>]]`. Wikilinks without `|` SHALL render exactly as they do before this change.
  - `AC-FR-002-01` given markdown.Markdown(extensions=['wikilinks']), when converting '[[Installation Guide|]]', then output is exactly '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-02` given markdown.Markdown(extensions=['wikilinks']), when converting '[[ Installation Guide |   ]]', then output is exactly '<p><a class="wikilink" href="/Installation_Guide/">Installation Guide</a></p>'
  - `AC-FR-002-03` given markdown.Markdown(extensions=['wikilinks']), when converting 'Some text with a [[WikiLink]].', '[[ foo bar_baz ]]' and 'foo [[ ]] bar', then outputs are exactly '<p>Some text with a <a class="wikilink" href="/WikiLink/">WikiLink</a>.</p>', '<p><a class="wikilink" href="/foo_bar_baz/">foo bar_baz</a></p>' and '<p>foo  bar</p>'; all existing TestWikiLinks tests and the legacy tests/extensions/wikilinks.txt -> wikilinks.html test still pass unmodified
  - `AC-FR-002-04` given markdown.Markdown(extensions=['wikilinks']), when converting 'foo [[ |text]] bar', then output contains no '<a' element (PROVISIONAL, see ASSUMP-002 / Q-002); recommended exact output '<p>foo  bar</p>'
  - `AC-FR-002-05` given markdown.Markdown(extensions=['wikilinks']), when converting '[[a|b|c]]', then output is exactly '<p>[[a|b|c]]</p>' (PROVISIONAL, see ASSUMP-003 / Q-003)

### Change plan (from design.md)

| File | Symbol | Change |
|---|---|---|
| `markdown/extensions/wikilinks.py` | `WikiLinkExtension.extendMarkdown` | modify: set `WIKILINK_RE = r'\[\[([\w0-9_ -]+)(?:\ |
| `markdown/extensions/wikilinks.py` | `WikiLinksInlineProcessor.handleMatch` | modify: compute `text = self._restore_raw_html((m.group(2) or '')).strip()` before falling back to `label`. Everything else stays as it is: label strip, `build_url(label, base_url, end_url)`, `_getMeta`, class handling, `''` for an empty name. |
| `markdown/extensions/wikilinks.py` | `(new) WikiLinksInlineProcessor._restore_raw_html` | add: a method that uses `util.HTML_PLACEHOLDER_RE.sub` to replace each placeholder whose `self.md.htmlStash.rawHtmlBlocks[int(n)]` is a `str` starting with `<` with that raw string. Any other placeholder, or a missing key (`IndexError`/`ValueError`), stays as it is. Add `from .. import util` to the imports. |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkText` | modify: replace the `[[Page\ |
| `tests/test_extensions.py` | `TestWikiLinks.testCustomLinkTextSettings` | modify: add the exact spec cases AC-FR-001-03 (`Some text with a [[WikiLink\ |
| `tests/test_extensions.py` | `(new) TestWikiLinks.testCustomLinkTextEntityAndBrackets` | add: `[[foo\ |

### Tests (from test_report.md)

Full suite with the new acceptance tests: **OK (skipped=52)** (1183 tests)

---
## Stage 5 check (orchestrator)

- PR: https://github.com/AlooKaLaddoo/markdown/pull/11
- PR state: OPEN
- CI (`ci.yml` on `autose/issue-3`): success https://github.com/AlooKaLaddoo/markdown/actions/runs/45424986492
- Result: **PASS** 
