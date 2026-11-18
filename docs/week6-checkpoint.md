# Week 6 checkpoint: from a fuzzy request to spec, tests and reviewed code

Philmon · 13 November 2026

**Source code and evidence:** <https://github.com/mpagaphilmon-dot/ai-for-software-week1>. Every `docs/week6/...` path below is in that repository: <https://github.com/mpagaphilmon-dot/ai-for-software-week1/tree/main/docs/week6>.

This submission covers both Week 6 briefs: the **checkpoint submission** (fuzzy request → spec → tests → implementation, reviewed separately) and **capstone milestone 1** (a one-page spec with EARS requirements and an out-of-scope section, an agent plan reviewed before implementation, and tests critiqued for real behaviour).

## 0. Setup

**The capstone feature:** a `month` command for the same small command-line expense tracker (Python, standard library only) I've used in Weeks 1–5. It's deliberately small, and the existing code nearly supports it already: `report.py` has `monthly_total`, but no command uses it.

**How the agent was run.** Claude Code 2.1.322 (Claude Opus 5.5), `claude -p`, in an **isolated copy** of the repository with its own git history. Every step was a **fresh session**: the only context each one got was its prompt file, plus the repo and its `CLAUDE.md` rules. That stopped the tests from being shaped by an implementation the agent had already written, and kept the code review independent of the tests. Read-only steps could only use Read/Glob/Grep. Editing steps could also edit files and run `python -m unittest`. Exact commands: `docs/week6/prompts/command.txt`.

| Step | Who | Input | Output | Agent cost |
| --- | --- | --- | --- | --- |
| 1 | me | the fuzzy request | spec v1 (draft) | |
| 2 | agent, read-only | request + spec v1 | spec critique | 2 turns, $0.27 |
| 3 | me | critique | **spec v2**, decisions made | |
| 4 | agent, read-only | spec v2 | implementation plan | 10 turns, $0.35 |
| 5 | me | plan | plan review: approved + 4 amendments | |
| 6 | agent, edits tests only | spec + plan + amendments | tests, failing (red) | 13 turns, $0.50 |
| 7 | me | test diff | test review, +1 test | |
| 8 | agent, edits code only, tests frozen | spec + plan + amendments | implementation (green) | 13 turns, $0.32 |
| 9 | agent, read-only, no access to tests | spec + code diff | code review | 7 turns, $0.33 |
| 10 | me | code diff + review | code review, 1-line fix | |
| 11 | me | final code | red/green runs, manual runs, mutation checks | |

The isolated copy's history shows who wrote what (`docs/week6/copy_git_log.txt`):
```
561dc6f human: human metavar fix
e368d1b agent: agent implementation
99368bf human: human tie test
7c5bb64 agent: agent tests
a8c2837 baseline: baseline
```

Everything is in `docs/week6/`:

| Path | Contents |
| --- | --- |
| `fuzzy_request.txt` | the original request |
| `spec_v1.md`, `spec.md` | my draft and the final spec (v2) |
| `plan_review.md`, `test_review.md` | my reviews of the plan and of the tests |
| `prompts/1_spec_review.txt` … `5_code_review.txt`, `prompts/command.txt` | each prompt exactly as sent, and the commands |
| `outputs/N_*_final.md`, `*_toolcalls.txt`, `*.jsonl` | each run's final answer, its tool calls, and the raw log |
| `outputs/3_tests.diff`, `outputs/4_implement.diff` | the agent's test diff and implementation diff |
| `human_test_change.diff`, `human_code_change.diff` | my changes |
| `final.diff` | the full accepted change (code + tests + README) |
| `verification.txt`, `mutate.py` | my own red/green, manual and mutation runs |

---

## 1. The original fuzzy request

> "Can it tell me what I spent this month? Maybe split by category too, I never know where the money goes."

