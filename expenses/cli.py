import argparse
from datetime import date

from expenses.models import Expense
from expenses.report import total, total_by_category
from expenses.storage import append_expense, load_expenses

DEFAULT_FILE = "data/expenses.csv"


def build_parser():
    parser = argparse.ArgumentParser(prog="expenses", description="Track expenses in a CSV file.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="CSV file to read and write")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="record a new expense")
    add.add_argument("category")
    add.add_argument("amount", type=float)
    add.add_argument("--note", default="")
    add.add_argument("--date", type=date.fromisoformat, default=None, help="YYYY-MM-DD, defaults to today")

    commands.add_parser("list", help="show every expense")
    commands.add_parser("summary", help="show totals per category")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.command == "add":
        expense = Expense(
            day=args.date or date.today(),
            category=args.category.strip().lower(),
            amount=args.amount,
            note=args.note,
        )
        append_expense(args.file, expense)
        print(f"Added {expense.amount:.2f} to {expense.category}")
        return 0

    expenses = load_expenses(args.file)

    if args.command == "list":
        for e in expenses:
            print(f"{e.day}  {e.category:<12} {e.amount:>9.2f}  {e.note}")
        return 0

    for category, amount in total_by_category(expenses).items():
        print(f"{category:<12} {amount:>9.2f}")
    print(f"{'total':<12} {total(expenses):>9.2f}")
    return 0
