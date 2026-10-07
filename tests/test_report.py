import unittest
from datetime import date

from expenses.models import Expense
from expenses.report import total, total_by_category

EXPENSES = [
    Expense(date(2026, 9, 2), "food", 12.50),
    Expense(date(2026, 9, 3), "transport", 3.20),
    Expense(date(2026, 10, 4), "food", 9.75),
]


class ReportTests(unittest.TestCase):
    def test_total(self):
        self.assertEqual(total(EXPENSES), 25.45)

    def test_total_of_nothing_is_zero(self):
        self.assertEqual(total([]), 0)

    def test_total_by_category_is_sorted_largest_first(self):
        self.assertEqual(list(total_by_category(EXPENSES).items()), [("food", 22.25), ("transport", 3.20)])


if __name__ == "__main__":
    unittest.main()
