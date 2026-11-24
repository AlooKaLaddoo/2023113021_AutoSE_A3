# Hidden acceptance tests

Kept outside the fork, so no agent can read them. 2-4 tests per issue.

| Issue | File | Tests | Source | On base `3f2c551` | On reference fix |
|---|---|---|---|---|---|
| 1 bug: toc crash on bare `{id}` | `test_issue1.py` | 4 | 2 upstream (`dc26ab5`) + 2 ours | 3 error, 1 pass (guard) | 4 pass |
| 2 bug: RecursionError on deep lists | `test_issue2.py` | 4 | upstream (`7d0d95a`) | 3 error, 1 pass (guard) | 4 pass |
| 3 feature: `[[Page\|text]]` wikilinks | `test_issue3.py` | 4 | A2 task T2 | 4 fail | 4 pass |
| 4 feature: `~~strikethrough~~` | `test_issue4.py` | 4 | ours | 4 error | 4 pass |
| 5 vague: toc ids for non-Latin text | `test_issue5.py` | 4 | ours | 1 fail, 3 pass (guards) | 4 pass |

`reference_solutions.patch` holds the reference fixes (upstream fixes for issues 1-2, A2's `T2_reference.patch` for issue 3, our own for 4-5). With it, the full existing suite still passes (1078 tests, 52 skipped).

Score a checkout (after `pip install -e '.[testing]'`):

```bash
python -m unittest discover -s /path/to/hidden_tests -p 'test_issue3.py' -t /path/to/hidden_tests
```
