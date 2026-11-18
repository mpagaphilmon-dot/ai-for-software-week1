def filter_by_date(expenses, start, end):
    """Return the expenses dated from start to end, inclusive."""
    return [e for e in expenses if start <= e.day <= end]
