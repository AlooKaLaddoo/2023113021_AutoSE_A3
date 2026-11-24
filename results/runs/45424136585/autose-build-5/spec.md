# Spec: TOC is kind of useless for non-English docs

## 1. Summary and scope

The reporter writes documentation in Hindi and Russian. With the `toc` extension's default settings, every heading made only of non-Latin text gets an anchor of `_1`, `_2`, and so on. Shared section links therefore carry no meaning. The reporter asks whether `toc` can do better. [FACT]

Current behaviour, confirmed in the code:
- `markdown/extensions/toc.py:39-46`: the default `slugify` (with `unicode=False`) applies NFKD normalisation and then `encode('ascii', 'ignore')`. This removes all Cyrillic and Devanagari characters, so the slug is empty. [FACT]
- `markdown/extensions/toc.py:57-66`: `unique()` turns an empty id into `_1`, `_2`, ... [FACT]
- `markdown/extensions/toc.py:49-51`: `slugify_unicode` already exists as an opt-in (`slugify=slugify_unicode`), and `tests/test_syntax/extensions/test_toc.py:1198-1218` tests it with Japanese. [FACT]
- `markdown/extensions/toc.py:45`: in both modes, `re.sub(r'[^\w\s-]', '', value)` removes characters that are not `\w`. Python's `\w` does not match Unicode combining marks (categories Mn/Mc), such as Devanagari vowel signs and the virama. So even `slugify_unicode` changes Hindi words: `परिचय` becomes `परचय`. [INFERRED; to be confirmed by the test in AC-FR-002-01]

**In scope**
- When the default slugify would produce an empty slug, headings in non-Latin scripts get readable anchors made of their own letters (FR-001).
- Unicode slugs keep the combining marks that are part of words, so Hindi and other Indic text stays intact (FR-002).

**Out of scope**
- Transliteration (for example Cyrillic to Latin `vvedenie`). The issue does not ask for it, and it would need a new dependency.
- Changing slugs for headings whose ASCII slug is already non-empty (Latin, extended Latin, or mixed text).
- Changes to `unique()` suffix numbering, the `separator` option, or custom `slugify` callables supplied by users.
- Documentation changes. These may go with the change, but they are not covered by acceptance criteria.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Produce readable default anchors for non-Latin headings"
statement: "With the default `slugify` option, the toc extension SHALL use a slug that keeps the heading's Unicode word characters (lower-cased, whitespace replaced by the separator) whenever the ASCII-only slug would be empty, and SHALL keep the current ASCII slug in every other case."
epistemic_status: "INFERRED"
source: "Issue #5: 'the links are all `#_1`, `#_2`, ... nobody can tell where it goes ... Can toc be improved for this?'; markdown/extensions/toc.py:39-46, 57-66"
actor: "Documentation author writing in a non-Latin script; readers following shared links"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-002"]
inputs: [{name: "heading text", type: "str", description: "Markdown heading text in any script"}]
outputs: [{name: "id / TOC href", type: "str", description: "Heading id attribute and matching TOC link fragment"}]
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Russian heading gets a readable id by default"
    given: "Markdown source '# Введение' and extensions=['toc'] with default config"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"введение\">Введение</h1>'"
  - id: "AC-FR-001-02"
    scenario: "Multi-word Russian heading uses the separator, and the TOC links to it"
    given: "Markdown source '[TOC]\n\n# Быстрый старт' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output contains '<h1 id=\"быстрый-старт\">Быстрый старт</h1>' and '<a href=\"#быстрый-старт\">Быстрый старт</a>'"
  - id: "AC-FR-001-03"
    scenario: "Duplicate non-Latin headings get unique suffixed ids"
    given: "Markdown source '# Введение\n\n# Введение' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"введение\">Введение</h1>\n<h1 id=\"введение_1\">Введение</h1>'"
  - id: "AC-FR-001-04"
    scenario: "Existing behaviour unchanged: Latin and extended-Latin headings stay ASCII"
    given: "Markdown source '# Žlutý kůň\n\n# Hello World' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"zluty-kun\">Žlutý kůň</h1>\n<h1 id=\"hello-world\">Hello World</h1>'"
  - id: "AC-FR-001-05"
    scenario: "Existing behaviour unchanged: mixed Latin/Cyrillic heading keeps its ASCII slug"
    given: "Markdown source '# Setup Настройка' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"setup\">Setup Настройка</h1>'"
  - id: "AC-FR-001-06"
    scenario: "Edge case: heading with no word characters in any script still falls back to numbered id"
    given: "Markdown source '# !!!' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"_1\">!!!</h1>'"
  - id: "AC-FR-001-07"
    scenario: "Existing behaviour unchanged: a user-supplied slugify callable is used as-is"
    given: "Markdown source '# Введение' and extensions=[TocExtension(slugify=lambda value, separator: 'custom')]"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"custom\">Введение</h1>'"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Preserve combining marks in Unicode slugs"
