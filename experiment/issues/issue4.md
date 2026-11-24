# Support ~~strikethrough~~ like GitHub

**Type:** feature

GitHub, GitLab and most chat tools render `~~text~~` as struck-through text. Python-Markdown leaves
the tildes in the output, so our changelogs (which strike out withdrawn items) look broken when we
build the docs.

Could there be a built-in extension for this, so I can write
`markdown.markdown(text, extensions=['strikethrough'])`? It should produce `<del>...</del>` like
GitHub does, and other inline markup inside it (bold, emphasis, links) should still work. A single
`~` or an unclosed `~~` should be left alone, and it should be off unless the extension is enabled.
