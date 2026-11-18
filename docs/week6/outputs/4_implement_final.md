I've added the `month` command, and all 41 tests pass with `python -m unittest`. Only `expenses/report.py`, `expenses/cli.py` and `README.md` changed; nothing under `tests/` was touched.

- **`expenses/report.py`**: new `expenses_in_month(expenses, year, month)`. It keeps the input order and raises `ValueError("month must be from 1 to 12")` for a month outside 1–12 (R8). `monthly_total` is unchanged.
- **`expenses/cli.py`**:
  - **Validation:** a new `year_month` function rejects anything that isn't exactly `YYYY-MM` with `invalid month: '<text>', expected YYYY-MM` and exit code 2. It checks the shape before calling `date.fromisoformat`, so `202609` and the empty string are rejected too (amendment A).
  - **Subcommand:** `month_cmd` has an optional `month` argument (amendment D).
  - **Output:** the category lines come from `total_by_category(expenses_in_month(...))` and the last line from `monthly_total(...)`.
  - **Default month:** with no argument it uses the current month, reading `date.today()` once so a run at midnight can't mix two dates.
  - **No writes:** the command only reads the CSV file.
- **`README.md`**: added `python -m expenses month 2026-09` to `## Usage`.

Amendments B and C (the full-message check and the October line order) are covered by the existing tests, and both pass. Nothing from the spec's out-of-scope list was built.