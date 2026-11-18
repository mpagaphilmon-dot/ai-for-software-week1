# Spec v2: `month` command

## User goal
"What did I spend this month, and where did it go?" Show one calendar month's spending, split by category, with the month total. With no argument it shows the current month.

## Input
```
python -m expenses [--file FILE] month [YYYY-MM]
```
- `YYYY-MM`: four-digit year, two-digit month 01–12 (e.g. `2026-09`). Optional; defaults to the month of today's date.

## Output (stdout)
- One line per category that has at least one expense dated in that month, formatted `f"{category:<12} {amount:>9.2f}"`, largest total first. Ties keep the order of first appearance in the file (the same order `summary` uses).
- Last line: `f"{'total':<12} {t:>9.2f}"`.
- No heading and no per-expense lines.

## Requirements (EARS)
- **R1** When the user runs `month YYYY-MM`, the system shall print one category line for each category with expenses dated from the 1st to the last day of that month inclusive, ordered by total, largest first, and exit 0.
- **R2** When the user runs `month YYYY-MM`, the system shall print as its last line the month total, rounded to 2 decimals.
- **R3** When the user runs `month` with no argument, the system shall behave as if given the current year and month.
- **R4** If the argument is not exactly a valid `YYYY-MM` month, then the system shall exit with code 2, print `invalid month: '<text>', expected YYYY-MM` on stderr, and print nothing on stdout.
- **R5** If no expenses are dated in that month (including a missing or empty file), then the system shall print only `total 0.00` (formatted as above) and exit 0.
- **R6** The system shall not count expenses from the same month of a different year, or from the neighbouring days of the previous or next month.
- **R7** The `month` command shall not write to the CSV file.
- **R8** *(added after plan review)* If `expenses_in_month` is called with a month outside 1–12, then it shall raise `ValueError` rather than return an empty list.

## Constraints
- Standard library only; follow `CLAUDE.md` (module jobs, argparse `type=` validation, `unittest`).
- **Selecting a month's expenses is a calculation, so it belongs in `report.py`:** add `expenses_in_month(expenses, year, month)` (pure, keeps input order) with its own report tests. `cli.py` must not compute month boundaries or filter by itself.
- Category lines come from `total_by_category(<month's expenses>)`; the total line comes from `monthly_total(expenses, year, month)`.
- Validation is a `year_month` argparse type function returning `(year, month)`.
- Add one usage line to `README.md`.

## Acceptance criteria (with `data/sample.csv` data rebuilt in a temp file)
| Command | Expected stdout | Exit |
| --- | --- | --- |
| `month 2026-09` | `rent 650.00` / `food 61.40` / `transport 3.20` / `total 714.60` (in this order) | 0 |
| `month 2026-10` | `food 9.75` / `transport 3.20` / `total 12.95` | 0 |
| `month 2025-09` | `total 0.00` only | 0 |
| `month` (an expense added for today) | that expense's category and amount, and the total | 0 |
| `month 2026-13`, `2026-00`, `2026-9`, `2026-09-15`, `abc` | nothing; stderr has `invalid month` | 2 |
| Dec/Jan: expenses on 2026-11-30, 2026-12-01, 2026-12-31, 2027-01-01; `month 2026-12` | only the two December expenses | 0 |

## Out of scope (do not build)
- Percentages, averages, budgets, charts, per-expense listing, filtering to one category.
- Multiple months, year summaries, comparing months, `--sort`, JSON/CSV output, currency symbols.
- Changing `add`, `list`, `summary`, `between` or refactoring their shared print code; changing `monthly_total`.
- Handling malformed CSV rows; editing `data/`, `docs/`; new dependencies.
- Making category lines add up exactly to the total (each is rounded separately; a 1-cent difference is accepted).
