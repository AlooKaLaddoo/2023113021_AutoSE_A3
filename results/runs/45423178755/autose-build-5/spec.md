# Spec: TOC is kind of useless for non-English docs

## 1. Summary and scope

The reporter writes docs in Hindi and Russian. With the `toc` extension, every heading gets an id like `_1`, `_2`, and so on, so shared section links say nothing about where they go.

**Current behaviour (checked in the code):**
- The default `slugify` (`markdown/extensions/toc.py:39-46`) runs NFKD normalization, then encodes to ASCII with `'ignore'`. All Cyrillic and Devanagari characters are dropped, so the slug is `""`. Then `unique()` (`markdown/extensions/toc.py:57-65`) treats an empty id as a collision and returns `_1`, `_2`, and so on. That is the behaviour the issue describes. [FACT]
- An opt-in `slugify_unicode` already exists (`markdown/extensions/toc.py:49-51`). It is documented in one sentence (`docs/extensions/toc.md:219-220`) and covered by tests with Japanese text only (`tests/test_syntax/extensions/test_toc.py:1198-1218`). [FACT]
- `slugify_unicode` removes characters with `re.sub(r'[^\w\s-]', '', value)`. Python's `\w` does not match combining marks (Unicode categories Mn and Mc). Devanagari vowel signs and the virama are combining marks, so `slugify_unicode` breaks Hindi words. For example, `नमस्ते दुनिया` becomes `नमसत-दनय`. [INFERRED from reading the code and Python `re` semantics; not run]

**In scope**
- `slugify_unicode` keeps combining marks (Mn, Mc), so ids made from Hindi or other Indic text stay readable.
- The `slugify` option docs in `docs/extensions/toc.md` get a concrete example of using `slugify_unicode` for non-Latin headings.

**Out of scope**
- Changing the default `slugify`, so that existing ASCII ids stay the same (see ASSUMP-001 and Q-001).
- Transliteration, for example Cyrillic to Latin (see Q-002).
- Changes to `unique()` or the `_n` suffix scheme.
- Anything under `.github/`.

## 2. Functional requirements

```yaml
id: "FR-001"
title: "Preserve combining marks in slugify_unicode"
statement: "The function markdown.extensions.toc.slugify_unicode SHALL keep characters of Unicode categories Mn and Mc in the generated slug, while keeping all its current behaviour for other characters (lowercasing, removal of non-word punctuation, separator collapsing)."
epistemic_status: "INFERRED"
source: "Issue #5: 'We write our docs in Hindi and Russian ... links are all #_1, #_2'; markdown/extensions/toc.py:45 (re.sub(r'[^\\w\\s-]', '', value)) drops Mn/Mc characters"
actor: "Documentation author using the toc extension with slugify=slugify_unicode"
priority: "MUST_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["ASSUMP-001", "ASSUMP-002"]
inputs: [{name: "value", type: "str", description: "Heading text"}, {name: "separator", type: "str", description: "Word separator, default '-'"}]
outputs: [{name: "slug", type: "str", description: "Id string used for the heading and the TOC link"}]
acceptance_criteria:
  - id: "AC-FR-001-01"
    scenario: "Hindi heading keeps vowel signs and virama"
    given: "Markdown source '# नमस्ते दुनिया' and extensions=[TocExtension(slugify=slugify_unicode)]"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"नमस्ते-दुनिया\">नमस्ते दुनिया</h1>'"
  - id: "AC-FR-001-02"
    scenario: "Direct call on Hindi text with combining marks"
    given: "value='हिन्दी', separator='-'"
    when: "slugify_unicode(value, separator) is called"
    then: "Return value is exactly 'हिन्दी'"
  - id: "AC-FR-001-03"
    scenario: "Russian heading (existing behaviour unchanged)"
    given: "Markdown source '# Привет мир' and extensions=[TocExtension(slugify=slugify_unicode)]"
    when: "markdown.markdown is called"
    then: "Output is exactly '<h1 id=\"привет-мир\">Привет мир</h1>'"
  - id: "AC-FR-001-04"
    scenario: "Punctuation still removed, Japanese unchanged (existing behaviour)"
    given: "value='Unicode ヘッダー!?', separator='-'"
    when: "slugify_unicode(value, separator) is called"
    then: "Return value is exactly 'unicode-ヘッダー'; the existing tests testPermalinkWithUnicodeInID and testPermalinkWithUnicodeTitle still pass"
  - id: "AC-FR-001-05"
    scenario: "Default slugify unchanged"
    given: "value='Théâtre', separator='-' and value='Привет мир', separator='-'"
    when: "markdown.extensions.toc.slugify(value, separator) is called"
    then: "Returns exactly 'theatre' and exactly '' respectively; the existing test testPermalinkWithExtendedLatinInID still passes"
verification_method: "TEST"
```

