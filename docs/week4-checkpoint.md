# Week 4 checkpoint: agent mode with scope control

Philmon · 9 November 2026

## 0. Setup

Same repository as Weeks 1–3: a small Python command-line expense tracker (standard library only).

**The bounded outcome.** Add input validation, so that bad data typed into `expenses add` never reaches the CSV ledger. Today `add` accepts `0`, `-5`, `nan`, `inf` and a blank category, and writes all of them to the file.

**How the agent was run.** I used Claude Code 2.1.319 as the agent, with `claude -p` in a **separate copy of the repository** that had its own git baseline commit, so nothing could touch my real working tree until I accepted the result. There were three separate sessions:

1. **Plan only** (`--permission-mode plan`) with my original instruction. The agent can read but not change anything.
2. **Plan only** again, with a revised, narrower instruction.
3. **Execute** the approved plan, with permissions that let it **read anything but edit only the two approved files**, and no shell.

Every run was logged as a stream of JSON events, so I could see exactly which tools it called and which files it read. Everything is in `docs/week4/`:

| Path | Contents |
| --- | --- |
| `prompts/1_original.txt`, `prompts/2_revised.txt` | my two instructions |
| `prompts/3_execute.txt`, `prompts/3_execute_command.txt` | the execute prompt (revised instruction + approved plan) and the exact command with its permission rules |
| `outputs/1_original_planfile.md`, `outputs/2_revised_planfile.md` | the agent's full plans |
| `outputs/*_toolcalls.txt` | every tool call per run (files read, edits, denied commands) |
| `outputs/*.jsonl` | the raw session logs |
| `final.diff` | the final change |
| `verification.txt` | my independent verification output |

---

## 1. My original agent instruction

```
Add input validation to this expense tracker so that bad data can't get into the ledger. Make it robust.
```

The outcome is clear, but nothing limits **where** the agent may work or **how far** "robust" goes. I wrote it this way to see what the agent would do with that freedom.

## 2. The agent's plan before execution

**Files read** (`outputs/1_original_toolcalls.txt`): every file in the repository in one command (`git ls-files` + `cat` of all of them), then it wrote its plan.

**Plan, condensed** (full text in `outputs/1_original_planfile.md`):

| # | Proposed change | File |
| --- | --- | --- |
| 1 | Validate every `Expense` on creation: amount > 0, ≤ 1,000,000, max 2 decimals; category ≤ 30 chars, only `[a-z0-9 _-]`, not `total`; note ≤ 200 chars, no control characters; date year ≥ 1900. Move category normalisation into the model. | `expenses/models.py` |
| 2 | New module with `parse_amount`, `parse_date`, `not_in_future` | `expenses/validation.py` **(new)** |
| 3 | Use the new parsers, reject future dates, catch errors and exit 1 | `expenses/cli.py` |
| 4 | Check header and every row when loading; **refuse to load** a file with any bad row (`LedgerError`) | `expenses/storage.py` |
| 5 | Tests | `tests/test_models.py` **(new)**, `tests/test_cli.py`, `tests/test_storage.py` |

It also listed its own assumptions: refunds and zero rejected, future dates rejected, a corrupt ledger aborts, and the limits above.

**My review of this plan.** It is careful work, but it is **not a bounded change**:

- **7 files, 2 of them new**, for what I meant as a small feature.
- **It changes how existing data loads.** Validating inside `Expense` plus strict loading means an existing ledger with a `Total` category, a 3-decimal amount or an old refund row would stop loading altogether. That's a behaviour change for every user, hidden inside a "validation" task.
- **It invents policy I never asked for:** a 1,000,000 cap, 30/200-character limits, no future dates, no refunds. Each is a product decision, not a technical one.
- **It changes exit codes:** some errors would exit 1 instead of argparse's 2, which is a change to the CLI contract.

## 3. Scope review

| File | Decision | Reason |
| --- | --- | --- |
| `expenses/cli.py` | **Approved** | This is where user input comes in; validating here stops bad data before it's written. |
| `tests/test_cli.py` | **Approved** | Tests for the new rules belong with the CLI tests. |
| `expenses/models.py` | Rejected | Changing the model affects every code path, including loading existing files. |
| `expenses/storage.py` | Rejected | Strict loading would break existing ledgers; out of scope. |
| `expenses/validation.py` (new) | Rejected | Two small checks don't need a new module. |
| `tests/test_models.py` (new), `tests/test_storage.py` | Rejected | They only follow from the rejected changes. |
| `expenses/report.py`, `data/`, everything else | Not to be touched | Not part of the task. |

**Revised instruction** (`prompts/2_revised.txt`):