statement: "When the toc extension produces a Unicode slug (via `slugify_unicode` or the FR-001 fallback), it SHALL keep Unicode combining marks (general categories Mn and Mc) that occur in the heading text, so that words in scripts such as Devanagari are not altered."
epistemic_status: "INFERRED"
source: "Issue #5: 'We write our docs in Hindi'; markdown/extensions/toc.py:45 (regex `[^\\w\\s-]` drops non-\\w characters)"
actor: "Documentation author writing in Hindi or another script that uses combining marks"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001", "ASSUMP-003"]
inputs: [{name: "heading text", type: "str", description: "Heading text containing combining marks"}]
outputs: [{name: "id / TOC href", type: "str", description: "Slug that keeps the marks"}]
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Hindi heading keeps vowel signs with default config"
    given: "Markdown source '# परिचय' and extensions=['toc']"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"परिचय\">परिचय</h1>'"
  - id: "AC-FR-002-02"
    scenario: "Hindi multi-word heading keeps virama and vowel signs with slugify_unicode"
    given: "Markdown source '# नमस्ते दुनिया' and extensions=[TocExtension(slugify=slugify_unicode)]"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"नमस्ते-दुनिया\">नमस्ते दुनिया</h1>'"
  - id: "AC-FR-002-03"
    scenario: "Existing behaviour unchanged: punctuation is still stripped from Unicode slugs"
    given: "Markdown source '# Unicode ヘッダー!' and extensions=[TocExtension(slugify=slugify_unicode)]"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"unicode-ヘッダー\">Unicode ヘッダー!</h1>'"
  - id: "AC-FR-002-04"
    scenario: "Existing behaviour unchanged: ASCII mode still strips accents from Latin text"
    given: "The function call slugify('Žlutý kůň', '-')"
    when: "It is evaluated"
    then: "It returns 'zluty-kun'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: The fix changes the default behaviour, but only for headings whose ASCII slug is empty. Those headings currently get the meaningless `_N` ids, so few useful existing links will break. Impact if invalid: MEDIUM. If maintainers require the default output to stay identical, FR-001 becomes documentation only and users would opt in with `slugify=slugify_unicode`. Validation: maintainer review of Q-001.
- **ASSUMP-002** [INFERRED]: Fallback slugs are lower-cased and use the configured `separator`, the same as `slugify_unicode` today (`toc.py:45-46`). Impact if invalid: LOW.
- **ASSUMP-003** [INFERRED]: Python's `re` `\w` does not match Mn/Mc combining marks, so Devanagari vowel signs and the virama are currently dropped. Impact if invalid: LOW. FR-002 would then already be satisfied, and its tests serve as regression tests.
- **Q-001**: Should non-Latin headings get readable ids by default, or only when the user opts in?
  - Option A: fall back to a Unicode slug only when the ASCII slug is empty. This is the minimal change and leaves Latin output unchanged.
  - Option B: make `slugify_unicode` the default. This changes ids for all accented Latin headings and breaks existing links.
  - Option C: change no code and document `slugify_unicode`. This does not help users who keep the default settings.
  - **Recommended default: A** (adopted as ASSUMP-001). Blocks: FR-001.
- **Q-002**: Is transliteration (for example `введение` to `vvedenie`) wanted, for ASCII-only URLs? Recommended default: no. It is out of scope, and percent-encoded Unicode fragments work in modern browsers. Blocks: none.
- **Risk**: The issue text contains no instructions aimed at the agent. No prompt-injection attempt was found.

## 5. Validation

1. **Completeness:** PASS. Both FRs define the actor, inputs and outputs, and have normal, edge and unchanged-behaviour criteria.
2. **Testability:** PASS. Every criterion is an exact `markdown.markdown` output or function return value that a unit test can check, and there are no subjective qualifiers.
3. **Consistency:** PASS. FR-001 and FR-002 do not conflict, and AC-FR-001-04, -05 and -07 and AC-FR-002-03 and -04 protect existing behaviour.
4. **Feasibility:** PASS. This needs only the standard library (`unicodedata`, `re`) inside `markdown/extensions/toc.py`.
5. **Traceability:** PASS. Each FR cites the issue text and code locations, and depends on ASSUMP-001 to ASSUMP-003 and Q-001.


---
## Stage 1 check (orchestrator, attempt 2)

Result: **PASS**

- AC-FR-001-01: testable=True (Gives a concrete Markdown input, config, and an exact expected HTML string, so a test can assert equality.)
- AC-FR-001-02: testable=True (Gives a concrete input with a [TOC] marker and specific substrings that the output must contain, so a test can check for them.)
- AC-FR-001-03: testable=True (Gives duplicate headings and an exact expected output including the _1 suffix for the second id, so a test can assert equality.)
- AC-FR-001-04: testable=True (Gives non-ASCII headings and an exact expected output with the transliterated ids, so a test can assert equality.)
- AC-FR-001-05: testable=True (Gives a mixed Latin and Cyrillic heading and an exact expected output, so a test can assert equality.)
- AC-FR-001-06: testable=True (Gives a heading with only punctuation and an exact expected output including the _1 fallback id, so a test can assert equality.)
- AC-FR-001-07: testable=True (Supplies a custom slugify callable that returns a fixed value, and the expected output id is that exact value, so a test can assert equality.)
- AC-FR-002-01: testable=True (Gives a Devanagari heading with the toc extension and an exact expected output, so a test can assert equality.)
- AC-FR-002-02: testable=True (Gives a Devanagari heading, names the slugify_unicode function, and provides an exact expected output; the function is assumed to be the library's own implementation.)
- AC-FR-002-03: testable=True (Gives a mixed Latin and Japanese heading with punctuation and an exact expected output, so a test can assert equality.)
- AC-FR-002-04: testable=True (Gives a direct function call with concrete arguments and an exact return value, so a test can assert equality.)