```yaml
id: "FR-002"
title: "Document a concrete non-Latin slugify_unicode example"
statement: "The `slugify` option entry in docs/extensions/toc.md SHALL contain a usage example that passes slugify_unicode to TocExtension and shows the exact id produced for a Cyrillic heading."
epistemic_status: "INFERRED"
source: "Issue #5: 'Can toc be improved for this?'; docs/extensions/toc.md:219-220 mentions slugify_unicode in one sentence with no example"
actor: "Documentation author writing non-English docs"
priority: "SHOULD_HAVE"
readiness_status: "PROVISIONAL"
dependencies: ["FR-001", "ASSUMP-001"]
inputs: [{name: "docs/extensions/toc.md", type: "file", description: "Extension documentation"}]
outputs: [{name: "docs/extensions/toc.md", type: "file", description: "Updated documentation"}]
acceptance_criteria:
  - id: "AC-FR-002-01"
    scenario: "Example shows the configuration"
    given: "The file docs/extensions/toc.md after the change"
    when: "Its text is read as UTF-8"
    then: "It contains the exact substring 'TocExtension(slugify=slugify_unicode)' and the exact substring 'from markdown.extensions.toc import TocExtension, slugify_unicode'"
  - id: "AC-FR-002-02"
    scenario: "Example shows a Cyrillic heading and its exact id"
    given: "The file docs/extensions/toc.md after the change"
    when: "Its text is read as UTF-8"
    then: "It contains the exact substring '# Привет мир' and the exact substring '<h1 id=\"привет-мир\">Привет мир</h1>'"
  - id: "AC-FR-002-03"
    scenario: "Documented output matches actual output"
    given: "Markdown source '# Привет мир' and extensions=[TocExtension(slugify=slugify_unicode)]"
    when: "markdown.markdown is called"
    then: "The result equals exactly '<h1 id=\"привет-мир\">Привет мир</h1>', the same string required in AC-FR-002-02"
  - id: "AC-FR-002-04"
    scenario: "Existing default documented unchanged"
    given: "The file docs/extensions/toc.md after the change"
    when: "Its text is read as UTF-8"
    then: "It still contains the exact substring 'Default: `markdown.extensions.toc.slugify`'"
verification_method: "TEST"
```

## 3. Non-functional requirements

None.

## 4. Assumptions and open questions

- **ASSUMP-001** [INFERRED]: The default `slugify` stays ASCII-only, and the fix is delivered through the existing opt-in `slugify_unicode` plus documentation.
  - **Rationale:** Changing the default would change ids, and so break inbound links, for every existing user whose headings contain extended Latin characters (for example `Théâtre` would become `théâtre`).
  - **Impact if invalid:** MEDIUM. A maintainer who wants a new default would need an extra FR and a changelog/deprecation note.
  - **Validation path:** Q-001.
- **ASSUMP-002** [INFERRED]: Keeping combining marks (Mn, Mc) in `slugify_unicode` is acceptable even though decomposed Latin input such as `e` + U+0301 will now keep the accent instead of losing it.
  - **Rationale:** `slugify_unicode` exists to preserve Unicode. The changelog entry at `docs/changelog.md:443` ("not remove diacritical marks", #1118) shows this has been the intent before.
  - **Impact if invalid:** LOW.
  - **Validation path:** maintainer review.
- **Q-001:** Should the default `slugify` change to Unicode-preserving?
  - **Options:** (a) keep the ASCII default and document the opt-in. No breakage; users must opt in. (b) Switch the default. Readable out of the box, but it breaks existing ids. (c) Fall back to the Unicode slug only when the ASCII slug is empty. Fixes `#_1` with no breakage for ASCII-producing headings, but behaviour becomes harder to predict.
  - **Recommended default:** (a), adopted as ASSUMP-001. Affects FR-002.
- **Q-002:** Is transliteration (for example `Привет` → `privet`) wanted instead of native-script ids?
  - **Recommended default:** no. It needs language-specific tables, which this project does not have. It is out of scope and affects no FR.
- **Note (risk):** The issue text contains no instructions aimed at the pipeline. No prompt-injection attempt was found.

## 5. Validation

1. **Completeness:** PASS. Both FRs define actor, inputs, outputs, and both normal and edge/unchanged-behaviour criteria.
2. **Testability:** PASS. Every AC compares exact strings: function return values, `markdown.markdown` output, or exact substrings in `docs/extensions/toc.md`.
3. **Consistency:** PASS. FR-002's documented output (AC-FR-002-02) is the same string checked at runtime (AC-FR-002-03 and AC-FR-001-03).
4. **Feasibility:** PASS. The change is limited to `slugify_unicode`'s character filtering and one docs section, with existing test patterns at `tests/test_syntax/extensions/test_toc.py:1198-1218`.
5. **Traceability:** PASS. Each FR cites the issue text and code locations. The provisional status traces to ASSUMP-001, ASSUMP-002, Q-001 and Q-002.


---
## Stage 1 check (orchestrator, attempt 2)

Result: **PASS**

- AC-FR-001-01: testable=True (Gives a concrete Devanagari Markdown input with TocExtension(slugify=slugify_unicode) and an exact expected HTML string, so a unit test can assert equality.)
- AC-FR-001-02: testable=True (Specifies exact inputs to slugify_unicode and an exact expected return value, giving an unambiguous equality assertion.)
- AC-FR-001-03: testable=True (Specifies a Cyrillic Markdown input and the exact expected HTML output, which a test can compare directly.)
- AC-FR-001-04: testable=True (Specifies exact input and expected slug 'unicode-ヘッダー', and names existing tests whose pass/fail status is observable.)
- AC-FR-001-05: testable=True (Gives exact inputs to markdown.extensions.toc.slugify with exact expected outputs ('theatre' and '') plus a named existing test that can be run.)
- AC-FR-002-01: testable=True (Defines a file path and two exact substrings that can be checked by reading the file as UTF-8 and testing for containment.)
- AC-FR-002-02: testable=True (Defines a file path and two exact substrings to search for, giving a clear pass/fail containment check.)
- AC-FR-002-03: testable=True (Gives exact Markdown input, extension configuration, and the exact expected HTML output for an equality assertion.)
- AC-FR-002-04: testable=True (Defines a file path and an exact substring whose presence can be checked by a containment assertion.)
