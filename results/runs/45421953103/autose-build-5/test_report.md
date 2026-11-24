# test_report.md (issue #5, round 1)

Existing suite on the base commit: **OK (skipped=52)** (1166 tests)

## Acceptance criteria → tests

| Acceptance criterion | Tests |
|---|---|
| AC-FR-001-01 | test_ac_fr_001_01_hindi_heading_keeps_vowel_signs_and_virama |
| AC-FR-001-02 | test_ac_fr_001_02_direct_call_hindi_combining_marks |
| AC-FR-001-03 | test_ac_fr_001_03_russian_heading_unchanged |
| AC-FR-001-04 | test_ac_fr_001_04_punctuation_removed_japanese_unchanged, test_ac_fr_001_04_permalink_with_unicode_in_id_still_passes, test_ac_fr_001_04_permalink_with_unicode_title_still_passes |
| AC-FR-001-05 | test_ac_fr_001_05_default_slugify_extended_latin, test_ac_fr_001_05_default_slugify_cyrillic_empty, test_ac_fr_001_05_permalink_with_extended_latin_in_id_still_passes |
| AC-FR-002-01 | test_ac_fr_002_01_docs_show_configuration |
| AC-FR-002-02 | test_ac_fr_002_02_docs_show_cyrillic_heading_and_id |
| AC-FR-002-03 | test_ac_fr_002_03_documented_output_matches_actual |
| AC-FR-002-04 | test_ac_fr_002_04_default_documented_unchanged |

New acceptance tests on the *base* commit (they should fail for a bug/feature): **FAILED (failures=4)** (13 tests)

## Attempts

| # | Build | Full suite | Note |
|---|---|---|---|
| 1 | pass | OK (skipped=52) |  |

## Final full run: **OK (skipped=52)** (1185 tests)

```
.............................................................................................................................................s................................................................................sssssssssssssssssssssssssssssssssssssssssssssss............................................................................ss.......................................................................................................................................................................................................................ss.............................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 1185 tests in 1.490s

OK (skipped=52)

```
