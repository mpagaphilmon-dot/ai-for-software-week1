I found no spec or CLAUDE.md violations, a few minor quality issues, and nothing out of scope. This was a review by reading the code only: the sandbox blocked my probe script, so none of the inputs below were actually run.

## 1. Spec / CLAUDE.md violations
None. Requirement by requirement:
- **R1, R2, ties:** `total_by_category` uses a stable sort on a dict that keeps first-appearance order, so equal totals stay in file order, as `summary` does. The total line comes from `monthly_total`, as the spec requires.
- **R3:** with no argument, `default=None` is not passed through `type=`, so `date.today()` supplies the year and month (`cli.py:105-107`).
- **R4:** `2026-13`, `2026-00`, `2026-9`, `2026-09-15`, `abc`, `0000-01` and full-width digits like `２０２６-12` are all rejected by the shape check or `fromisoformat`. Each raises `ArgumentTypeError` with the exact spec message, so the exit code is 2 and nothing goes to stdout.
- **R5:** a missing file gives `[]` from `load_expenses`, and an empty file gives no rows, so the output is only `total 0.00`.
- **R6:** the filter checks both year and month, so the Dec/Jan boundary case is correct.
- **R7:** the command never calls `append_expense`.
- **R8:** `expenses_in_month` raises `ValueError` for a month outside 1–12 (`report.py:37`).
- **Module jobs:** filtering is in `report.py` and the CLI only formats. The README has its one usage line, and the new report function has a docstring that says how it rounds.

## 2. Risks / code-quality issues (all low)
1. **Help text shows `month [month]`, not `[YYYY-MM]`.** The positional has no `metavar`, so `month -h` and the usage line in error messages show `month [month]`, while the spec writes `month [YYYY-MM]`. Also, `args.month` holds a `(year, month)` tuple, which is easy to misread as an int. Fix: add `metavar="YYYY-MM"`; a clearer `dest` is optional.
2. **The month filter is written twice.** `expenses_in_month` and `monthly_total` use the same year-and-month condition. The spec requires both functions and forbids changing `monthly_total`, so this is accepted. It's still worth knowing that the two copies could drift apart later.
3. **The validation condition is hard to read.** `year_month` packs five checks into one line (`cli.py:38`). It's correct, and the `isascii()` guard against non-ASCII digits is a good catch. Splitting it, or adding a comment that names what each check rejects, would make it easier to maintain. Building the `ArgumentTypeError` before the checks is harmless.

## 3. Built but out of scope
None. The diff doesn't touch `add`, `list`, `summary`, `between`, `monthly_total`, `data/` or `docs/`, and adds no new dependencies.