I added the `between` command and four CLI tests for it. All 26 tests pass (`python -m unittest`). I couldn't run the command against `data/sample.csv` myself because the permission prompt for that shell command wasn't approved, so it has only been exercised through the tests.

`python -m expenses between 2026-09-03 2026-09-15` prints each expense in the range in the same format as `list`, then a `total` line. Both dates are included in the range.

**Changes:**
- **`expenses/cli.py`**: the new command uses the existing `expenses_between` and `total` functions from `report.py`, so there's no new calculation code. Each date goes through a new `iso_date` check: a bad date is rejected by argparse with `invalid date: '…', expected YYYY-MM-DD` and exit code 2.
- **Start date after end date:** this can't be caught while checking one argument at a time, so `main` checks it after parsing and calls `parser.error(...)`. That gives the same exit code 2 and message style as other bad input. To do this, `main` now keeps the parser in a local variable.
- **`tests/test_cli.py`** covers:
  - expenses on the start and end dates are kept, the days just outside are left out, and the total is correct (114.75);
  - a range with no expenses prints only `total 0.00`;
  - an invalid start or end date (`2026-13-01`, `tomorrow`) exits with code 2 and the "invalid date" message;
  - a start date after the end date exits with code 2 and the "must not be after" message.
- **`README.md`**: one usage line added to `## Usage`.

The filtering logic already had its own tests in `tests/test_report.py`, so I didn't add any there.