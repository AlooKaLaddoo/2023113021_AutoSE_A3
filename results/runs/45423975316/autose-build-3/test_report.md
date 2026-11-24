# test_report.md (issue #3, round 1)

Existing suite on the base commit: **OK (skipped=52)** (1166 tests)

## Acceptance criteria → tests

| Acceptance criterion | Tests |
|---|---|
| AC-FR-001-01 | test_ac_fr_001_01_basic_piped_link |
| AC-FR-001-02 | test_ac_fr_001_02_whitespace_ignored |
| AC-FR-001-03 | test_ac_fr_001_03_simple_settings |
| AC-FR-001-04 | test_ac_fr_001_04_empty_html_class |
| AC-FR-001-05 | test_ac_fr_001_05_metadata_overrides |
| AC-FR-001-06 | test_ac_fr_001_06_build_url_receives_page_name |
| AC-FR-001-07 | test_ac_fr_001_07_internal_whitespace_preserved |
| AC-FR-001-08 | test_ac_fr_001_08_special_characters_escaped |
| AC-FR-002-01 | test_ac_fr_002_01_empty_text_falls_back |
| AC-FR-002-02 | test_ac_fr_002_02_whitespace_text_falls_back |
| AC-FR-002-03 | test_ac_fr_002_03_plain_wikilinks_unchanged |
| AC-FR-002-04 | test_ac_fr_002_04_empty_page_name_no_link |
| AC-FR-002-05 | test_ac_fr_002_05_multiple_pipes_literal |

New acceptance tests on the *base* commit (they should fail for a bug/feature): **FAILED (failures=10)** (13 tests)

## Attempts

| # | Build | Full suite | Note |
|---|---|---|---|
| 1 | pass | OK (skipped=52) |  |

## Final full run: **OK (skipped=52)** (1183 tests)

```
.................................................................................................................................................s................................................................................sssssssssssssssssssssssssssssssssssssssssssssss............................................................................ss.......................................................................................................................................................................................................................ss.......................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 1183 tests in 1.197s

OK (skipped=52)

```
