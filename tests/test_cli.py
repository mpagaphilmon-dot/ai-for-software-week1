import io
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout
from datetime import date
from pathlib import Path

from expenses.cli import main
from expenses.storage import load_expenses

# The rows of data/sample.csv, rebuilt with `add --date` in a temp file.
SAMPLE_ROWS = [
    ("2026-09-02", "food", "12.50"),
    ("2026-09-03", "transport", "3.20"),
    ("2026-09-10", "food", "48.90"),
    ("2026-09-15", "rent", "650.00"),
    ("2026-10-01", "transport", "3.20"),
    ("2026-10-04", "food", "9.75"),
]


def run(argv):
    out = io.StringIO()
    with redirect_stdout(out):
        code = main(argv)
    return code, out.getvalue()


def add_rows(path, rows):
    for day, category, amount in rows:
        run(["--file", path, "add", category, amount, "--date", day])


def line(label, amount):
    return f"{label:<12} {amount:>9.2f}"


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

    def test_add_rejects_non_positive_or_non_finite_amount(self):
        for amount in ["0", "-5", "nan", "inf"]:
            with self.subTest(amount=amount), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "expenses.csv"
                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        main(["--file", str(path), "add", "Food", amount])
                self.assertEqual(ctx.exception.code, 2)
                self.assertFalse(path.exists())

    def test_add_rejects_blank_category(self):
        for category in ["", "   "]:
            with self.subTest(category=category), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "expenses.csv"
                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        main(["--file", str(path), "add", category, "5"])
                self.assertEqual(ctx.exception.code, 2)
                self.assertFalse(path.exists())

    def test_between_lists_range_inclusive_then_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            for day, category, amount in [
                ("2026-09-02", "food", "1"),
                ("2026-09-03", "food", "10.25"),
                ("2026-09-10", "transport", "4.5"),
                ("2026-09-15", "rent", "100"),
                ("2026-09-16", "food", "1000"),
            ]:
                run(["--file", path, "add", category, amount, "--date", day])

            code, out = run(["--file", path, "between", "2026-09-03", "2026-09-15"])
            self.assertEqual(code, 0)
            lines = out.splitlines()
            self.assertEqual(len(lines), 4)
            self.assertTrue(lines[0].startswith("2026-09-03"))
            self.assertTrue(lines[1].startswith("2026-09-10"))
            self.assertTrue(lines[2].startswith("2026-09-15"))
            self.assertTrue(lines[3].startswith("total"))
            self.assertIn("114.75", lines[3])
            self.assertNotIn("2026-09-02", out)
            self.assertNotIn("2026-09-16", out)

    def test_between_with_no_matches_prints_zero_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            run(["--file", path, "add", "food", "5", "--date", "2026-08-01"])
            code, out = run(["--file", path, "between", "2026-09-01", "2026-09-30"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), [f"{'total':<12} {0:>9.2f}"])

    def test_between_rejects_invalid_date(self):
        for args in [["2026-13-01", "2026-09-15"], ["2026-09-03", "tomorrow"]]:
            with self.subTest(args=args), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "expenses.csv"
                err = io.StringIO()
                with redirect_stderr(err), redirect_stdout(io.StringIO()):
                    with self.assertRaises(SystemExit) as ctx:
                        main(["--file", str(path), "between", *args])
                self.assertEqual(ctx.exception.code, 2)
                self.assertIn("invalid date", err.getvalue())

    def test_between_rejects_start_after_end(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            err = io.StringIO()
            with redirect_stderr(err), redirect_stdout(io.StringIO()):
                with self.assertRaises(SystemExit) as ctx:
                    main(["--file", str(path), "between", "2026-09-15", "2026-09-03"])
            self.assertEqual(ctx.exception.code, 2)
            self.assertIn("expenses between: error: start date 2026-09-15 must not be after", err.getvalue())

    def test_month_shows_categories_largest_first_then_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            add_rows(path, SAMPLE_ROWS)
            code, out = run(["--file", path, "month", "2026-09"])
            self.assertEqual(code, 0)
            self.assertEqual(
                out.splitlines(),
                [line("rent", 650), line("food", 61.40), line("transport", 3.20), line("total", 714.60)],
            )

    def test_month_october(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            add_rows(path, SAMPLE_ROWS)
            code, out = run(["--file", path, "month", "2026-10"])
            self.assertEqual(code, 0)
            # Exact list equality also checks the order: food before transport.
            self.assertEqual(
                out.splitlines(),
                [line("food", 9.75), line("transport", 3.20), line("total", 12.95)],
            )

    def test_month_with_no_matches_prints_zero_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            add_rows(path, SAMPLE_ROWS)
            code, out = run(["--file", path, "month", "2025-09"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), [line("total", 0)])

    def test_month_on_missing_or_empty_file_prints_zero_total(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.csv"
            empty = Path(tmp) / "empty.csv"
            empty.write_text("", encoding="utf-8")
            for path in [missing, empty]:
                with self.subTest(path=path.name):
                    code, out = run(["--file", str(path), "month", "2026-09"])
                    self.assertEqual(code, 0)
                    self.assertEqual(out.splitlines(), [line("total", 0)])
            self.assertFalse(missing.exists())

    def test_month_excludes_neighbouring_months(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            add_rows(path, [
                ("2026-11-30", "food", "1"),
                ("2026-12-01", "food", "2"),
                ("2026-12-31", "transport", "4"),
                ("2027-01-01", "food", "8"),
            ])
            code, out = run(["--file", path, "month", "2026-12"])
            self.assertEqual(code, 0)
            self.assertEqual(
                out.splitlines(),
                [line("transport", 4), line("food", 2), line("total", 6)],
            )

    def test_month_ties_keep_first_appearance_order(self):
        # Added in human review: the spec's tie rule had no test. Alphabetical
        # order would put food first, so this catches a tie-break by name.
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            add_rows(path, [("2026-09-01", "transport", "5"), ("2026-09-02", "food", "5")])
            code, out = run(["--file", path, "month", "2026-09"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), [line("transport", 5), line("food", 5), line("total", 10)])

    def test_month_defaults_to_current_month(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = str(Path(tmp) / "expenses.csv")
            run(["--file", path, "add", "food", "7"])
            today = date.today()
            other = "2025-01-01" if (today.year, today.month) != (2025, 1) else "2025-02-01"
            run(["--file", path, "add", "rent", "500", "--date", other])
            code, out = run(["--file", path, "month"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), [line("food", 7), line("total", 7)])

    def test_month_does_not_write_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            add_rows(str(path), SAMPLE_ROWS)
            before = path.read_bytes()
            code, _ = run(["--file", str(path), "month", "2026-09"])
            self.assertEqual(code, 0)
            self.assertEqual(path.read_bytes(), before)

    def test_undo_removes_last_added_expense(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            add_rows(str(path), SAMPLE_ROWS[:2])
            run(["--file", str(path), "add", "Food", "12.5", "--date", "2026-09-04"])
            code, out = run(["--file", str(path), "undo"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), ["Removed 12.50 from food (2026-09-04)"])
            self.assertEqual(
                [(str(e.day), e.category, f"{e.amount:.2f}") for e in load_expenses(path)],
                SAMPLE_ROWS[:2],
            )

    def test_undo_until_empty_then_nothing_to_undo(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            add_rows(str(path), SAMPLE_ROWS[:1])
            code, out = run(["--file", str(path), "undo"])
            self.assertEqual(out.splitlines(), ["Removed 12.50 from food (2026-09-02)"])
            before = path.read_bytes()
            code, out = run(["--file", str(path), "undo"])
            self.assertEqual(code, 0)
            self.assertEqual(out.splitlines(), ["Nothing to undo"])
            self.assertEqual(path.read_bytes(), before)

    def test_undo_on_missing_or_empty_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.csv"
            empty = Path(tmp) / "empty.csv"
            empty.write_text("", encoding="utf-8")
            for path in [missing, empty]:
                with self.subTest(path=path.name):
                    code, out = run(["--file", str(path), "undo"])
                    self.assertEqual(code, 0)
                    self.assertEqual(out.splitlines(), ["Nothing to undo"])
            self.assertFalse(missing.exists())
            self.assertEqual(empty.read_bytes(), b"")

    def test_month_rejects_invalid_month(self):
        for text in ["2026-13", "2026-00", "2026-9", "2026-09-15", "abc", "202609", ""]:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as tmp:
                path = Path(tmp) / "expenses.csv"
                out = io.StringIO()
                err = io.StringIO()
                with redirect_stderr(err), redirect_stdout(out):
                    with self.assertRaises(SystemExit) as ctx:
                        main(["--file", str(path), "month", text])
                self.assertEqual(ctx.exception.code, 2)
                self.assertIn(f"invalid month: {text!r}, expected YYYY-MM", err.getvalue())
                self.assertEqual(out.getvalue(), "")
                self.assertFalse(path.exists())


if __name__ == "__main__":
    unittest.main()
