Everything below is checked against `expenses/cli.py`, `expenses/report.py`, `expenses/storage.py`, `tests/` and `data/sample.csv`. I didn't edit any files.

1. **Ambiguous or untestable requirements, rewritten in EARS style**
   - **Input (no requirement number) and the user goal.** The user asked about *this* month, but the spec only accepts an explicit `YYYY-MM`, so the most likely use case isn't covered. See 3a.
   - **R1** doesn't give an order, a line format, or a rule for which days count.
     *When the user runs `month YYYY-MM`, the system shall print one line per category that has at least one expense dated from the 1st to the last day of that month, inclusive. Each line is formatted `f"{category:<12} {amount:>9.2f}"`, sorted by total from largest to smallest, and the command exits 0.*
   - **R2** doesn't say where the line goes or how it is rounded.
     *When the user runs `month YYYY-MM`, the system shall print as its last line `f"{'total':<12} {t:>9.2f}"`, where `t` is the sum of that month's expenses rounded to 2 decimals.*
   - **R3** doesn't define "invalid" or "error".
     *If the month argument is not a valid `YYYY-MM` with a month from 01 to 12, the system shall reject it through argparse: exit code 2, stderr contains `invalid month`, nothing on stdout.*
   - **R4** doesn't say whether category lines appear.
     *If no expenses are dated in the given month (including a missing or empty file), the system shall print exactly one line, `f"{'total':<12} {0:>9.2f}"`, and exit 0.* This matches `test_between_with_no_matches_prints_zero_total`.

2. **Missing edge and error cases**
   - **Malformed months:** `2026-00`, `2026-13`, `2026-9`, `26-09`, a full date like `2026-09-15`, an empty string, `abc`, and no argument at all.
     - Python 3.11+ `date.fromisoformat` accepts more formats than 3.10 does, so pin the exact accepted form with tests rather than relying on it.
     - With no argument, argparse's own message appears, not `invalid month`.
   - **Boundaries:** the 1st and last day of the month are included. 30 and 31 day months, and Feb 29 in a leap year, all work.
   - **Neighbouring months:** expenses dated the last day of the previous month or the 1st of the next are excluded.
   - **Year mix-up:** `2025-09` must not count `2026-09` expenses. Also cover December/January.
   - **Ties:** two categories with equal totals. The order should be stated (first seen in the file, since `sorted` is stable).
   - **Category case:** mixed case in the CSV (`Food`, ` food `) merges into one line. `storage.py` already does this; one test should lock it in.
   - **Cents:** the total must equal the sum of the category lines. Test with amounts such as 0.10 + 0.20.

3. **Decisions the user should make, with a recommendation for each**
   - **a. What happens with no argument?** Recommend making `month` optional and defaulting to today's month. That is what the user actually asked for.
   - **b. Is there a heading line, e.g. `2026-09`?** Recommend no, to keep the output identical to `summary`.
   - **c. Is the per-expense list shown, as in `between`?** Recommend no. The user asked for totals by category.
   - **d. Show percentages per category?** The user said "I never know where the money goes", which hints at shares. Recommend no for v1 and listing it under out of scope.
   - **e. How are the expenses filtered by month?** The spec's constraint ("reuse `monthly_total`, `total_by_category`") doesn't work as written:
     - `report.py` has no function that returns a month's expenses, and `total_by_category` needs that filtered list.
     - CLAUDE.md forbids doing that filtering in `cli.py`.
     - Recommend: `cli.py` builds the 1st of the month and the 1st of the next month, then calls `expenses_between(expenses, first, next_first - timedelta(days=1))`.
       - The category lines come from `total_by_category`. The total line comes from `monthly_total`, or from `total(selected)`; the spec should name one.
       - The alternative is a new `expenses_in_month` function in `report.py`, with its own test. The user should choose; I recommend the first option because it adds no code to `report.py`.
       - Don't use `calendar`: it isn't on the allowed library list in CLAUDE.md.

4. **Add to "Out of scope"**
   - Ranges of several months, a year summary, or comparing months.
   - Averages, percentages, per-expense listing, filtering to one category.
   - Output options: `--sort`, JSON or CSV output, currency symbols.
   - Changing `summary`, `between` or `add`, or refactoring their shared print code.
   - Handling malformed CSV rows.
   - New dependencies, `requirements.txt`, or edits to `data/*.csv` or `docs/`.
   - README changes other than one usage line.

5. **Acceptance criteria**
   - **The 714.60 total is correct:** 12.50 + 3.20 + 48.90 + 650.00 = 714.60. The October rows (3.20 and 9.75) are rightly excluded.
   - **The first criterion is too weak to catch bugs.** It doesn't check order or per-category amounts, so a list sorted A–Z or a wrong food total would still pass. The exact expected output is:
     ```
     rent            650.00
     food             61.40
     transport         3.20
     total           714.60
     ```
     The CLI test should rebuild this data in a temporary directory with `--file`, following the `tests/test_cli.py` convention, rather than relying on `data/sample.csv`.
   - **"`month 2026-13` fails" is wrong as a criterion.** It must assert exit code 2, `invalid month` on stderr and an empty stdout (CLAUDE.md §5). Otherwise a test could pass because of an unrelated argparse error.
   - **Missing criteria:**
     - `month 2026-10` on the sample gives `food 9.75`, `transport 3.20`, `total 12.95`.
     - `month 2025-09` prints only `total 0.00`.
     - Category values in the spec are written to two decimals (`61.40`, not `61.4`) because the output uses `:.2f`.