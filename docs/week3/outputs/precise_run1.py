def expenses_between(expenses, start, end):
    """Expenses dated from start to end inclusive, in their original order."""
    if start > end:
        raise ValueError("start must not be after end")
    return [e for e in expenses if start <= e.day <= end]
