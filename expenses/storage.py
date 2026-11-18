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


def remove_last_expense(path):
    """Remove the last expense row from the CSV file and return it.

    Returns None, leaving the file untouched, when there is no expense to remove.
    Every other byte of the file is kept as it was.
    """
    path = Path(path)
    expenses = load_expenses(path)
    if not expenses:
        return None

    with path.open(newline="", encoding="utf-8") as f:
        lines = f.readlines()

    # A quoted note can span several lines, so let csv find where the last
    # record starts instead of just dropping the last line.
    consumed = []

    def feed():
        for text in lines:
            consumed.append(text)
            yield text

    start = last_start = 0
    for row in csv.reader(feed()):
        if row:
            last_start = start
        start = len(consumed)

    # Write to a sibling file and swap it in, so a failed write can't
    # truncate the ledger; replace() is atomic on the same filesystem.
    tmp = path.with_name(path.name + ".tmp")
    try:
        tmp.write_text("".join(lines[:last_start]), encoding="utf-8", newline="")
        tmp.replace(path)
    finally:
        tmp.unlink(missing_ok=True)
    return expenses[-1]


def append_expense(path, expense):
    """Add one expense to the CSV file, creating it with a header if needed."""
    path = Path(path)
    # An existing but empty file has no header yet, so treat it as new.
    is_new = not path.exists() or path.stat().st_size == 0
    path.parent.mkdir(parents=True, exist_ok=True)

    # A hand-edited file may lack a trailing newline; without one the new
    # row would be glued onto the end of the last line.
    needs_newline = False
    if not is_new and path.stat().st_size > 0:
        with path.open("rb") as f:
            f.seek(-1, 2)
            needs_newline = f.read(1) not in (b"\n", b"\r")

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if needs_newline:
            f.write("\r\n")
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
