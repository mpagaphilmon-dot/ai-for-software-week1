import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest import mock

from expenses.models import Expense
from expenses.storage import append_expense, load_expenses, remove_last_expense


class StorageTests(unittest.TestCase):
    def test_missing_file_is_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            self.assertEqual(load_expenses(Path(tmp) / "none.csv"), [])

    def test_round_trip(self):
        expense = Expense(date(2026, 9, 2), "food", 12.5, "lunch")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "nested" / "expenses.csv"
            append_expense(path, expense)
            append_expense(path, expense)
            self.assertEqual(load_expenses(path), [expense, expense])

    def test_append_to_empty_file_writes_header(self):
        expense = Expense(date(2026, 9, 2), "food", 12.5, "lunch")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "empty.csv"
            path.write_bytes(b"")
            append_expense(path, expense)
            self.assertEqual(load_expenses(path), [expense])

    def test_append_to_file_without_trailing_newline(self):
        existing = Expense(date(2026, 9, 2), "food", 12.5, "lunch")
        added = Expense(date(2026, 9, 3), "food", 5.0, "snack")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "handedit.csv"
            path.write_bytes(b"date,category,amount,note\n2026-09-02,food,12.50,lunch")
            append_expense(path, added)
            self.assertEqual(load_expenses(path), [existing, added])

    def test_append_to_normal_file_is_unchanged(self):
        added = Expense(date(2026, 9, 3), "food", 5.0, "snack")
        original = b"date,category,amount,note\r\n2026-09-02,food,12.50,lunch\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            path.write_bytes(original)
            append_expense(path, added)
            self.assertEqual(
                path.read_bytes(), original + b"2026-09-03,food,5.00,snack\r\n"
            )

    def test_remove_last_returns_it_and_keeps_other_bytes(self):
        # LF endings, as in data/sample.csv: the kept rows must not be rewritten.
        kept = b"date,category,amount,note\n2026-09-02,food,12.50,lunch\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            path.write_bytes(kept + b"2026-09-03,Transport,3.20,bus\n")
            removed = remove_last_expense(path)
            self.assertEqual(removed, Expense(date(2026, 9, 3), "transport", 3.2, "bus"))
            self.assertEqual(path.read_bytes(), kept)

    def test_remove_last_without_trailing_newline(self):
        kept = b"date,category,amount,note\r\n2026-09-02,food,12.50,lunch\r\n"
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            path.write_bytes(kept + b"2026-09-03,food,5.00,snack")
            self.assertEqual(remove_last_expense(path).note, "snack")
            self.assertEqual(path.read_bytes(), kept)

    def test_remove_last_with_multiline_note(self):
        first = Expense(date(2026, 9, 2), "food", 12.5, "lunch")
        last = Expense(date(2026, 9, 3), "food", 5.0, "two\nlines")
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            append_expense(path, first)
            append_expense(path, last)
            self.assertEqual(remove_last_expense(path), last)
            self.assertEqual(load_expenses(path), [first])

    def test_remove_last_failed_write_keeps_file(self):
        original = (
            b"date,category,amount,note\r\n"
            b"2026-09-02,food,12.50,lunch\r\n"
            b"2026-09-03,food,5.00,snack\r\n"
        )

        def failing_write_text(self, *args, **kwargs):
            self.write_bytes(b"")  # truncated, as open(..., "w") does
            raise OSError("disk full")

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "expenses.csv"
            path.write_bytes(original)
            with mock.patch.object(Path, "write_text", failing_write_text):
                with self.assertRaises(OSError):
                    remove_last_expense(path)
            self.assertEqual(path.read_bytes(), original)
            self.assertEqual(list(Path(tmp).iterdir()), [path])

    def test_remove_last_with_nothing_to_remove(self):
        with tempfile.TemporaryDirectory() as tmp:
            missing = Path(tmp) / "missing.csv"
            self.assertIsNone(remove_last_expense(missing))
            self.assertFalse(missing.exists())
            for content in [b"", b"date,category,amount,note\r\n"]:
                with self.subTest(content=content):
                    path = Path(tmp) / "expenses.csv"
                    path.write_bytes(content)
                    self.assertIsNone(remove_last_expense(path))
                    self.assertEqual(path.read_bytes(), content)


if __name__ == "__main__":
    unittest.main()