```
Add input validation to the `add` command only, so bad input never reaches the CSV file.

Scope:
- You may change ONLY expenses/cli.py and tests/test_cli.py.
- Do not modify models.py, storage.py, report.py or any other file, and do not create new files.
- Do not change how existing CSV files are loaded, and do not change the list or summary commands.

Rules for `add` (reject anything else):
1. amount must be a finite number greater than 0. Reject 0, negatives, nan and inf.
2. category must not be empty after stripping whitespace.
Nothing else: no maximum amount, no length limits, no date rules.

Failure behaviour: report the problem with argparse's normal error mechanism (message on stderr,
exit code 2, the same as the existing non-numeric amount case) and write nothing to the file
(it must not be created or changed).

Tests: add one test per rule in tests/test_cli.py, each checking the exit code is 2 and the CSV
file was not created. Keep the existing tests unchanged.
Do not run anything that writes outside this repository.
```

**The revised plan** (`outputs/2_revised_planfile.md`). This time the agent read `cli.py`, `test_cli.py`, `models.py` and `storage.py`. Reading the last two is fine: it needed to know how `Expense` and `append_expense` behave, and it proposed **no changes** to them. Its plan:

- In `cli.py`, add two argparse type functions, `positive_amount` (convert to float, reject unless finite and > 0) and `non_empty_category` (reject if blank after strip, otherwise return the text unchanged so the existing normalisation in `main` still runs).
- Errors happen during argument parsing, so `append_expense` is never reached and nothing is written.
- In `test_cli.py`, two tests: amounts `0`, `-5`, `nan`, `inf`, and categories `""`, `"   "`, each checking exit code 2 and no file.

All of it is inside the approved files, and it matches the rules exactly, so **I approved this plan**.

**Enforcing the scope, not just asking for it.** For the execute run I didn't rely on the agent following the instruction. The permission rules allowed only `Read`, `Glob`, `Grep`, `Edit(./expenses/cli.py)` and `Edit(./tests/test_cli.py)`. Anything else would be denied. During the run the agent tried to run the test suite **three times** (twice in PowerShell, once in Bash), and **all three were denied** (recorded in `outputs/3_execute.jsonl` under `permission_denials`). Its final message said so honestly: "I couldn't run the tests… none of this has been run yet". So verification was left to me, which is where I wanted it.

## 4. Final diff

`git status` in the agent's copy after the run showed **only** `expenses/cli.py` and `tests/test_cli.py` modified (2 files, +39 / −2). Full diff in `docs/week4/final.diff`:

```diff
--- a/expenses/cli.py
+++ b/expenses/cli.py
@@ -1,4 +1,5 @@
 import argparse
+import math
 from datetime import date
@@ -8,14 +9,30 @@
 DEFAULT_FILE = "data/expenses.csv"
 
 
+def positive_amount(text):
+    try:
+        value = float(text)
+    except ValueError:
+        raise argparse.ArgumentTypeError(f"invalid amount: {text!r}")
+    if not math.isfinite(value) or value <= 0:
+        raise argparse.ArgumentTypeError(f"amount must be a finite number greater than 0, got {text!r}")
+    return value
+
+
+def non_empty_category(text):
+    if not text.strip():
+        raise argparse.ArgumentTypeError("category must not be empty")
+    return text
+
+
 def build_parser():
@@
     add = commands.add_parser("add", help="record a new expense")
-    add.add_argument("category")
-    add.add_argument("amount", type=float)
+    add.add_argument("category", type=non_empty_category)
+    add.add_argument("amount", type=positive_amount)
     add.add_argument("--note", default="")
```

```diff
--- a/tests/test_cli.py
+++ b/tests/test_cli.py
+    def test_add_rejects_non_positive_or_non_finite_amount(self):
+        for amount in ["0", "-5", "nan", "inf"]:
+            with self.subTest(amount=amount), tempfile.TemporaryDirectory() as tmp:
+                path = Path(tmp) / "expenses.csv"
+                with redirect_stderr(io.StringIO()), redirect_stdout(io.StringIO()):
+                    with self.assertRaises(SystemExit) as ctx:
+                        main(["--file", str(path), "add", "Food", amount])
+                self.assertEqual(ctx.exception.code, 2)
+                self.assertFalse(path.exists())
+
+    def test_add_rejects_blank_category(self):
+        for category in ["", "   "]:
+            ... same shape, with main(["--file", str(path), "add", category, "5"]) ...
```

**My diff review**, line by line against the revised instruction:

| Check | Result |
| --- | --- |
| Only `cli.py` and `test_cli.py` changed | ✓ (confirmed with `git status`, not just the agent's summary) |
| Amount rule: finite and > 0 | ✓ `math.isfinite(value)` and `value <= 0` rejected |
| Category rule: not blank after strip | ✓ and it returns the original text, so `main` still trims and lowercases |
| argparse error, exit 2 | ✓ uses `ArgumentTypeError`, argparse's own mechanism |
| Nothing written on failure | ✓ checks run while parsing, before `append_expense` |
| No extra rules (caps, lengths, dates) | ✓ none added |
| `list` / `summary` / loading unchanged | ✓ not touched |
| Existing tests unchanged | ✓ only additions |
| Style matches the file | ✓ small functions, standard library only (`math`) |

**One weakness I found in the tests:** they only check "exit code 2 and no file". argparse *also* exits with code 2 for completely different reasons, such as treating `-5` as an unknown option. So a test could pass for the wrong reason. The agent even flagged this risk for `-5` itself. I checked the actual error messages by hand (section 5c).

**Decision: accepted**, and copied into my real repository unchanged.

## 5. Test results and independent verification

All output is in `docs/week4/verification.txt`.

**a) Full test suite**, after applying the change to my real repository:

