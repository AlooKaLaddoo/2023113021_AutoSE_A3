# Wikilinks: allow custom link text with `[[Page Name|link text]]`

**Type:** feature (reused from A2 task T2)

We're moving our wiki from MediaWiki and use the `wikilinks` extension. Almost every page has links
like `[[Installation Guide|see the install docs]]`, where the part after `|` is the text that should
be shown. Right now these don't render as links at all.

Could `wikilinks` support `[[Page Name|link text]]`? The link should point exactly where
`[[Page Name]]` points (we rely on `base_url`, `end_url`, `html_class`, a custom `build_url` and the
`wiki_*` meta-data overrides), just with different text. Whitespace around the name or the text
shouldn't matter, and if the text part is empty just use the page name. Plain `[[Page Name]]` links
must keep working the same way.
