import tempfile
import unittest
from datetime import date
from pathlib import Path

from expenses.models import Expense
from expenses.storage import append_expense, load_expenses


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


if __name__ == "__main__":
    unittest.main()
