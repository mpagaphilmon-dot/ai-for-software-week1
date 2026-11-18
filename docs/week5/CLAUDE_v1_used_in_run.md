# Rules for this repository

A tiny command-line expense tracker backed by a CSV file. Python 3.10+, **standard library only**.
Each rule has a short *why* so you can apply it to cases the examples don't cover.

## 1. Source of truth

| Question | Read this | Never use |
| --- | --- | --- |
| What the code does | `expenses/*.py` | `docs/**`, `wk*/`, `check/` |
| How tests are written | `tests/*.py` (`tests/test_cli.py` for CLI tests) | test code quoted in `docs/` |
| How to run it | `README.md` | |

- `docs/`, `wk*/` and `check/` are **coursework archives**: old copies of files (e.g. `docs/week3/report_before.py`), rejected AI drafts (`docs/week3/outputs/*.py`) and diffs. They are out of date on purpose. Do not read them to learn the code, copy from them, import them or edit them.
  *Why:* several of them define functions with the same names as the real ones but with different behaviour; grepping the whole repo will find them first.
- If you need a function, check `expenses/report.py` / `storage.py` **before** writing a new one.
  *Why:* `report.py` already has `total`, `total_by_category`, `average_by_category`, `monthly_total`, `expenses_between`. A second copy of the same logic will drift.

## 2. Structure: one job per module

| Module | Job | Must not |
| --- | --- | --- |
| `models.py` | the frozen `Expense` dataclass | validate, read files |
| `storage.py` | read/append the CSV | print, know about argparse |
| `report.py` | pure calculations on a list of `Expense` | read files, print, parse strings |
| `cli.py` | parse arguments, call storage + report, print | do arithmetic beyond formatting |

*Why:* report functions are tested with plain lists, no files; keeping I/O in `cli.py` keeps them that way.

Keep changes small: touch only the files the task needs. Don't reformat, rename or "tidy" unrelated code, and don't add files unless asked.

## 3. Naming and style

- `snake_case` functions, short nouns for data (`expenses`, `day`, `category`, `amount`), no type-hint retrofits on untouched code.
- A new report function gets a one-line docstring saying what it returns and how it rounds.
- Money is a `float` rounded with `round(x, 2)` in `report.py`, printed with `:.2f` in `cli.py`.
- Categories are compared lower-case and stripped (`" Food "` -> `"food"`), done in `cli.py` and `storage.py`.

## 4. Errors

- **Bad command-line input** is rejected by **argparse**, using a `type=` function that raises `argparse.ArgumentTypeError`. Result: message on stderr, exit code **2**, nothing written.
  *Why:* this is how `positive_amount`, `non_empty_category` and `--date` already behave; one mechanism means one exit code and one message format.
- **Programming errors** inside `report.py` raise `ValueError` with a plain message (see `expenses_between`). Never return an empty result to hide bad arguments.
- No `try/except` that swallows errors, no `sys.exit(1)` / `print(..., file=sys.stderr)` in commands.

## 5. Tests

- `unittest` only (no pytest), run with `python -m unittest` from the repo root. All tests must pass before you finish.
- Report tests: build `Expense` lists in the test (see `EXPENSES` / `SAMPLE` in `tests/test_report.py`), no files.
- CLI tests: use the `run(argv)` helper in `tests/test_cli.py`, a `tempfile.TemporaryDirectory()` and `--file`; never use `data/expenses.csv` or `data/sample.csv` as a writable file.
- For a rejected input, assert **exit code 2 and the error message**, not just the exit code.
  *Why:* argparse also exits 2 for unrelated reasons (e.g. `-5` read as an option), so code-only tests can pass for the wrong reason.

## 6. Preferred / Avoid

**Reuse the report function**

```python
# Preferred (cli.py)
print(f"{'total':<12} {monthly_total(expenses, year, month):>9.2f}")

# Avoid: re-implementing a calculation that report.py already has
s = 0
for e in expenses:
    if e.day.strftime("%Y-%m") == text:
        s += e.amount
```
*Why:* the calculation is already tested once; a copy in `cli.py` is untested and can drift (rounding, year mix-ups).

**Validate input with an argparse type function**

```python
# Preferred
def year_month(text):
    try:
        day = date.fromisoformat(f"{text}-01")
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid month: {text!r}, expected YYYY-MM")
    return day.year, day.month

cmd.add_argument("month", type=year_month)

# Avoid: checking after parsing and choosing your own exit code
if not re.match(r"\d{4}-\d{2}", args.month):
    print("bad month", file=sys.stderr)
    return 1
```
*Why:* same exit code (2) and message style as every other bad argument, and the command body never sees bad data.

**Test a rejection by its message**

```python
# Preferred
err = io.StringIO()
with redirect_stderr(err), redirect_stdout(io.StringIO()):
    with self.assertRaises(SystemExit) as ctx:
        main(["--file", str(path), "month", "2026-13"])
self.assertEqual(ctx.exception.code, 2)
self.assertIn("invalid month", err.getvalue())

# Avoid
with self.assertRaises(SystemExit):
    main(["month", "2026-13"])        # no --file, no message check
```

## 7. Libraries

Standard library only: `argparse`, `csv`, `datetime`, `dataclasses`, `pathlib`, `collections`, `math`. Do not add `click`, `pandas`, `pytest`, `dateutil` or a `requirements.txt`.
*Why:* the README promises "standard library only"; a dependency for one feature breaks that for every user.

## 8. Documentation

When you add a command, add one usage line to the `## Usage` block in `README.md`. Don't touch other docs.
