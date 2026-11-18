I've written the tests in `tests/test_report.py` and `tests/test_cli.py` and changed nothing else. The new tests fail, and every failure is because the `month` feature doesn't exist yet. I ran `python -m unittest` twice: the first run's output was cut off, so I ran it again to see the summary.

**Result:** `Ran 23 tests, FAILED (failures=7, errors=9)`. All 14 existing CLI tests still pass.

## Why they fail

**1. `tests/test_report.py` can't be imported (1 error).**
`ImportError: cannot import name 'expenses_in_month' from 'expenses.report'`. That function isn't written yet, so the whole file fails to load. That's why only 23 tests ran: the 12 existing report tests in that file didn't run either, and will run again once `expenses_in_month` exists. The new report tests are:
- `test_expenses_in_month_only_that_month`: September and October picks from `SAMPLE`.
- `test_expenses_in_month_does_not_mix_years`: 2025-09 gives `[]`.
- `test_expenses_in_month_excludes_neighbouring_days`: from expenses on 11-30, 12-01, 12-31 and 2027-01-01, only the two December ones are kept.
- `test_expenses_in_month_keeps_input_order`
- `test_expenses_in_month_of_nothing_is_empty`
- `test_expenses_in_month_rejects_bad_month`: `ValueError` "month must be" for 0 and 13 (R8).

**2. Seven CLI tests error with `SystemExit: 2`** (8 errors, because one test has two subtests). argparse rejects `month` as an `invalid choice` because the subcommand doesn't exist, so `run()` gets `SystemExit` instead of an exit code:
- `test_month_shows_categories_largest_first_then_total`: the exact four lines for 2026-09.
- `test_month_october`: exact list, so food must come before transport (amendment C).
- `test_month_with_no_matches_prints_zero_total`: 2025-09 prints only the padded `total` line.
- `test_month_on_missing_or_empty_file_prints_zero_total`: two subtests, one missing file and one empty file. It also checks that the missing file is not created.
- `test_month_excludes_neighbouring_months`: the Dec/Jan acceptance case.
- `test_month_defaults_to_current_month`: adds an expense for today plus a decoy in another month.
- `test_month_does_not_write_file`: the file's bytes are the same before and after.

**3. Seven failures in `test_month_rejects_invalid_month`**, one per input: `2026-13`, `2026-00`, `2026-9`, `2026-09-15`, `abc`, `202609`, `""`. Each one already exits with code 2, but for the wrong reason (the unknown subcommand). The test catches that because it checks the **full** message `invalid month: '<text>', expected YYYY-MM` (amendment B). This is the failure that CLAUDE.md §5 warns a code-only check would miss.

## Choices I made
- **Test helpers:** I added `SAMPLE_ROWS`, `add_rows()` and `line()` to `test_cli.py`. `SAMPLE_ROWS` rebuilds the sample data with `add --date` in a temp directory, the same way the `between` tests do. `line()` builds the `f"{label:<12} {amount:>9.2f}"` string, so outputs are compared exactly rather than against the literal text in the spec (plan risk 4).
- **Full message for every input:** the rejection test checks the full message, empty stdout and that no file is written for all seven inputs. That covers amendment B for each input, so I didn't add a separate single-input test.
- **Extra cases beyond the plan:** an empty-file case (R5 says "missing or empty file"), an empty-list report test, and a decoy expense in the "today" test. Without the decoy, a `month` command that ignored the month and summed everything would still pass.
- **Not covered here:** amendment D (naming the subparser `month_cmd`) is about the implementation, so these tests can't check it.