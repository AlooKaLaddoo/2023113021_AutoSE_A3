# test_report.md (issue #4, round 1)

Existing suite on the base commit: **OK (skipped=52)** (1166 tests)

## Acceptance criteria → tests

| Acceptance criterion | Tests |
|---|---|
| AC-FR-001-01 | test_ac_fr_001_01_load_by_short_name |
| AC-FR-001-02 | test_ac_fr_001_02_load_by_dotted_path |
| AC-FR-001-03 | test_ac_fr_001_03_unchanged_without_extension |
| AC-FR-001-04 | test_ac_fr_001_04_fenced_code_alongside |
| AC-FR-002-01 | test_ac_fr_002_01_plain_in_sentence |
| AC-FR-002-02 | test_ac_fr_002_02_nested_inline_markup |
| AC-FR-002-03 | test_ac_fr_002_03_inside_emphasis |
| AC-FR-002-04 | test_ac_fr_002_04_multiple_spans |
| AC-FR-002-05 | test_ac_fr_002_05_code_span_unaffected |
| AC-FR-003-01 | test_ac_fr_003_01_single_tildes_literal |
| AC-FR-003-02 | test_ac_fr_003_02_unclosed_double_tilde |
| AC-FR-003-03 | test_ac_fr_003_03_whitespace_flanked_delimiters |
| AC-FR-003-04 | test_ac_fr_003_04_three_tildes_not_delimiter |
| AC-FR-003-05 | test_ac_fr_003_05_escaped_tildes_literal |

New acceptance tests on the *base* commit (they should fail for a bug/feature): **FAILED (errors=13)** (14 tests)

## Attempts

| # | Build | Full suite | Note |
|---|---|---|---|
| 1 | pass | OK (skipped=52) |  |

## Final full run: **OK (skipped=52)** (1200 tests)

```
..............................................................................................................................................s................................................................................sssssssssssssssssssssssssssssssssssssssssssssss............................................................................ss.......................................................................................................................................................................................................................ss...........................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 1200 tests in 0.944s

OK (skipped=52)

```
