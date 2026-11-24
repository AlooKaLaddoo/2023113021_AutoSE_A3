## AutoSE independent review: ❌ REQUEST CHANGES

Reviewer: `claude-sonnet-5-5` (variant `main`), fresh context: issue + diff + repository at `d9954805a9`; no access to the spec, design, test report or implementer transcript.

**Summary.** The PR keeps Hindi and other Indic combining marks in `slugify_unicode` and adds docs and tests, but it introduces a regression. Emoji with a variation selector (U+FE0F, category `Mn`) now leave invisible characters in the id. The default `slugify` is unchanged, so default-config Hindi and Russian headings still produce `#_1`, `#_2`. The full suite passes (1185 tests, 52 skipped).

**What the issue asks for** (listed before reading the diff):
- Hindi and Russian headings should get readable, meaningful ids instead of _1, _2, ...
- Section links should be shareable and understandable
- Improve the toc extension for non-English docs
- Existing behaviour (default ASCII slugify, other unicode handling) should not regress

**Checklist**

- [ ] addresses every issue point
- [x] existing tests pass
- [x] own probe done
- [ ] no regression found
- [x] fits codebase design
- [x] no out of scope changes

**Findings**

| Severity | Location | Problem | Evidence |
|---|---|---|---|
| major | `markdown/extensions/toc.py:48` | Keeping every Mn/Mc character is too broad and regresses emoji headings. Emoji variation selectors (U+FE0F, category Mn) are now kept while the emoji itself (So) is dropped. Ids start with an invisible character, and emoji-only headings get a non-empty invisible id instead of the empty-slug fallback (`_1`). Old logic gave 'love' and ''. | `slugify_unicode('❤️ Love','-')` printed `'️-love'`, and `slugify_unicode('❤️','-')` printed `'️'`. `markdown.markdown('# ❤️ Love', extensions=[TocExtension(slugify=slugify_unicode)])` printed `<h1 id="️-love">`. The old regex `re.sub(r'[^\w\s-]','',v)` on the same inputs gave 'love' and ''. A combining mark should only be kept when it follows a kept base character, or variation selectors (U+FE00–FE0F) should be excluded. |
| major | `markdown/extensions/toc.py:41` | The issue reporter's complaint is about the default configuration, which is unchanged. Hindi and Russian headings with default settings still produce `_1`, `_2`. Russian already worked with `slugify_unicode` before this PR, so the only code change addresses Hindi marks. The docs note that `slugify_unicode` keeps non-Latin scripts, but nothing says the default drops them or points users hitting `_1` to the option, for example in the `slugify` option description or a warning near the default. The scope may be acceptable for backward compatibility, but the discoverability gap remains. | `markdown.markdown('# Привет мир\n## नमस्ते', extensions=['toc'])` printed `<h1 id="_1">Привет мир</h1>\n<h2 id="_2">नमस्ते</h2>`. |
| minor | `tests/test_autose_issue_5.py:1` | This new test file duplicates most of the tests added to tests/test_syntax/extensions/test_toc.py: Hindi, Cyrillic, punctuation, and the default-unchanged case. Tests that read the docs file by string matching are brittle. No test covers combining marks on characters that are otherwise dropped, such as emoji variation selectors. | Diff shows the same assertions in both files, for example `slugify_unicode('हिन्दी', '-')` and `'# Привет мир'`. |
| minor | `markdown/extensions/toc.py:47` | Zero-width joiner and non-joiner (U+200D, U+200C, category Cf) are still stripped, so conjuncts like 'क्‍ष' lose their joiner. The id is still readable, so this is cosmetic. The per-character `re.match` is also slower than a single compiled regex. | `slugify_unicode('क्‍ष','-')` printed `'क्ष'`. |

**Commands the reviewer ran**

- `python -m unittest discover -s tests -t .`
- `python -c slugify_unicode probes on Hindi, Cyrillic, Arabic, Korean, ZWJ, accents`
- `python -c slugify_unicode('❤️ Love') and markdown.markdown('# ❤️ Love', extensions=[TocExtension(slugify=slugify_unicode)])`
- `python -c re-implementation of the old slugify_unicode regex on '❤️ Love' and '❤️'`
- `python -c markdown.markdown('# Привет мир\n## नमस्ते', extensions=['toc'])`

Reviewer's own verdict: `request_changes`, proposed route: `implementation`.

**Orchestrator decision:** `request_changes` → route `implementation` (2 blocker/major finding(s) with evidence).

_A human maintainer decides whether to merge. The workflow never merges._
