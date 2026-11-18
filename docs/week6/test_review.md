# My review of the agent's tests (outputs/3_tests.diff), done before any implementation existed

Reviewed as an artifact on its own: do the tests pin down the **spec**, and would they fail for the right reason?

| Test | Requirement | Asserts real behaviour? | Note |
| --- | --- | --- | --- |
| `test_month_shows_categories_largest_first_then_total` | R1, R2 | yes | Whole-output equality: catches wrong order, wrong amount, extra lines, a heading. |
| `test_month_october` | R1, R2 | yes | Order checked through list equality (amendment C). |
| `test_month_with_no_matches_prints_zero_total` | R5, R6 (year) | yes | `2025-09` against 2026 data also covers the year mix-up. |
| `test_month_on_missing_or_empty_file_prints_zero_total` | R5, R7 | yes | Also checks the missing file is not created. Agent added the empty-file case unprompted. Good. |
| `test_month_excludes_neighbouring_months` | R6 | yes | If 2027-01-01 leaked in, food would be 10, not 2. Distinct amounts (1, 2, 4, 8) make every leak visible in the total. |
| `test_month_defaults_to_current_month` | R3 | yes | The **decoy** expense in another month is what makes this real: without it, "sum everything" passes. Small midnight-at-month-end flake risk accepted. |
| `test_month_does_not_write_file` | R7 | yes | Byte-for-byte comparison. |
| `test_month_rejects_invalid_month` (7 subtests) | R4 | yes | Full message + empty stdout + no file, for every input. Already proved its worth: before the feature existed these exited 2 for the *wrong* reason (unknown subcommand), and the message check caught it. |
| report `expenses_in_month_*` (6) | R1, R6, R8 | yes | Pure lists, no files. `keeps_input_order` would catch a sorted result. |

**What I changed:** one test added (`human_test_change.diff`): `test_month_ties_keep_first_appearance_order`. The spec states a tie rule, but nothing tested it. I chose `transport` before `food` so an alphabetical tie-break would fail.

**Weaknesses I accept and record (not fixed):**
1. **R4 shape guard is not proven by any test on Python 3.10.** Every rejected input is already rejected by `date.fromisoformat` on 3.10, so deleting the guard would leave all tests green here. Confirmed by mutation M3 (see `verification.txt`).
2. **R2 rounding is not observable at the CLI.** `:.2f` hides float noise (0.1 + 0.2 prints `0.30` with or without `round`). Rounding is covered only by the existing `monthly_total` report tests.
3. **The CLI tests build data with `add`**, so a broken `add` would make `month` tests fail for an unrelated reason. That's acceptable, because the failure would still be loud.
4. **Category-line vs total consistency** (1-cent rounding gap) is out of scope, so it isn't tested.
