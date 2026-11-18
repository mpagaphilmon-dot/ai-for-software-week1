`expenses/storage.py` is the persistence layer for the expense tracker. It stores expenses as rows in a CSV file and converts between those rows and `Expense` objects from `expenses.models`.

## The file format

```python
FIELDS = ["date", "category", "amount", "note"]
```

The CSV has these four columns in this order, for example:

```
date,category,amount,note
2026-10-01,food,12.50,lunch
```

Note that the CSV column is called `date` but the `Expense` attribute is called `day`. The module maps one to the other in both directions.

## `load_expenses(path)` (lines 10–30)

Reads the whole file and returns a list of `Expense` objects.

- **A missing file returns `[]`** (line 16). A ledger that doesn't exist yet counts as empty, not as an error.
- It uses `csv.DictReader`, so each row is a dict keyed by the header names.
- Each field is converted on the way in:
  - `date`: the ISO string `"2026-10-01"` becomes a `datetime.date`.
  - `category`: spaces are trimmed and it's lowercased, so `" Food "` and `"food"` count as the same category.
  - `amount`: parsed as a `float`.
  - `note`: `row.get("note") or ""` gives an empty string when the column is blank or missing.
- The file is opened with `newline=""` and `encoding="utf-8"`. This is the setup the `csv` module recommends, and it handles line endings correctly on Windows.

## `append_expense(path, expense)` (lines 33–50)

Adds a single expense to the end of the file.

- It checks whether the file already exists **before** opening it (line 36). Opening in `"a"` (append) mode would create the file, so checking afterwards would always say it exists.
- `mkdir(parents=True, exist_ok=True)` creates any missing parent folders, such as a `data/` directory.
- The header is written only when the file is new.
- Each field is converted on the way out:
  - `day` becomes an ISO string.
  - `amount` is formatted to two decimal places (`f"{amount:.2f}"`).
- Appending one row at a time means the existing rows are never rewritten.

## Things worth knowing

1. **An empty file loses its first expense.** If the file exists but has 0 bytes, `is_new` is `False`, so no header gets written. On the next load, `DictReader` reads the first data row as the header, and that expense disappears. Checking `not path.exists() or path.stat().st_size == 0` would fix this.
2. **Categories are only cleaned up when loading.** `append_expense` writes the category exactly as given, and the cleanup happens when the file is read back. The result is consistent, but the file itself can contain mixed casing.
3. **Money is stored as `float`.** The two-decimal formatting keeps the file tidy, but adding many floats can create small rounding errors. `decimal.Decimal` would make the totals exact.
4. **No error handling for bad rows.** A row with a malformed date or amount raises a `ValueError` and stops the whole load, instead of skipping that row.