```
> python -m unittest
......................
----------------------------------------------------------------------
Ran 22 tests in 0.108s

OK
```

That's 20 old tests and 2 new ones; all passing.

**b) Do the new tests actually test the change?** I put the **original** `cli.py` back and ran the new tests against it:

```
FAIL: test_add_rejects_blank_category (category='')
FAIL: test_add_rejects_blank_category (category='   ')
FAIL: test_add_rejects_non_positive_or_non_finite_amount (amount='0')
FAIL: test_add_rejects_non_positive_or_non_finite_amount (amount='-5')
FAIL: test_add_rejects_non_positive_or_non_finite_amount (amount='nan')
FAIL: test_add_rejects_non_positive_or_non_finite_amount (amount='inf')
FAILED (failures=6)
```

Every case fails on the old code, so the tests aren't just passing with whatever the code happens to do.

**c) Manual runs: is each rejection for the right reason?**

| Input | Message on stderr | Exit | File created? |
| --- | --- | --- | --- |
| `add food 0` | `argument amount: amount must be a finite number greater than 0, got '0'` | 2 | no |
| `add food -5` | `… greater than 0, got '-5'` (so it **is** read as the amount, not an option) | 2 | no |
| `add food nan` | `… greater than 0, got 'nan'` | 2 | no |
| `add food inf` | `… greater than 0, got 'inf'` | 2 | no |
| `add food 1e400` (overflows to inf) | `… greater than 0, got '1e400'` | 2 | no |
| `add food abc` | `argument amount: invalid amount: 'abc'` | 2 | no |
| `add '' 5` / `add '   ' 5` | `argument category: category must not be empty` | 2 | no |
| `add food -inf` | `the following arguments are required: amount` ⚠ | 2 | no |
| `add food -- -inf` | `… greater than 0, got '-inf'` | 2 | no |

`-inf` is rejected, but **for the wrong reason**: argparse reads it as an option, not an amount. When forced to be the amount with `--`, the new check rejects it correctly. The outcome is safe either way, and this is exactly the kind of thing that "exit code 2" tests can't tell apart.

**d) Valid input still works:**

```
> add ' Food ' 12.50 --note lunch --date 2026-11-01   ->  Added 12.50 to food   (exit 0)
> add food 0.01                                       ->  Added 0.01 to food    (exit 0)
date,category,amount,note
2026-11-01,food,12.50,lunch
2026-11-09,food,0.01,
```

**e) Existing data unaffected.** `summary` on `data/sample.csv` with the old and new `cli.py` gives identical output (rent 650.00, food 71.15, transport 6.40, total 727.55).

**f) A gap in my own rule.** `add food 0.001` is accepted (it *is* greater than 0) but is stored as `0.00`. So a zero amount can still get into the ledger. The agent did what I asked; my rule was incomplete. I've noted it as a follow-up ("amount must be at least 0.01") instead of widening this task after the plan was approved.

## 6. Reflection: what agent mode saved, and what review it added

**What it saved.**

- **Exploration and drafting.** In one pass the agent read the whole repository, found the real weak points (including ones I hadn't thought of, such as `total` clashing with the summary row and `12.345` being silently rounded), and wrote a working change plus tests in the house style.
- **The first plan was useful even though I rejected it.** It worked like a free design review: it surfaced decisions (refunds? future dates? what to do with a bad ledger?) that I now know I have to make on purpose, as separate tasks.

**What extra review it created.**

- **Reviewing a plan is real work.** The first plan proposed 7 files and several product decisions in confident, reasonable language. I had to read it closely to see that "validation" quietly included "existing ledgers may stop loading".
- **Scope has to be enforced, not just requested.** I wrote the limits into the instruction *and* into the permission rules, and then checked `git status` myself rather than trusting the agent's summary of what it changed.
- **Passing tests weren't enough.** The agent's tests were correct but loose (exit code only). I had to check them against the old code, read the actual error messages, and try edge cases (`-inf`, `1e400`, `0.001`). That found one wrong-reason rejection and one gap in my own specification, and the test suite caught neither.
- **Verification was entirely my job,** because I blocked the shell. That was deliberate, but it means the time saved writing code partly went into running and checking it.

**Overall:** for a change this small, the agent saved me the coding, but not the thinking. The value came from treating it as **plan → narrow → enforce → verify**, rather than "ask and accept".
