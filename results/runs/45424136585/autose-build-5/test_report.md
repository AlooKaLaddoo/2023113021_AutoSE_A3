# test_report.md (issue #5, round 1)

Existing suite on the base commit: **OK (skipped=52)** (1166 tests)

## Acceptance criteria → tests

| Acceptance criterion | Tests |
|---|---|
| AC-FR-001-01 | test_ac_fr_001_01_russian_heading_readable_id, test_ac_fr_001_01_fallback_uses_composed_characters |
| AC-FR-001-02 | test_ac_fr_001_02_multi_word_russian_uses_separator_and_toc_link |
| AC-FR-001-03 | test_ac_fr_001_03_duplicate_non_latin_headings_unique |
| AC-FR-001-04 | test_ac_fr_001_04_latin_and_extended_latin_unchanged |
| AC-FR-001-05 | test_ac_fr_001_05_mixed_latin_cyrillic_keeps_ascii_slug |
| AC-FR-001-06 | test_ac_fr_001_06_no_word_characters_falls_back_to_numbered_id |
| AC-FR-001-07 | test_ac_fr_001_07_user_slugify_callable_used_as_is |
| AC-FR-002-01 | test_ac_fr_002_01_hindi_heading_keeps_vowel_signs_by_default |
| AC-FR-002-02 | test_ac_fr_002_02_hindi_multi_word_keeps_marks_with_slugify_unicode |
| AC-FR-002-03 | test_ac_fr_002_03_punctuation_still_stripped_from_unicode_slugs |
| AC-FR-002-04 | test_ac_fr_002_04_ascii_mode_strips_latin_accents |

## Attempts

| # | Build | Full suite | Note |
|---|---|---|---|
| 1 | pass | OK (skipped=52) |  |

## Final full run: **OK (skipped=52)** (1183 tests)

```
............................................................................................................................................s................................................................................sssssssssssssssssssssssssssssssssssssssssssssss............................................................................ss.......................................................................................................................................................................................................................ss............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 1183 tests in 1.879s

OK (skipped=52)

```
