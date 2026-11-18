I added the `undo` command and its tests. `python -m unittest` passes: 48 tests, OK. Nothing is committed yet.

## PR description

**Add `undo` command to remove the most recently added expense**

### What changed
- **`expenses/storage.py`**: new `remove_last_expense(path)`. It removes the last expense row from the CSV and returns it as an `Expense`. If there's nothing to remove (missing file, empty file, or a file with only the header), it returns `None`, doesn't touch the file and doesn't create one.
  - Every other byte of the file stays exactly as it was. Rows aren't rewritten, so hand-edited LF files like `data/sample.csv` keep their line endings.
  - It uses `csv` to find where the last record starts, so a quoted note that spans several lines is removed as one record, not one line at a time.
  - It reads the expense back with the existing `load_expenses`, so the removed row is parsed the same way as everywhere else.
- **`expenses/cli.py`**: new `undo` subcommand. It calls `remove_last_expense` and prints either `Removed 12.50 from food (2026-09-02)` or `Nothing to undo`. Both cases exit 0, because an empty ledger isn't an error. Printing happens only in `cli.py`; `storage.py` doesn't print.
- **`README.md`**: added `python -m expenses undo` to the Usage block.

### How it was tested
- **`tests/test_storage.py`**, four new tests:
  - removing the last row gives back the right `Expense` and leaves the rest of an LF file byte-for-byte the same;
  - a last row with no trailing newline;
  - a last note that spans several lines;
  - nothing to remove (missing, empty, header-only), checking the file is unchanged or still doesn't exist.
- **`tests/test_cli.py`**, three new tests, using `run()`, a temp directory and `--file`:
  - `undo` prints the exact message and only the last row is gone;
  - undoing until empty, then `Nothing to undo` with the file unchanged;
  - `undo` on a missing or empty file prints `Nothing to undo`, doesn't create the missing file and leaves the empty file empty.
- `python -m unittest`: 48 tests, all pass.