# Week 5 checkpoint: context engineering with a rules file

Philmon · 9 November 2026

## 0. Setup

Same repository as Weeks 1–4: a small Python command-line expense tracker (standard library only).

**The experiment.** I gave the agent the same small task twice, in two **separate copies** of the repository, each with its own git baseline commit. The copies were identical except for one thing: the second copy had my rules file, `CLAUDE.md`, at the root. Claude Code loads that file into the agent's context automatically. The task prompt was word-for-word the same in both runs, so the rules file is the only variable.

**Why this repository is a good test of "stale context".** It isn't only code. `docs/` and `wk*/` hold four weeks of coursework, and that includes **old copies of the code with the same function names**:

| Stale file | What's wrong with it |
| --- | --- |
| `docs/week3/report_before.py` | `report.py` as it was before Week 3 (no `expenses_between`) |
| `docs/week3/outputs/vague_run2.py` | a rejected AI draft of `expenses_between` that **sorts** the result and silently returns `[]` when start > end, the opposite of the real function |
| `docs/week3/outputs/precise_run*.py`, diffs, prompts | more partial copies of `report.py` functions |

A search for `expenses_between` across the whole repo finds 13 files, and only 2 of them are the real code and tests.

**How the agent was run.** Claude Code 2.1.319 (model Claude Opus 5.5), `claude -p`, with edit permission and permission to run `python -m unittest`, and every event logged as JSON. The exact commands are in `docs/week5/prompts/command.txt`. There were two experiments:

1. **Coding task:** once without rules, once with rules.
2. **Source probe:** an explanation question where stale copies are easy to pick up by mistake. I ran it twice without rules and twice with rules.

Everything is in `docs/week5/`:

| Path | Contents |
| --- | --- |
| `prompts/task.txt`, `prompts/source_probe.txt`, `prompts/command.txt` | the two prompts and the exact commands |
| `CLAUDE_v1_used_in_run.md` | the rules file exactly as the agent saw it |
| `../../CLAUDE.md` | the rules file after my correction (v2, one rule added) |
| `outputs/1_task_{before,after}.diff` | each run's code change |
| `outputs/1_task_*_toolcalls.txt`, `*_final.md`, `*.jsonl` | every tool call, the agent's final message, and the raw log |
| `outputs/2_probe_*` | the same for the four source-probe runs |
| `human_correction.diff` | what I changed in the accepted output |
| `verification.txt` | my own test and manual-run output |

---

## 1. Task prompt before adding rules

```
Add a `between` command to the expense tracker CLI: `python -m expenses between 2026-09-03 2026-09-15`
should list the expenses dated in that range and then print their total. Add tests for it.
```

I chose this task on purpose. The rules file contains snippets for a *different* command (`month`), so the agent can't copy an answer. It has to **generalise** the patterns: reuse `report.py`, validate with an argparse type function, and test the error message.

## 2. Task prompt after adding rules

**The prompt itself is unchanged.** The added context is the rules file, which Claude Code puts into the agent's context at the start of the session. I kept the prompt fixed so that any difference in output comes from the rules file and not from better wording. In the probe runs, the agent confirmed in its answer that it had the file ("`CLAUDE.md`: loaded automatically… section 1 says which files define the code").

## 3. The rules file

Full file: `CLAUDE.md` (113 lines as used in the run, 121 after my correction). It's designed, not dumped: it doesn't paste the code in. It gives the agent the **facts it can't easily work out for itself**, with a reason for each rule. Summary:

| Section | Rule | Rationale given to the agent |
| --- | --- | --- |
| 1. Source of truth | Code = `expenses/*.py`, tests = `tests/*.py`. `docs/`, `wk*/`, `check/` are coursework archives: don't read, copy, import or edit them. Check `report.py` before writing a new function. | "Several of them define functions with the same names as the real ones but with different behaviour; grepping the whole repo will find them first." |
| 2. Structure | One job per module (models / storage / report / cli), with a "must not" column. Touch only the files the task needs; don't tidy unrelated code. | Report functions are tested with plain lists; keeping I/O in `cli.py` keeps them that way. |
| 3. Naming and style | `snake_case`, short data nouns, `round(x, 2)` in report, `:.2f` in cli, categories stripped and lower-cased | consistency with the existing code |
| 4. Errors | Bad CLI input → argparse `type=` function raising `ArgumentTypeError` → exit 2. Report errors → `ValueError`. No `sys.exit(1)`, no swallowed errors. | "One mechanism means one exit code and one message format." |
| 5. Tests | `unittest` only; CLI tests use `run()`, a temp dir and `--file`; for a rejection assert **exit code and message** | "argparse also exits 2 for unrelated reasons, so code-only tests can pass for the wrong reason" (the lesson from Week 4) |
| 6. Preferred / Avoid | three real code pairs: reuse the report function; validate with a type function; test a rejection by its message | each pair has its own *why* |
| 7. Libraries | standard library only; no click, pandas, pytest, dateutil | the README promises it |
| 8. Documentation | one usage line in `README.md` per new command | |

One of the Preferred / Avoid pairs, as it appears in the file:

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

## 4. Before / after comparison of the AI output

Both runs produced **working** code: the tests passed in both, and both give the same correct output on the sample data (3 rows, `total 702.10`). The difference is in **how it was built and how well it fits the repository**.

**Without rules** (`outputs/1_task_before.diff`, 2 files, +87 / −3):

```python
between.add_argument("start", type=date.fromisoformat, help="YYYY-MM-DD, inclusive")
...
def print_expense(e):                       # new helper; `list` rewritten to use it
    print(f"{e.day}  {e.category:<12} {e.amount:>9.2f}  {e.note}")
...
class BetweenTests(unittest.TestCase):      # new test class with setUp, unlike the rest of the file
    ...
    def test_rejects_invalid_dates(self):
        ...
        self.assertEqual(ctx.exception.code, 2)          # exit code only
```

**With rules** (`outputs/1_task_after.diff`, 3 files, +78 / −2):

```python
def iso_date(text):
    try:
        return date.fromisoformat(text)
    except ValueError:
        raise argparse.ArgumentTypeError(f"invalid date: {text!r}, expected YYYY-MM-DD")
...
between.add_argument("start", type=iso_date, help="YYYY-MM-DD")
...
    def test_between_rejects_invalid_date(self):         # in the existing CliTests class
        ...
        self.assertEqual(ctx.exception.code, 2)
        self.assertIn("invalid date", err.getvalue())    # exit code AND message
```
plus one line in `README.md`: `python -m expenses between 2026-09-03 2026-09-15`.

