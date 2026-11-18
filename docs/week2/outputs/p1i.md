```diff
--- a/expenses/report.py
+++ b/expenses/report.py
@@ -15,6 +15,18 @@ def total_by_category(expenses):
     return {category: round(amount, 2) for category, amount in ranked}
 
 
+def average_by_category(expenses):
+    """Map each category to its average expense, sorted from largest to smallest."""
+    totals = defaultdict(float)
+    counts = defaultdict(int)
+    for e in expenses:
+        totals[e.category] += e.amount
+        counts[e.category] += 1
+    averages = {category: totals[category] / counts[category] for category in totals}
+    ranked = sorted(averages.items(), key=lambda item: item[1], reverse=True)
+    return {category: round(amount, 2) for category, amount in ranked}
+
+
 def monthly_total(expenses, year, month):
     """Sum of the expenses dated in the given year and month, rounded to cents."""
     return round(sum(e.amount for e in expenses if e.day.year == year and e.day.month == month), 2)
--- a/tests/test_report.py
+++ b/tests/test_report.py
@@ -2,7 +2,7 @@ import unittest
 from datetime import date
 
 from expenses.models import Expense
-from expenses.report import monthly_total, total, total_by_category
+from expenses.report import average_by_category, monthly_total, total, total_by_category
 
 EXPENSES = [
     Expense(date(2026, 9, 2), "food", 12.50),
@@ -10,6 +10,15 @@ EXPENSES = [
     Expense(date(2026, 10, 4), "food", 9.75),
 ]
 
+SAMPLE = [
+    Expense(date(2026, 9, 2), "food", 12.50, "lunch"),
+    Expense(date(2026, 9, 3), "transport", 3.20, "bus"),
+    Expense(date(2026, 9, 10), "food", 48.90, "groceries"),
+    Expense(date(2026, 9, 15), "rent", 650.00, ""),
+    Expense(date(2026, 10, 1), "transport", 3.20, "bus"),
+    Expense(date(2026, 10, 4), "food", 9.75, "lunch"),
+]
+
 
 class ReportTests(unittest.TestCase):
     def test_total(self):
@@ -28,6 +37,15 @@ class ReportTests(unittest.TestCase):
     def test_monthly_total_does_not_mix_years(self):
         self.assertEqual(monthly_total(EXPENSES, 2025, 9), 0)
 
+    def test_average_by_category_is_rounded_and_sorted_largest_first(self):
+        self.assertEqual(
+            list(average_by_category(SAMPLE).items()),
+            [("rent", 650.0), ("food", 23.72), ("transport", 3.2)],
+        )
+
+    def test_average_by_category_of_nothing_is_empty(self):
+        self.assertEqual(average_by_category([]), {})
+
 
 if __name__ == "__main__":
     unittest.main()
```

```
$ python -m unittest
.........
----------------------------------------------------------------------
Ran 9 tests in 0.043s

OK
```
