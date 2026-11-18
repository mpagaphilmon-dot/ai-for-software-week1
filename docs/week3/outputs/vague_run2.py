def expenses_between(expenses, start, end):
    """Expenses dated from start to end, inclusive, in chronological order."""
    return sorted((e for e in expenses if start <= e.day <= end), key=lambda e: e.day)