| | Without rules | With rules |
| --- | --- | --- |
| **First action** | tried to `cat` **every tracked file**, `docs/` included (blocked only because `cat` wasn't in my allow-list), then `Glob **/*`: **101 paths, 62 of them under `docs/`**, including `report_before.py` and all three `vague_run*.py` | read `cli.py`, `report.py`, `test_cli.py`, `README.md` directly; one Grep limited to `tests/` |
| **Reused `expenses_between` + `total`** | ✓ | ✓ |
| **Bad-date error message** | `invalid fromisoformat value: '2026-13-01'` (Python's internal wording) | `invalid date: '2026-13-01', expected YYYY-MM-DD` |
| **Error mechanism** | argparse, exit 2 ✓ | argparse type function, exit 2 ✓ (the generalised `year_month` pattern) |
| **Bad-date test checks the message** | ✗ exit code only | ✓ |
| **Unrequested change** | refactored `list` to use a new `print_expense` helper | none |
| **Test layout** | new `BetweenTests` class with `setUp`, unlike the rest of the file | added to the existing `CliTests`, same shape as its neighbours |
| **README updated** | ✗ | ✓ one usage line |
| **Tests added / suite** | 6 / 28 pass | 4 / 26 pass |
| **Cost, turns, time** | $0.35, 16 turns, 59 s | $0.34, 15 turns, 58 s |

**The specific quality difference I observed:** the no-rules output was *correct* but *drifted*: a refactor nobody asked for, its own error wording, its own test layout, and a test that can pass for the wrong reason. The with-rules output was **smaller and more consistent with the existing code**. It followed rules it could only have learned from the file: the `type=` function pattern applied to a new type (date instead of month), the message assertion, the README line, and no tidying. The rules didn't make the agent smarter, and they cost nothing extra. What they did was **narrow down what it chose to change**.

**Did the agent obey each rule?** Checked against the diff:

| Rule | Obeyed? |
| --- | --- |
| 1 Source of truth / reuse `report.py` | ✓ used `expenses_between` and `total`; no file under `docs/` opened |
| 2 Small change, no tidying | ✓ (and it **duplicated** the one-line print format rather than refactor `list`; see section 7) |
| 4 argparse `type=` function, exit 2 | ✓ for single dates; **improvised** for start > end (see section 7) |
| 5 `unittest`, `run()`, temp dir, `--file`, message asserted | ✓ |
| 7 Standard library only | ✓ |
| 8 README usage line | ✓ |

## 5. Source audit

**a) Coding task: which files were used.**

| | Should have used | Used without rules | Used with rules |
| --- | --- | --- | --- |
| `expenses/cli.py`, `report.py` | ✓ | ✓ read | ✓ read |
| `tests/test_cli.py` | ✓ | ✓ read | ✓ read |
| `README.md` | ✓ (usage section) | ✗ | ✓ read and updated |
| `models.py`, `storage.py`, `__main__.py` | optional | read | not needed |
| `docs/**` stale copies | ✗ never | **pulled into context** by `Glob **/*` (names of 62 files; full contents attempted via `cat`, denied) | ✗ never listed |

**b) Source probe** (`prompts/source_probe.txt`): *"What does `expenses_between` do when start is after end, and does it sort? List every file you looked at and which one you treated as authoritative."* The correct answer (from `expenses/report.py`) is: it raises `ValueError` and does **not** sort. The stale draft `vague_run2.py` says the opposite on both points.

| Run | Search | Stale files seen | Answer | Authority chosen |
| --- | --- | --- | --- | --- |
| No rules #1 | Grep whole repo | **11 `docs/` files** incl. `vague_run2.py` (names only) | ✓ correct | `report.py`, reasoned from "the module the tests import" |
| No rules #2 | Grep whole repo | same 11 | ✓ correct | same reasoning |
| Rules #1 | Read `report.py`, then Grep whole repo | 11 (names only) | ✓ correct | `report.py`, **citing CLAUDE.md section 1** |
| Rules #2 | Read `report.py`, Grep **`tests/` only** | **none** | ✓ correct | `report.py`, citing CLAUDE.md section 1; "didn't search the whole repo and didn't open any of those folders" |

**What I conclude, honestly:** the model got the right answer **every time, even without rules**. It reasoned its way to the real file and even used `docs/week3/vague_vs_tests.txt` to work out that the drafts were wrong. So the rules file didn't fix a wrong answer here. What it changed:

- **Where the agent looked:** in both rules probe runs, the *first* action was to read `report.py`. Both no-rules probes started with a repo-wide search instead. In one of the two rules probes the stale files never entered the context at all.
- **Why it trusted the source:** with rules, the agent cited a stated policy instead of inferring it. That matters most with a weaker model, or a stale copy that *isn't* obviously labelled "vague" or "before".

**What I corrected in the sources:**
- Section 1 of the rules file now names `docs/`, `wk*/`, `check/` as archives, with the reason, and points the agent to `expenses/` and `tests/` first.
- The agent's task-run summary said it "couldn't run the command against `data/sample.csv`" (that call was outside my allow-list). So I ran it myself; see section 6.

## 6. Verification (my own runs)

Full output in `docs/week5/verification.txt`. After accepting the with-rules change plus my correction:

```
> python -m unittest
Ran 26 tests in 0.174s
OK
```

| Command (`--file data/sample.csv`) | Output | Exit |
| --- | --- | --- |
| `between 2026-09-03 2026-09-15` | 3 rows (both end dates included), `total 702.10` | 0 |
| `between 2026-10-01 2026-10-31` | 2 rows, `total 12.95` | 0 |
| `between 2026-09-15 2026-09-03` | `expenses between: error: start date 2026-09-15 must not be after end date 2026-09-03` | 2 |
| `between 2026-13-01 2026-09-15` | `argument start: invalid date: '2026-13-01', expected YYYY-MM-DD` | 2 |
| `between tomorrow 2026-09-15` | `argument start: invalid date: 'tomorrow', …` | 2 |
| `between 2026-09-03` | `the following arguments are required: end` | 2 |
| `--file nope.csv between …` | `total 0.00`, no file created | 0 |
| `summary`, `list` | unchanged (total 727.55) | 0 |

