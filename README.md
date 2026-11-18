# expenses

A tiny command-line expense tracker backed by a CSV file. Standard library only, Python 3.10+.

## Usage

```
python -m expenses add food 12.50 --note lunch
python -m expenses list
python -m expenses summary
python -m expenses between 2026-09-03 2026-09-15
python -m expenses month 2026-09
python -m expenses undo
python -m expenses --file data/sample.csv summary
```

Expenses are stored in `data/expenses.csv` unless `--file` is given.

## Tests

```
python -m unittest
```

## Layout

- `expenses/models.py` — the `Expense` record
- `expenses/storage.py` — reading and appending the CSV file
- `expenses/report.py` — totals
- `expenses/cli.py` — argument parsing and commands
