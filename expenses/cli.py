import argparse
import math
from datetime import date

from expenses.models import Expense
from expenses.report import expenses_between, expenses_in_month, monthly_total, total, total_by_category
from expenses.storage import append_expense, load_expenses, remove_last_expense

DEFAULT_FILE = "data/expenses.csv"


def positive_amount(text):
    try:
        value = float(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid amount: {text!r}")
    if not math.isfinite(value) or value <= 0:
        raise argparse.ArgumentTypeError(f"amount must be a finite number greater than 0, got {text!r}")
    return value


def non_empty_category(text):
    if not text.strip():
        raise argparse.ArgumentTypeError("category must not be empty")
    return text


def iso_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date: {text!r}, expected YYYY-MM-DD")


def year_month(text):
    error = argparse.ArgumentTypeError(f"invalid month: {text!r}, expected YYYY-MM")
    # fromisoformat alone accepts other ISO shapes on 3.11+, so check YYYY-MM first.
    if not (len(text) == 7 and text.isascii() and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit()):
        raise error
    try:
        day = date.fromisoformat(f"{text}-01")
    except ValueError:
        raise error
    return day.year, day.month


def build_parser():
    parser = argparse.ArgumentParser(prog="expenses", description="Track expenses in a CSV file.")
    parser.add_argument("--file", default=DEFAULT_FILE, help="CSV file to read and write")
    commands = parser.add_subparsers(dest="command", required=True)

    add = commands.add_parser("add", help="record a new expense")
    add.add_argument("category", type=non_empty_category)
    add.add_argument("amount", type=positive_amount)
    add.add_argument("--note", default="")
    add.add_argument("--date", type=date.fromisoformat, default=None, help="YYYY-MM-DD, defaults to today")

    commands.add_parser("list", help="show every expense")
    commands.add_parser("summary", help="show totals per category")
    commands.add_parser("undo", help="remove the most recently added expense")

    between = commands.add_parser("between", help="show expenses from START to END inclusive, then their total")
    between.add_argument("start", type=iso_date, help="YYYY-MM-DD")
    between.add_argument("end", type=iso_date, help="YYYY-MM-DD")
    # start > end needs both values, so it is checked after parsing; report it
    # through this subparser so the usage line matches its other errors.
    between.set_defaults(error=between.error)

    month_cmd = commands.add_parser("month", help="show one month's totals per category, then the month total")
    month_cmd.add_argument("month", nargs="?", type=year_month, default=None, metavar="YYYY-MM", help="defaults to the current month")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)

    if args.command == "between" and args.start > args.end:
        args.error(f"start date {args.start} must not be after end date {args.end}")

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

    if args.command == "undo":
        expense = remove_last_expense(args.file)
        if expense is None:
            print("Nothing to undo")
        else:
            print(f"Removed {expense.amount:.2f} from {expense.category} ({expense.day})")
        return 0

    expenses = load_expenses(args.file)

    if args.command == "list":
        for e in expenses:
            print(f"{e.day}  {e.category:<12} {e.amount:>9.2f}  {e.note}")
        return 0

    if args.command == "between":
        selected = expenses_between(expenses, args.start, args.end)
        for e in selected:
            print(f"{e.day}  {e.category:<12} {e.amount:>9.2f}  {e.note}")
        print(f"{'total':<12} {total(selected):>9.2f}")
        return 0

    if args.command == "month":
        if args.month is None:
            today = date.today()
            year, month = today.year, today.month
        else:
            year, month = args.month
        for category, amount in total_by_category(expenses_in_month(expenses, year, month)).items():
            print(f"{category:<12} {amount:>9.2f}")
        print(f"{'total':<12} {monthly_total(expenses, year, month):>9.2f}")
        return 0

    for category, amount in total_by_category(expenses).items():
        print(f"{category:<12} {amount:>9.2f}")
    print(f"{'total':<12} {total(expenses):>9.2f}")
    return 0