## 7. One place the agent still needed human correction

**The problem.** Start > end needs *both* dates, so it can't be checked by a `type=` function. My rules didn't cover that case. The agent improvised sensibly: it kept exit code 2 by calling `parser.error(...)`. But it used the **top-level** parser, so this one error looked different from every other `between` error:

```
usage: expenses [-h] [--file FILE] {add,list,summary,between} ...     <- start > end (agent)
expenses: error: start date 2026-09-15 must not be after end date 2026-09-03

usage: expenses between [-h] start end                                <- every other bad input
expenses between: error: argument start: invalid date: ...
```

Its test only checked `assertIn("must not be after", …)`, so it passed anyway.

**My correction** (`docs/week5/human_correction.diff`, +4 / −3):

```diff
     between.add_argument("end", type=iso_date, help="YYYY-MM-DD")
+    # start > end needs both values, so it is checked after parsing; report it
+    # through this subparser so the usage line matches its other errors.
+    between.set_defaults(error=between.error)
     return parser
 ...
-    parser = build_parser()
-    args = parser.parse_args(argv)
+    args = build_parser().parse_args(argv)
 
     if args.command == "between" and args.start > args.end:
-        parser.error(f"start date {args.start} must not be after end date {args.end}")
+        args.error(f"start date {args.start} must not be after end date {args.end}")
```
and the test now asserts `"expenses between: error: start date 2026-09-15 must not be after"`. I checked that the tightened test **fails on the agent's version** and passes on mine (`verification.txt` section b).

**And I fixed the context, not just the code.** I added a rule to section 4 of `CLAUDE.md` for "a check that needs two arguments", with the pattern and the reason. Next time the agent won't have to guess. (`docs/week5/CLAUDE_v1_used_in_run.md` is the version the agent actually saw.)

**A judgement call I left as-is:** the with-rules output copies the one-line row format from `list` instead of sharing it (the no-rules run made a helper). That follows my "don't tidy unrelated code" rule. For one line it's acceptable, but it's a trade-off the rule created, and I'd revisit it if a third command needs the same format.

**Line endings:** the agent's edited files came back with Windows CRLF line endings, while the repo uses LF. I converted them back before accepting.

## 8. What I learned

- **A strong model can often find the right source anyway. The rules file mainly removed drift.** The biggest visible difference wasn't correctness. It was that the no-rules run made its own choices in several places (error wording, test layout, an unrequested refactor, no README line), and the with-rules run stayed with the existing conventions.
- **Rules need reasons.** The `month` snippets were never copied. The agent applied the *reason* ("one mechanism, one message format") to dates. Where I had given no rule (a check across two arguments), it guessed.
- **Context hygiene is about what goes *in*.** Without rules, the agent's first move was to load the whole repo, which would have put 60+ stale coursework files into its context. One sentence in the rules file ("these folders are archives, here's why") kept them out.
- **Check the source, not just the answer.** All six runs got a correct answer, but only the tool-call logs show *which* files it was based on. That's the evidence that the right source of truth was used.
- **Every human correction should update the rules file,** otherwise I'll be making the same correction next week.

## 9. AI-use declaration

- **Agent under test:** Claude Code 2.1.319 (Claude Opus 5.5), run non-interactively (`claude -p`) in isolated copies of the repository, for the two coding runs and four probe runs. The logs and diffs are included unchanged.
- **Assistant:** I also used Claude Code as my assistant to draft the rules file from the existing code and tests, set up the isolated copies, extract tool calls from the logs, and draft this write-up and its tables.
- **My part:** I chose the task and the probe so stale sources would matter. I reviewed both diffs against the rules, ran the tests and manual checks myself, found the parser/usage-line inconsistency, wrote the correction and the extra rule, and decided what to accept. The accepted code is the with-rules agent output plus my +4 / −3 correction.
