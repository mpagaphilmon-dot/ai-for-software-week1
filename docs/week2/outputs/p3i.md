I added `tests/test_cli.py` with the three tests you asked for, and `python -m unittest` passes: all 10 tests, including the 7 existing ones. I didn't change any other file. Every test passes `--file` with a path inside a `tempfile.TemporaryDirectory()`. The `data/` folder held only `sample.csv` before and after the run, so `data/expenses.csv` was never created.

**`tests/test_cli.py`**
```python
import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path

from expenses.cli import main
from expenses.storage import load_expenses


def run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


class CliTests(unittest.TestCase):
    def test_add_then_summary(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")

            code, out = run(["--file", path, "add", "Food", "12.5", "--note", "lunch"])
            self.assertEqual(code, 0)
            self.assertIn("Added 12.50 to food", out)

            code, out = run(["--file", path, "summary"])
            self.assertEqual(code, 0)
            lines = out.splitlines()
            food = [line for line in lines if line.startswith("food")]
            totals = [line for line in lines if line.startswith("total")]
            self.assertEqual(len(food), 1)
            self.assertIn("12.50", food[0])
            self.assertEqual(len(totals), 1)
            self.assertIn("12.50", totals[0])

    def test_add_normalises_category(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            code, _ = run(["--file", str(path), "add", " Food ", "3"])
            self.assertEqual(code, 0)
            [expense] = load_expenses(path)
            self.assertEqual(expense.category, "food")

    def test_add_rejects_non_numeric_amount(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    main(["--file", str(path), "add", "Food", "abc"])
            self.assertEqual(ctx.exception.code, 2)
            self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
```

**Test output**
```
test_add_normalises_category (tests.test_cli.CliTests) ... ok
test_add_rejects_non_numeric_amount (tests.test_cli.CliTests) ... ok
test_add_then_summary (tests.test_cli.CliTests) ... ok
test_monthly_total_does_not_mix_years (tests.test_report.ReportTests) ... ok
test_monthly_total_only_counts_that_month (tests.test_report.ReportTests) ... ok
test_total (tests.test_report.ReportTests) ... ok
test_total_by_category_is_sorted_largest_first (tests.test_report.ReportTests) ... ok
test_total_of_nothing_is_zero (tests.test_report.ReportTests) ... ok
test_missing_file_is_empty (tests.test_storage.StorageTests) ... ok
test_round_trip (tests.test_storage.StorageTests) ... ok

----------------------------------------------------------------------
Ran 10 tests in 0.154s

OK
```

Two checks go slightly beyond what you specified:
- **Exactly one line each:** the `add`/`summary` test requires exactly one `food` line and one `total` line, so a duplicated row would also make it fail.
- **No file written:** the bad-amount test also checks that no CSV file gets created. Its error message goes into a buffer so it doesn't clutter the test output.
