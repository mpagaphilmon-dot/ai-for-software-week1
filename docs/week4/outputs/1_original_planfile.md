# Input validation for the expense tracker

## Context
Today almost nothing stops bad data reaching `data/expenses.csv`:
- `add` uses `type=float`, so `nan`, `inf`, `-50`, `0`, `1e308` and `12.345` are all accepted (the last is silently rounded on write, so the in-memory value differs from what is stored).
- Category can be empty (`"  "` → `""`), contain newlines/control chars, be arbitrarily long, or be `total` (collides with the summary's total row).
- Note can contain newlines/control chars and has no length cap.
- Dates can be in the future.
- `load_expenses` crashes with a raw traceback (`KeyError`, `ValueError`) on a bad header or row, with no line number; NaN/negative rows written by hand load fine and corrupt totals.

Goal: one set of rules enforced at every entry point (CLI, CSV load, direct `Expense(...)` construction), clear error messages, no tracebacks for user errors, and nothing ever written when input is invalid.

## Design
Two layers:
1. **Model invariants** (always true for any `Expense`) — enforced in `Expense.__post_init__`, so no code path can create a bad record.
2. **Entry-point policy** (context-dependent) — "no future dates" lives in the CLI `add` path only, so old ledgers and tests aren't tied to the clock.

Bad rows on load **fail loudly** (error names file + line) rather than being skipped, because silently dropping rows would make totals wrong without anyone noticing.

### 1. `expenses/models.py` — validate in `__post_init__`
Add `class InvalidExpense(ValueError)` and constants (`MAX_AMOUNT = 1_000_000`, `MAX_CATEGORY_LEN = 30`, `MAX_NOTE_LEN = 200`, `RESERVED_CATEGORIES = {"total"}`).
- `day`: must be `datetime.date` and **not** `datetime.datetime` (subclass); reject year < 1900.
- `amount`: `int`/`float` but not `bool`; finite; `0 < amount <= MAX_AMOUNT`; at most 2 decimal places (check via `Decimal(str(amount))` exponent). Store as `float`.
- `category`: `str`; normalise `strip().lower()` (via `object.__setattr__`, since the dataclass is frozen — this moves normalisation out of cli.py/storage.py); non-empty; ≤ 30 chars; matches `^[a-z0-9][a-z0-9 _-]*$`; not reserved.
- `note`: `str`; strip surrounding whitespace; ≤ 200 chars; no control characters (`unicodedata.category(c).startswith("C")`), which covers `\n`, `\r`, `\t`, NUL.
Each failure raises `InvalidExpense` with a human message, e.g. `amount must be greater than 0 (got -5)`.

### 2. `expenses/validation.py` (new, small) — string parsers for entry points
- `parse_amount(text) -> float`: parse with `Decimal` (rejects `nan`/`inf`/`""`/`"1,000"` explicitly with a clear message), then apply the same range/cents rules by constructing via the model's checks (reuse a shared `check_amount` helper exported from models.py to avoid duplicating rules).
- `parse_date(text) -> date`: `date.fromisoformat` with a friendly error (`date must be YYYY-MM-DD`).
- `not_in_future(day, today=None)`: raises if `day > today`; `today` injectable for tests.
These raise `argparse.ArgumentTypeError`-compatible `ValueError` so argparse shows `error: argument amount: ...` and exits 2 (matching existing `test_add_rejects_non_numeric_amount`).

### 3. `expenses/cli.py`
- `add.add_argument("amount", type=parse_amount)`, `--date type=parse_date`.
- Drop manual `.strip().lower()` (model does it).
- Wrap command bodies: catch `InvalidExpense` / `LedgerError` → print `error: <msg>` to stderr, return `1`. Apply `not_in_future` before building the `Expense`.
- `list`/`summary` on a corrupt ledger → clean error + exit 1 instead of traceback.

### 4. `expenses/storage.py`
- Add `class LedgerError(ValueError)`.
- `load_expenses`: verify header == `FIELDS` (missing/extra/misordered columns → `LedgerError("<path>: expected header date,category,amount,note")`); skip fully blank lines; for each row, parse `date`/`amount` with the `validation` parsers and build `Expense`, wrapping any `ValueError` as `LedgerError(f"{path}, line {reader.line_num}: {msg}")`; reject rows with too many fields (`None` key in DictReader row).
- `append_expense`: defensively `isinstance(expense, Expense)` check; record is already valid by construction. No write happens before validation (already true since `Expense` is built first).

## Tests to add
- `tests/test_models.py` (new): each invariant — zero/negative/NaN/inf/huge/3-decimal/bool amounts; empty, too long, `"food\n"`, `"a,b"`, `"total"` categories; note with newline/NUL/too long; `datetime` passed as day; normalisation of `" Food "` and note whitespace.
- `tests/test_cli.py`: `add` rejects `nan`, `-5`, `0`, `12.345`, future `--date`, bad date format, empty category, note with newline → non-zero exit, stderr message, **file not created/unchanged**. `list` on corrupt file → exit 1, message includes line number.
- `tests/test_storage.py`: bad header, bad date row, NaN amount row, extra field row → `LedgerError` naming the line; blank trailing lines tolerated; `data/sample.csv` still loads.
Existing tests should pass unchanged (they only use valid data and dates before 2026-11-09).

## Verification
```
python -m unittest discover -s tests -v
python -m expenses --file data/sample.csv summary
python -m expenses --file %TEMP%/x.csv add food nan        # exit 2, clear error
python -m expenses --file %TEMP%/x.csv add "" 5            # exit 1, clear error
python -m expenses --file %TEMP%/x.csv add food 5 --date 2099-01-01   # exit 1
```
Confirm no file is created by any rejected `add`.

## Assumptions (flag if wrong)
- Refunds/negative amounts are **not** allowed; zero is not allowed.
- Future dates are rejected on `add` (today is allowed).
- Limits: amount ≤ 1,000,000, category ≤ 30 chars `[a-z0-9 _-]`, note ≤ 200 chars.
- A corrupt ledger aborts with an error rather than skipping bad rows.
- Amounts stay `float` (switching to `Decimal` throughout is a larger refactor not needed for validation).
