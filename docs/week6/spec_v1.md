# Spec v1 (draft): `month` command

## User goal
See how much I spent in one calendar month, and where it went (per category).

## Input
`python -m expenses [--file FILE] month YYYY-MM`, e.g. `month 2026-09`.

## Output
- One line per category that has expenses in that month, largest total first, same format as `summary`.
- Then a `total` line with the month's total.

## Requirements
- R1. When the user runs `month YYYY-MM`, the system shall print the per-category totals for expenses dated in that month.
- R2. The system shall then print a `total` line with the sum of that month's expenses.
- R3. If the month is invalid, the system shall show an error.
- R4. If there are no expenses in that month, the system shall print a total of 0.

## Constraints
- Standard library only.
- Reuse `report.py` (`monthly_total`, `total_by_category`).

## Acceptance criteria
- `month 2026-09` on `data/sample.csv` shows rent, food, transport and the total 714.60.
- `month 2026-13` fails.

## Out of scope
- Budgets, charts.
