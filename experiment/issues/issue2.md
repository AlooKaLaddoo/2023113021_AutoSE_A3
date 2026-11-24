# RecursionError on deeply nested lists takes down our server

**Type:** bug (real upstream bug, fixed upstream after our pinned commit in `7d0d95a`)

We render user comments with Python-Markdown. Someone posted a comment that is just a long run of
list markers and the worker crashed with `RecursionError`:

```python
>>> import markdown
>>> markdown.markdown('- ' * 500 + 'x')
Traceback (most recent call last):
  ...
RecursionError: maximum recursion depth exceeded
```

Same with ordered lists (`'1. ' * 500 + 'x'`) and with a few hundred lines that are each indented a
bit more than the previous one. It's only about 1 KB of input, so anyone can trigger it.

I don't care if a 500-level list renders "correctly" (nobody needs that), but it must not raise.
Normal nested lists (2-3 levels) should of course look exactly like they do today. I believe
blockquotes already have some protection against this.
