import unittest
from datetime import date

from expenses.models import Expense
from expenses.report import monthly_total, total, total_by_category

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

    def test_monthly_total_only_counts_that_month(self):
        self.assertEqual(monthly_total(EXPENSES, 2026, 9), 15.70)
        self.assertEqual(monthly_total(EXPENSES, 2026, 10), 9.75)

    def test_monthly_total_does_not_mix_years(self):
        self.assertEqual(monthly_total(EXPENSES, 2025, 9), 0)


if __name__ == "__main__":
    unittest.main()
