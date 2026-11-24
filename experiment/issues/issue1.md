# TypeError in toc when a heading has a bare `{id}` attribute

**Type:** bug (real upstream bug, fixed upstream after our pinned commit in `dc26ab5`, upstream issue #1705)

I'm using `toc` together with `attr_list`. One of my headings ended up with an empty attribute
block like `{id}` (I was going to fill in the id later and forgot), and instead of just rendering the
page, Markdown crashes:

```python
>>> import markdown
>>> markdown.markdown('#d {id}', extensions=['toc', 'attr_list'])
Traceback (most recent call last):
  ...
TypeError: expected string or bytes-like object, got 'NoneType'
```

It happens with and without a `[TOC]` marker in the document. I'd expect it to just behave as if
no id was given (generate the normal slug), not crash the whole build. Headings with a real id like
`# Title {#my-id}` work fine.

Python 3.12, Markdown at the current `master`.
