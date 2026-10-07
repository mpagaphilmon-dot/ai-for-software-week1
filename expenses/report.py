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


def monthly_total(expenses, year, month):
    """Sum of the expenses dated in the given year and month, rounded to cents."""
    return round(sum(e.amount for e in expenses if e.day.year == year and e.day.month == month), 2)
