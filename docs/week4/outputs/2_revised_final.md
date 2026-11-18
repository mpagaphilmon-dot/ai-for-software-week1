I've written the plan to `C:\Users\Administrator\.claude\plans\add-input-validation-to-temporal-quail.md`. Plan mode is on, so nothing has been changed or run yet.

**Code change (only `expenses/cli.py`):**
- I'll add two small check functions and attach them to the `add` arguments, the same way `type=float` is attached now:
  - **`positive_amount`:** converts the amount to a number, then rejects it unless it is finite and greater than 0. That covers 0, negatives, `nan` and `inf`.
  - **`non_empty_category`:** rejects a category that is empty once spaces are stripped. It returns the text unchanged, so the existing lowercasing and trimming in `main` still work.
- A failed check stops argparse while it is still reading the arguments. It prints the message to stderr and exits with code 2, exactly like the current `abc` case. `main` never reaches `append_expense`, so the file is never created or changed.

**Tests (only `tests/test_cli.py`, existing tests untouched):** two new tests built like the existing non-numeric amount test.
- **Amount rule:** tries `"0"`, `"-5"`, `"nan"` and `"inf"`.
- **Category rule:** tries `""` and `"   "`.
- Each input gets its own temporary folder and checks for exit code 2 and that the CSV file doesn't exist.

**To check it:** `python -m unittest discover -s tests -v`. The tests only write to temporary folders that are deleted afterwards.

The instructions said to finish by calling ExitPlanMode, but this session doesn't have that tool. Tell me if the plan is approved and I'll make the changes.