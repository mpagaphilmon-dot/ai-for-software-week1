import csv
from datetime import date
from pathlib import Path

from expenses.models import Expense

FIELDS = ["date", "category", "amount", "note"]


def load_expenses(path):
    """Read every expense from the CSV file at `path`.

    A missing file is treated as an empty ledger.
    """
    path = Path(path)
    if not path.exists():
        return []

    expenses = []
    with path.open(newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            expenses.append(
                Expense(
                    day=date.fromisoformat(row["date"]),
                    category=row["category"].strip().lower(),
                    amount=float(row["amount"]),
                    note=row.get("note") or "",
                )
            )
    return expenses


def append_expense(path, expense):
    """Add one expense to the CSV file, creating it with a header if needed."""
    path = Path(path)
    is_new = not path.exists()
    path.parent.mkdir(parents=True, exist_ok=True)

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if is_new:
            writer.writeheader()
        writer.writerow(
            {
                "date": expense.day.isoformat(),
                "category": expense.category,
                "amount": f"{expense.amount:.2f}",
                "note": expense.note,
            }
        )
