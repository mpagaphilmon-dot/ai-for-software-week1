def filter_by_date(expenses, start, end):
    """Return the expenses dated between start and end, inclusive."""
    return [e for e in expenses if start <= e.day <= end]
