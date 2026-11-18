I added CLI tests in `tests/test_cli.py`. They use `unittest`, like the other test files. The full suite passes with `python -m unittest`: 15 tests, 8 of them new.

The tests call `main()` directly with a temporary `--file`, so nothing touches `data/expenses.csv`. They capture stdout to check the exact output.

What they cover:
- **`add`:**
  - The expense is saved with its note and date.
  - The confirmation message is printed (`Added 12.50 to food`).
  - The category is cleaned up: `"  Food "` is saved as `food`.
  - The date defaults to today when `--date` is left out.
- **`list`:** each saved expense prints on its own line in the right column layout, and a file that doesn't exist yet prints nothing.
- **`summary`:** category totals print largest first with a `total` line at the end, and a file that doesn't exist yet prints only `total 0.00`.
- **Bad arguments:** no command, an unknown command, an amount that isn't a number, and a date not in `YYYY-MM-DD` form each exit with code 2 and create no file.

The "defaults to today" test compares against the real `date.today()`. That means it could fail if the run happens to cross midnight.
