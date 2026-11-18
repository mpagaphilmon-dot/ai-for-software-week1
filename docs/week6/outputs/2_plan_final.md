# Implementation plan: `month` command

I read `expenses/*.py`, `tests/*.py`, `README.md` and `data/sample.csv`. I did not change any files. I tried to run a short Python check of how `date.fromisoformat` handles odd inputs, but that command wasn't approved, so risk 1 below rests on what I know rather than a test run.

## Changes, in order

**1. `expenses/report.py`**: add a new function below `monthly_total` (line 32) and above the `expenses_between` comment block. Leave `monthly_total` unchanged.
```python
def expenses_in_month(expenses, year, month):
    """Expenses dated in the given year and month, in their original order (no rounding)."""
    if not 1 <= month <= 12:
        raise ValueError("month must be from 1 to 12")
    return [e for e in expenses if e.day.year == year and e.day.month == month]
```
Matching on `year` and `month` avoids working out the last day of the month, which would need `calendar`, a module CLAUDE.md §7 doesn't list. The `ValueError` follows CLAUDE.md §4 (see risk 3).

**2. `expenses/cli.py`**
- Change line 6 to also import `expenses_in_month` and `monthly_total`.
- Add `year_month(text)` after `iso_date` (line 32). Base it on CLAUDE.md §6, which returns `(year, month)` and raises `ArgumentTypeError(f"invalid month: {text!r}, expected YYYY-MM")`. Add a shape check before `fromisoformat`: `len(text) == 7 and text[4] == "-" and text.isascii()`, with the year and month parts both digits (see risk 1).
- In `build_parser`, after the `between` block and before `return parser`:
  `month = commands.add_parser("month", help="show one month's totals per category, then the month total")`
  `month.add_argument("month", nargs="?", type=year_month, default=None, help="YYYY-MM, defaults to the current month")`
- In `main`, add a `month` branch after the `between` branch (line 87) and before the summary code. Use a new variable name such as `selected`, because the name `month` already holds the subparser and the argument:
  ```python
  if args.command == "month":
      year, month = args.month or (date.today().year, date.today().month)
      for category, amount in total_by_category(expenses_in_month(expenses, year, month)).items():
          print(f"{category:<12} {amount:>9.2f}")
      print(f"{'total':<12} {monthly_total(expenses, year, month):>9.2f}")
      return 0
  ```
  Call `date.today()` once and store it, so a run at midnight can't mix two dates. `storage.py` already lower-cases categories, and the branch never writes (R7).

**3. `README.md`**: add `python -m expenses month 2026-09` to `## Usage`, after the `between` line.

## Tests to add

**`tests/test_report.py`** (add `expenses_in_month` to the import):
- `test_expenses_in_month_only_that_month`: on `SAMPLE`, (2026, 9) returns `SAMPLE[0:4]` and (2026, 10) returns `SAMPLE[4:6]`.
- `test_expenses_in_month_does_not_mix_years`: on `SAMPLE`, (2025, 9) returns `[]`.
- `test_expenses_in_month_excludes_neighbouring_days`: from expenses on 11-30, 12-01, 12-31 and 2027-01-01, (2026, 12) keeps only the two December ones.
- `test_expenses_in_month_keeps_input_order`: a shuffled list keeps its order.
- `test_expenses_in_month_rejects_bad_month`: `assertRaisesRegex(ValueError, "month must be")` for 0 and 13.

**`tests/test_cli.py`**: each test uses `run()`, `TemporaryDirectory` and `--file`. The sample data is rebuilt with `add ... --date`, as in the `between` tests.
- `test_month_shows_categories_largest_first_then_total`: for `2026-09`, the output is exactly the four formatted lines rent 650.00, food 61.40, transport 3.20, total 714.60, with exit 0.
- `test_month_october`: food 9.75, transport 3.20, total 12.95.
- `test_month_with_no_matches_prints_zero_total`: on the sample data, `2025-09` gives `[f"{'total':<12} {0:>9.2f}"]`. Run it again on a missing file for the same result.
- `test_month_excludes_neighbouring_months`: the Dec/Jan acceptance case. Only the two December amounts and their total appear.
- `test_month_defaults_to_current_month`: `add food 7` with no `--date`, then `month` with no argument, prints a food 7.00 line and a total 7.00 line.
- `test_month_does_not_write_file`: the file's bytes are the same before and after `month 2026-09`.
- `test_month_rejects_invalid_month`: run subtests for `2026-13`, `2026-00`, `2026-9`, `2026-09-15` and `abc`. Each must give exit 2, `"invalid month"` on stderr and empty stdout.

Run `python -m unittest` at the end. All tests must pass.

## Spec problems and risks

1. **The `year_month` example in CLAUDE.md is too permissive for R4.** It checks `date.fromisoformat(f"{text}-01")`, and on Python 3.11+ `fromisoformat` accepts more ISO formats than `YYYY-MM-DD`. Inputs like `202609` might get through, and I couldn't run a check to rule it out. The shape check in step 2 closes this, and it should get a few extra subtest cases.
2. **Two separate filters.** The total comes from `monthly_total` and the category lines from `expenses_in_month`, so the month selection is written twice. The spec requires this and forbids changing `monthly_total`. The acceptance tests are what keep the two in agreement.
3. **The month check in `expenses_in_month` isn't in the spec.** CLAUDE.md §4 says not to return an empty result for bad arguments, so I added the 1–12 check. It is the only addition beyond the spec. Drop it, and its test, if you want the spec followed strictly.
4. **R5 is loosely worded.** It says "print only `total 0.00`", but the real line is padded (`total` then spaces, then `0.00`). The tests should compare against the formatted string, not the literal text in the spec.
5. **The "today" test could rarely fail.** If it runs across midnight at the end of a month, the added expense and the `month` call can land in different months. This is accepted as unlikely.
6. **Ties are already handled.** `total_by_category` uses a stable sort on insertion order, which gives first-appearance order, so the tie rule needs no new code.