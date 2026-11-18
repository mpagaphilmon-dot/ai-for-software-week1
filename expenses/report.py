from collections import defaultdict


def total(expenses):
    """Sum of all expense amounts, rounded to cents."""
    return round(sum(e.amount for e in expenses), 2)


def total_by_category(expenses):
    """Map each category to its total, sorted from largest to smallest."""
    totals = defaultdict(float)
    for e in expenses:
        totals[e.category] += e.amount
    ranked = sorted(totals.items(), key=lambda item: item[1], reverse=True)
    return {category: round(amount, 2) for category, amount in ranked}


def average_by_category(expenses):
    """Map each category to its average expense, sorted from largest to smallest."""
    totals = defaultdict(float)
    counts = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount
        counts[e.category] += 1
    averages = {category: totals[category] / counts[category] for category in totals}
    ranked = sorted(averages.items(), key=lambda item: item[1], reverse=True)
    return {category: round(amount, 2) for category, amount in ranked}


def monthly_total(expenses, year, month):
    """Sum of the expenses dated in the given year and month, rounded to cents."""
    return round(sum(e.amount for e in expenses if e.day.year == year and e.day.month == month), 2)


def expenses_in_month(expenses, year, month):
    """Expenses dated in the given year and month, in their original order (no rounding)."""
    if not 1 <= month <= 12:
        raise ValueError("month must be from 1 to 12")
    return [e for e in expenses if e.day.year == year and e.day.month == month]


# expenses_between(expenses, start, end) -> list of Expense
# Data shape: `expenses` is a list of Expense records (expenses/models.py) whose
#   `day` is a datetime.date; `start` and `end` are datetime.date objects, not strings.
# Behavior: keep every expense with start <= e.day <= end. Both bounds are
#   INCLUSIVE, so an expense dated exactly on `start` or `end` is kept. Return a
#   new list in the same order as the input (do not sort); never modify the input.
#   An empty input list returns [].
# Failure mode: if start > end, raise ValueError("start must not be after end")
#   instead of silently returning [], which would hide a swapped-argument bug.
def expenses_between(expenses, start, end):
    """Expenses dated from start to end inclusive, in their original order."""
    if start > end:
        raise ValueError("start must not be after end")
    return [e for e in expenses if start <= e.day <= end]