What makes it fuzzy: "this month" (today's month, or any month?), "maybe" by category (required or not?), "where the money goes" (totals, percentages, a list?). It also says nothing about the output format, bad input, empty months or years.

## 2. The rewritten spec

### 2.1 From draft to spec: what the AI critique changed

I wrote a quick draft first (`spec_v1.md`, 30 lines) and gave it to a read-only agent session with the request, asking it to find ambiguity, missing cases, decisions left to the implementer, and wrong acceptance criteria. The critique (`outputs/1_spec_review_final.md`) found real problems:

| Problem in v1 | Raised by the critique | What v2 does |
| --- | --- | --- |
| "show an error" and "`month 2026-13` fails" aren't testable; argparse exits 2 for unrelated reasons too | yes | R4: exit 2, the exact message, empty stdout |
| R1 had no order, no line format, no date range | yes | exact `f"{category:<12} {amount:>9.2f}"` format, largest first, 1st to last day inclusive |
| "Reuse `monthly_total`, `total_by_category`" **can't work as written**: nothing returns a month's expenses, and filtering in `cli.py` breaks the module rules | yes | new pure `report.expenses_in_month` (see decision below) |
| The user said **"this month"**, but v1 required an argument | yes | R3: no argument = current month |
| No year mix-up, Dec/Jan boundary, empty or missing file, or ties | yes | R5, R6, tie rule, Dec/Jan acceptance row |
| Acceptance criterion checked presence but not order or amounts | yes | exact expected lines in a table |
| Out of scope was just "budgets, charts" | yes | 5 lines of explicit exclusions |

The critique recommended one decision that I **overruled**: it suggested building the month's date range in `cli.py` (1st of the month to the day before the 1st of the next month) and calling `expenses_between`. That is date arithmetic in `cli.py`, which `CLAUDE.md` gives no place in ("parse, call, print"), and it would be untested. I chose a new pure report function with its own tests instead.

### 2.2 Spec v2 (final, one page; full text in `docs/week6/spec.md`)

**User goal.** "What did I spend this month, and where did it go?" Show one calendar month's spending split by category, plus the month total. With no argument it shows the current month.

**Input.** `python -m expenses [--file FILE] month [YYYY-MM]`. The month is optional and defaults to today's month.

**Output.** One line per category with expenses in that month, `f"{category:<12} {amount:>9.2f}"`, largest total first; ties keep first-appearance order (as `summary` does). The last line is `f"{'total':<12} {t:>9.2f}"`. There is no heading and there are no per-expense lines.

**Requirements (EARS).**

| ID | Requirement |
| --- | --- |
| R1 | **When** the user runs `month YYYY-MM`, the system **shall** print one category line for each category with expenses dated from the 1st to the last day of that month inclusive, largest first, and exit 0. |
| R2 | **When** the user runs `month YYYY-MM`, the system **shall** print the month total, rounded to 2 decimals, as its last line. |
| R3 | **When** the user runs `month` with no argument, the system **shall** behave as if given the current year and month. |
| R4 | **If** the argument isn't exactly a valid `YYYY-MM`, **then** the system **shall** exit 2, print `invalid month: '<text>', expected YYYY-MM` on stderr, and print nothing on stdout. |
| R5 | **If** no expenses are dated in that month (including a missing or empty file), **then** the system **shall** print only the `total 0.00` line and exit 0. |
| R6 | The system **shall not** count expenses from the same month in another year, or from neighbouring days in the previous or next month. |
| R7 | The `month` command **shall not** write to the CSV file. |
| R8 | *(added after plan review)* **If** `expenses_in_month` gets a month outside 1–12, **then** it **shall** raise `ValueError` rather than return `[]`. |

**Constraints.** Standard library only, and follow `CLAUDE.md`. Selecting a month's expenses happens in `report.expenses_in_month(expenses, year, month)`, and `cli.py` doesn't filter or compute dates. Category lines come from `total_by_category`, and the total from `monthly_total`. Validation is an argparse `year_month` type function. Add one README usage line.

**Acceptance criteria** (the sample data rebuilt in a temporary file):

| Command | Expected stdout | Exit |
| --- | --- | --- |
| `month 2026-09` | `rent 650.00`, `food 61.40`, `transport 3.20`, `total 714.60`, in this order | 0 |
| `month 2026-10` | `food 9.75`, `transport 3.20`, `total 12.95` | 0 |
| `month 2025-09` | `total 0.00` only | 0 |
| `month` (expense added today) | that expense and the total | 0 |
| `month 2026-13` / `2026-00` / `2026-9` / `2026-09-15` / `abc` | nothing; stderr has `invalid month` | 2 |
| expenses on 11-30, 12-01, 12-31 and 2027-01-01; `month 2026-12` | only the two December expenses | 0 |

**Out of scope (non-goals).**
- Percentages, averages, budgets, charts, per-expense listing, filtering to one category.
- Several months, year summaries, month comparisons, `--sort`, JSON or CSV output, currency symbols.
- Changing `add`, `list`, `summary`, `between` or `monthly_total`, or refactoring their print code.
- Handling malformed CSV rows, editing `data/` or `docs/`, adding dependencies.
- Making the category lines add up exactly to the total. Each is rounded separately, so a 1-cent gap is accepted.

## 3. The plan, and my review before any code

A fresh read-only session turned spec v2 into a plan (`outputs/2_plan_final.md`). It named each file, function, signature and position, listed 12 tests with what each one asserts, and flagged **six risks of its own**. Two of them were especially good:

- It added a `ValueError` for months outside 1–12, which wasn't in the spec, and **said so itself** ("the only addition beyond the spec; drop it if you want the spec followed strictly") instead of slipping it in.
- It warned that the `year_month` pattern from `CLAUDE.md` relies on `date.fromisoformat`, which accepts more formats on Python 3.11+, and proposed an explicit `YYYY-MM` shape check.

My review (`plan_review.md`): **approved with 4 amendments.**

| | Amendment | Why |
| --- | --- | --- |
| A | Add `202609` and `""` to the rejected inputs | so the shape check is actually exercised |
| B | At least one test must check the **full** message, `invalid month: '2026-13', expected YYYY-MM` | a substring like `invalid month` could also match an unrelated error |
| C | The October test must check line **order** | the plan only said "food 9.75, transport 3.20" |
| D | Name the subparser `month_cmd`, not `month` | `month` is also the argument name and a local variable in `main` |

I accepted R8 and wrote it into the spec. I checked the 3.11+ claim as far as I could: on 3.10 every odd input (`202609`, `2026-W01`, `2026-9`, full-width digits) is already rejected. There's no working 3.11+ interpreter on this machine, so I accepted the shape check as **insurance, not a proven fix**. Section 7 comes back to this.

## 4. The tests: created, reviewed, changed

### 4.1 Created first, by a separate session

A fresh session got the spec, the plan and my amendments, and was told to write **tests only** and not touch `expenses/`. It added 6 report tests and 7 CLI tests (`outputs/3_tests.diff`) and ran them. Everything new failed, for the expected reason (the feature doesn't exist yet). I reproduced that red run myself (`verification.txt` a):
```
ImportError: cannot import name 'expenses_in_month' from 'expenses.report'
Ran 24 tests ... FAILED (failures=7, errors=10)
```
One detail shows the value of amendment B. Before the feature existed, every invalid-month input **already exited with code 2**, because argparse rejected `month` as an unknown subcommand. A test that checked only the exit code would have passed against no implementation at all. The full-message check is what made those tests fail.

### 4.2 My review of the tests (`test_review.md`)

I reviewed the tests on their own terms before any implementation existed: does each one pin down a requirement, and would it fail for the right reason?

| Test | Req. | Real behaviour? | Why it holds up, or doesn't |
| --- | --- | --- | --- |
| `..._shows_categories_largest_first_then_total` | R1 R2 | yes | compares the **whole output**: catches wrong order, wrong amount, extra lines or a heading |
| `test_month_october` | R1 R2 | yes | list equality checks order |
| `..._with_no_matches_prints_zero_total` | R5 R6 | yes | `2025-09` against 2026 data also covers the year mix-up |
| `..._on_missing_or_empty_file_...` | R5 R7 | yes | also checks the missing file isn't created; the agent added the empty-file case unprompted |
| `..._excludes_neighbouring_months` | R6 | yes | amounts 1, 2, 4, 8 mean any leaked day changes the total |
| `..._defaults_to_current_month` | R3 | yes | **a decoy expense in another month**; without it, "sum everything" would pass |
| `..._does_not_write_file` | R7 | yes | byte-for-byte comparison |
| `..._rejects_invalid_month` (7 subtests) | R4 | yes | exit 2, full message, empty stdout and no file, for every input |
| 6 × `expenses_in_month_*` (report) | R1 R6 R8 | yes | plain lists; `keeps_input_order` would catch a sorted result |

**What I changed:** I added **one test** (`human_test_change.diff`). The spec has a tie rule ("ties keep first-appearance order") and nothing tested it:
```python
def test_month_ties_keep_first_appearance_order(self):
    # transport is added before food with the same total; alphabetical order would put food first
    add_rows(path, [("2026-09-01", "transport", "5"), ("2026-09-02", "food", "5")])
    ...
    self.assertEqual(out.splitlines(), [line("transport", 5), line("food", 5), line("total", 10)])
```
**Weaknesses I recorded but didn't fix** (see section 7): the shape check isn't proven by any test on 3.10, and rounding can't be observed through the CLI.

## 5. The implementation and its separate review

### 5.1 Implementation diff

A fresh session got the spec, the plan and the amendments. The tests were **frozen** ("do not modify any file under `tests/`"). It changed only the three files the plan named, and all 41 tests passed on its first run (`outputs/4_implement.diff`). The accepted code:

```diff
# expenses/report.py
+def expenses_in_month(expenses, year, month):
+    """Expenses dated in the given year and month, in their original order (no rounding)."""
+    if not 1 <= month <= 12:
+        raise ValueError("month must be from 1 to 12")
+    return [e for e in expenses if e.day.year == year and e.day.month == month]

# expenses/cli.py
+def year_month(text):
+    error = argparse.ArgumentTypeError(f"invalid month: {text!r}, expected YYYY-MM")
+    # fromisoformat alone accepts other ISO shapes on 3.11+, so check YYYY-MM first.
+    if not (len(text) == 7 and text.isascii() and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit()):
+        raise error
+    try:
+        day = date.fromisoformat(f"{text}-01")
+    except ValueError:
+        raise error
+    return day.year, day.month
 ...
+    month_cmd = commands.add_parser("month", help="show one month's totals per category, then the month total")
+    month_cmd.add_argument("month", nargs="?", type=year_month, default=None, metavar="YYYY-MM", help="defaults to the current month")
 ...
+    if args.command == "month":
+        if args.month is None:
+            today = date.today()
+            year, month = today.year, today.month
+        else:
+            year, month = args.month
+        for category, amount in total_by_category(expenses_in_month(expenses, year, month)).items():
+            print(f"{category:<12} {amount:>9.2f}")
+        print(f"{'total':<12} {monthly_total(expenses, year, month):>9.2f}")
+        return 0

# README.md
+python -m expenses month 2026-09
```

### 5.2 Code review, kept separate from the test review

A fourth fresh session reviewed **only the code**, against the spec and `CLAUDE.md`. It was told not to look at `tests/`, so a green test run couldn't stand in for review. It went through R1–R8 and found **no violations and nothing out of scope**, plus three low-severity issues (`outputs/5_code_review_final.md`). My own review agreed:

| Issue | Source | Decision |
| --- | --- | --- |
| Help and errors said `month [month]`, but the spec says `[YYYY-MM]` | agent reviewer | **fixed**: `metavar="YYYY-MM"`, and the redundant help text shortened (`human_code_change.diff`, 1 line) |
| The month filter now exists twice (`expenses_in_month` and `monthly_total`) and could drift | plan risk, reviewer, me | accepted: the spec forbids changing `monthly_total`; the acceptance tests keep the two in agreement |
| `year_month` packs five checks into one line | agent reviewer | accepted: correct and commented; a style call |
| The code comment says "fromisoformat accepts other shapes on 3.11+" as fact | me | accepted, noted: matches the Python 3.11 changelog, but I couldn't test it here |
| Module jobs: filtering in `report.py`, `cli.py` only formats; docstring says how it rounds; `date.today()` read once | me | correct |

After my fix, help reads `usage: expenses month [-h] [YYYY-MM]` and errors read `expenses month: error: argument YYYY-MM: invalid month: '2026-13', expected YYYY-MM`.

## 6. Test results and manual verification (my own runs, `verification.txt`)

- **Red, before implementation:** `FAILED (failures=7, errors=10)`, all because the feature was missing (section 4.1).
- **Green, in the real repo after accepting the change:** `Ran 41 tests ... OK` (26 before this week, plus 15 new).
- **Manual runs** on `data/sample.csv`:

| Command | Output | Exit | Spec |
| --- | --- | --- | --- |
| `month 2026-09` | rent 650.00 / food 61.40 / transport 3.20 / total 714.60 | 0 | R1 R2 ✓ |
| `month 2026-10` | food 9.75 / transport 3.20 / total 12.95 | 0 | ✓ |
| `month 2025-09` | total 0.00 | 0 | R5 R6 ✓ |
| `month` (today is 2026-11-13; sample has no November rows) | total 0.00 | 0 | R3 ✓ |
| `month 2026-13`, `2026-9`, `202609`, `2026-09-15` | `expenses month: error: argument YYYY-MM: invalid month: '…', expected YYYY-MM` | 2 | R4 ✓ |
| `--file nope.csv month 2026-09` | total 0.00, and `nope.csv` not created | 0 | R5 R7 ✓ |
| `git status data/` after all runs | no change | | R7 ✓ |
| `summary`, `between 2026-09-03 2026-09-15` | same output as Week 5 | 0 | unchanged ✓ |

## 7. What the tests prove, and what they don't

To check this rather than assume it, I ran **mutation checks** (`mutate.py`). Each one breaks the finished code in one deliberate way, runs the whole suite, and restores the file.

| Mutant (deliberate bug) | Result | Caught by |
| --- | --- | --- |
| M1 total line sums every month | **caught** | 5 CLI tests |
| M2 month filter ignores the year | **caught** | `expenses_in_month_does_not_mix_years`, `no_matches` |
| M4 default month is always January | **caught** | `defaults_to_current_month` (only that test) |
| M5 categories sorted alphabetically | **caught** | 3 CLI tests |
| M6 R8 range check removed | **caught** | `expenses_in_month_rejects_bad_month` |
| M7 category lines use every month | **caught** | 5 CLI tests |
| M9 ties broken by name, largest first kept | **caught** | **only my added tie test** |
| M3 `YYYY-MM` shape check removed | **survived** | none |
| M8 `isascii()` guard removed | **survived** | none |

**The tests prove** (on Python 3.10, with this data):
- the month selection is right at the year and month boundaries, in report code and end to end;
- the order (largest first, ties by first appearance) and the exact output format;
- the default month is today's month, not a constant or every month;
- bad months are rejected through argparse with the right message, exit code and no output;
- the command doesn't create or change the file;
- `expenses_in_month` refuses an impossible month instead of hiding it.

**They do not prove:**
1. **That the shape check is needed or works on Python 3.11+.** M3 and M8 survived: on 3.10, `date.fromisoformat` already rejects every input the tests try, so the guard is dead weight as far as the tests can tell. The defence is real code that no test covers. Proving it would take a 3.11+ test run.
2. **Rounding.** `:.2f` hides float noise at the CLI (0.1 + 0.2 prints `0.30` with or without `round`). Rounding is covered only by the existing `monthly_total` report tests.
3. **That the category lines add up to the total.** They're rounded separately, which the spec puts out of scope; there's no test.
4. **Behaviour at midnight on the last day of a month.** The "today" test can flake in that one-second window, and the code reads `date.today()` once to keep its own output consistent.
5. **Malformed CSV rows, large files, or non-UTF-8 data.** All out of scope.
6. **That the spec is what the user wanted.** The tests check the code against the spec. Only the user can say whether "split by category, largest first, no percentages" answers "where does my money go?"

## 8. Spec quality and code quality, judged separately

| | Spec | Code |
| --- | --- | --- |
| Judged by | Is each requirement testable, complete and bounded? Does it answer the request? | Does it meet the spec and `CLAUDE.md`, and is it simple? |
| Evidence | AI critique of v1 (7 problems fixed), plan built without questions, every R has a test (section 4.2) | separate code review (no violations), 41 tests green, 7/9 mutants caught |
| Weakest point | R4's "exactly YYYY-MM" asks for something that can't be tested on the only interpreter available | the uncovered shape guard; the duplicated month filter |
| Verdict | good, though v1 would have produced an implementation that **passes its own test and still fails the user** ("fails" was its whole error criterion) | good: small, in scope, 1-line human fix |

## 9. What I learned

- **The spec was where the real work was.** Writing v1 felt finished. The critique found that one of its constraints was impossible as written and that it ignored the user's own words ("this month"). After v2, the plan, the tests and the code each needed almost no changes.
- **Separate sessions are what make "review separately" real.** The test writer had never seen an implementation, and the code reviewer never saw the tests. Each artifact had to stand on its own.
- **Red first catches tests that pass for the wrong reason.** Every invalid-input test exited 2 before the feature existed. Only the message check made them fail, and so made them meaningful.
- **Green tests aren't proof.** Mutation checks turned "41 tests pass" into a concrete list of what's covered and two named gaps. One test I added by hand turned out to be the only defence against one bug (M9).
- **An agent that flags its own additions is easier to supervise.** The plan marked R8 as "beyond the spec", so it became a decision, not a surprise.

## 10. AI-use declaration

- **Agent under test:** Claude Code 2.1.322 (Claude Opus 5.5), run non-interactively (`claude -p`) in an isolated copy of the repository for five steps: spec critique, plan, tests, implementation and code review. The prompts, logs and diffs are included unchanged.
- **Assistant:** I also used Claude Code interactively as my assistant to draft spec v1 and v2, write the prompt files, run the agent steps, write the mutation script, carry out the reviews recorded in `plan_review.md` and `test_review.md`, and draft this write-up.
- **Human decisions in this submission:** choosing the feature; overruling the critique on where month filtering belongs; accepting R8 and the shape check; the four plan amendments; the added tie test; the metavar fix; accepting the duplicated filter and the untested guard as known gaps. The accepted code is the agent's implementation plus a 1-line fix, and the accepted tests are the agent's tests plus one added test.
