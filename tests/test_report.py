import unittest
from datetime import date

from expenses.models import Expense
from expenses.report import (
    average_by_category,
    expenses_between,
    expenses_in_month,
    monthly_total,
    total,
    total_by_category,
)

EXPENSES = [
    Expense(date(2026, 9, 2), "food", 12.50),
    Expense(date(2026, 9, 3), "transport", 3.20),
    Expense(date(2026, 10, 4), "food", 9.75),
]

SAMPLE = [
    Expense(date(2026, 9, 2), "food", 12.50, "lunch"),
    Expense(date(2026, 9, 3), "transport", 3.20, "bus"),
    Expense(date(2026, 9, 10), "food", 48.90, "groceries"),
    Expense(date(2026, 9, 15), "rent", 650.00, ""),
    Expense(date(2026, 10, 1), "transport", 3.20, "bus"),
    Expense(date(2026, 10, 4), "food", 9.75, "lunch"),
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

    def test_average_by_category_is_rounded_and_sorted_largest_first(self):
        self.assertEqual(
            list(average_by_category(SAMPLE).items()),
            [("rent", 650.0), ("food", 23.72), ("transport", 3.2)],
        )

    def test_average_by_category_of_nothing_is_empty(self):
        self.assertEqual(average_by_category([]), {})

    def test_expenses_between_includes_both_bounds(self):
        self.assertEqual(
            expenses_between(SAMPLE, date(2026, 9, 3), date(2026, 9, 15)),
            SAMPLE[1:4],
        )

    def test_expenses_between_keeps_input_order(self):
        shuffled = [SAMPLE[5], SAMPLE[0], SAMPLE[4]]
        self.assertEqual(
            expenses_between(shuffled, date(2026, 9, 1), date(2026, 10, 31)),
            shuffled,
        )

    def test_expenses_between_does_not_modify_input(self):
        expenses = list(SAMPLE)
        expenses_between(expenses, date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(expenses, SAMPLE)

    def test_expenses_between_of_nothing_is_empty(self):
        self.assertEqual(expenses_between([], date(2026, 9, 1), date(2026, 9, 30)), [])

    def test_expenses_between_rejects_start_after_end(self):
        with self.assertRaisesRegex(ValueError, "start must not be after end"):
            expenses_between(SAMPLE, date(2026, 10, 1), date(2026, 9, 1))

    def test_expenses_in_month_only_that_month(self):
        self.assertEqual(expenses_in_month(SAMPLE, 2026, 9), SAMPLE[0:4])
        self.assertEqual(expenses_in_month(SAMPLE, 2026, 10), SAMPLE[4:6])

    def test_expenses_in_month_does_not_mix_years(self):
        self.assertEqual(expenses_in_month(SAMPLE, 2025, 9), [])

    def test_expenses_in_month_excludes_neighbouring_days(self):
        expenses = [
            Expense(date(2026, 11, 30), "food", 1.00),
            Expense(date(2026, 12, 1), "food", 2.00),
            Expense(date(2026, 12, 31), "transport", 4.00),
            Expense(date(2027, 1, 1), "food", 8.00),
        ]
        self.assertEqual(expenses_in_month(expenses, 2026, 12), expenses[1:3])

    def test_expenses_in_month_keeps_input_order(self):
        shuffled = [SAMPLE[3], SAMPLE[0], SAMPLE[5], SAMPLE[2]]
        self.assertEqual(expenses_in_month(shuffled, 2026, 9), [SAMPLE[3], SAMPLE[0], SAMPLE[2]])

    def test_expenses_in_month_of_nothing_is_empty(self):
        self.assertEqual(expenses_in_month([], 2026, 9), [])

    def test_expenses_in_month_rejects_bad_month(self):
        for month in [0, 13]:
            with self.subTest(month=month):
                with self.assertRaisesRegex(ValueError, "month must be"):
                    expenses_in_month(SAMPLE, 2026, month)


if __name__ == "__main__":
    unittest.main()
