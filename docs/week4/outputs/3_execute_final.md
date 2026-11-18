I've made the changes to `expenses/cli.py` and `tests/test_cli.py`, but I couldn't run the tests. The permission settings need approval for `python -m unittest discover -s tests -v`, and this session can't ask for it. So none of this has been run yet.

**What changed**
- **`expenses/cli.py`:** I added `import math` and two checks that run as the arguments are parsed. The amount check rejects non-numbers, `0`, negative numbers, `nan` and `inf`. The category check rejects a category that's empty after stripping spaces, but passes a valid one through unchanged, so `main` still trims and lowercases it as before. The `add` command now uses both checks. Bad input stops with argparse's usual error and exit code 2 before `append_expense` is called, so the CSV file is never created or changed.
- **`tests/test_cli.py`:** I added two tests and left the existing ones unchanged.
  - `test_add_rejects_non_positive_or_non_finite_amount` tries `"0"`, `"-5"`, `"nan"` and `"inf"`.
  - `test_add_rejects_blank_category` tries `""` and `"   "`.
  
  Each input gets its own temporary folder, and each test checks for exit code 2 and that no file was created.

Nothing else was touched: no other files, no changes to list or summary, and no changes to how CSV files are loaded. I also skipped the optional manual check from the plan.

**To verify**, run this from the repo root:
```
python -m unittest discover -s tests -v
```
I expect 5 passing tests. The existing non-numeric amount test should still pass, since `abc` still exits with code 2, now with the message "invalid amount: 'abc'". One thing to check is that `-5` is read as an amount rather than an option. I believe argparse handles that correctly here, but it hasn't been confirmed by a run.