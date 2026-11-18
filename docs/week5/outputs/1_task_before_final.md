I added the `between` command. `python -m expenses between 2026-09-03 2026-09-15` lists every expense dated in that range, including both end dates, and then prints a `total` line. All 28 tests pass, including the 6 new ones. I couldn't run the command against `data/sample.csv` because that call needed approval that wasn't given here, so I haven't seen its real output. The new tests run the same code path.

**Changes in `expenses/cli.py`:**
- **The command:** it takes two `YYYY-MM-DD` arguments. It reuses the existing `expenses_between()` in `report.py` (which already includes both end dates) and `total()`.
- **Output format:** each expense is printed the same way `list` prints it, and the total line looks like the one in `summary`. To keep the formats identical I moved the line formatting into a shared `print_expense()` helper, which `list` now uses too.
- **Bad input:** a badly formed date, or a start date after the end date, prints a usage error and exits with code 2. This matches how `add` handles bad input, rather than crashing with a traceback.
- **No matches:** if nothing falls in the range, including when the file is missing, it prints just `total 0.00`.

**Tests in `tests/test_cli.py` (new `BetweenTests` class):** the test data has expenses on each end date and on the days just outside the range. The tests check:
- that the right rows are listed, in their original order, with a total of 34.75
- a range of a single day
- an empty range
- a missing file
- that a start date after the end date is rejected with the error message
- that invalid dates are rejected

To try it yourself: `python -m expenses --file data/sample.csv between 2026-09-03 2026-09-15`