# test_report.md (issue #1, round 1)

Existing suite on the base commit: **OK (skipped=52)** (1166 tests)

## Acceptance criteria → tests

| Acceptance criterion | Tests |
|---|---|
| AC-FR-001-01 | test_ac_fr_001_01_reported_reproduction |
| AC-FR-001-02 | test_ac_fr_001_02_bare_id_with_toc_marker |
| AC-FR-001-03 | test_ac_fr_001_03_generated_slug_is_unique |
| AC-FR-001-04 | test_ac_fr_001_04_bare_id_with_other_attributes |
| AC-FR-001-05 | test_ac_fr_001_05_bare_id_with_permalink, test_ac_fr_001_05_bare_id_with_anchorlink |
| AC-FR-002-01 | test_ac_fr_002_01_explicit_id_not_overridden |
| AC-FR-002-02 | test_ac_fr_002_02_heading_without_attributes_gets_slug |
| AC-FR-002-03 | test_ac_fr_002_03_existing_toc_and_attr_list_tests_pass |
| AC-FR-002-04 | test_ac_fr_002_04_valueless_id_without_toc_unchanged |

New acceptance tests on the *base* commit (they should fail for a bug/feature): **FAILED (errors=6)** (10 tests)

## Attempts

| # | Build | Full suite | Note |
|---|---|---|---|
| 1 | pass | OK (skipped=52) |  |

## Final full run: **OK (skipped=52)** (1185 tests)

```
..........................................................................................................................................s................................................................................sssssssssssssssssssssssssssssssssssssssssssssss............................................................................ss.......................................................................................................................................................................................................................ss................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................................
----------------------------------------------------------------------
Ran 1185 tests in 1.608s

OK (skipped=52)

```
