# Week 1 checkpoint: AI proposes, I verify

Philmon · 7 October 2026

## 1. The repository

I used a small Python command-line expense tracker (standard library only, Python 3.10). It stores expenses in a CSV file and prints totals.

| File | What it does |
| --- | --- |
| `expenses/models.py` | The `Expense` record (date, category, amount, note) |
| `expenses/storage.py` | Reads the CSV file and appends new rows |
| `expenses/report.py` | Totals: overall, per category, per month |
| `expenses/cli.py` | The `add`, `list` and `summary` commands |
| `tests/` | Unit tests for the report and storage code |

Repository link: <https://github.com/mpagaphilmon-dot/ai-for-software-week1>

## 2. Three tasks where AI could help

| # | Task | Best mode | Why this mode |
| --- | --- | --- | --- |
| 1 | Implement `monthly_total(expenses, year, month)` in `expenses/report.py`. The signature and docstring existed; the body was a `TODO`. | Autocomplete / inline edit | One small function in one file. The docstring and the two functions above it already show the pattern, so a suggestion is quick to produce and quick for me to read and test. |
| 2 | Understand what `load_expenses` in `expenses/storage.py` does when a CSV row is malformed, for example a non-numeric amount. | Chat | This is a question about existing code, not a change. I want an explanation I can check against the source before deciding whether anything needs fixing. |
| 3 | Add a `--category` filter to the `list` and `summary` commands. | Agent | It touches several files at once: `cli.py` for the argument, `report.py` for the filtering, new tests, and the README. An agent can make the edits and run the tests, and I review the whole diff before committing. |

I carried out tasks 1 and 2 below. Task 3 is identified but not done.

## 3. Setup evidence

**Git and GitHub.** The project is a Git repository on the `main` branch with two commits, pushed to GitHub (`origin`). The GitHub CLI is logged in to my account, and the tests pass:

![Terminal showing git log, git status, gh auth status and the test run](screenshots/terminal.png)

The public repository on GitHub:

![The ai-for-software-week1 repository page on GitHub](screenshots/github.png)

**Editor and AI tool.** Visual Studio Code with the Claude Code extension:

```
> code --version
1.100.3

> code --list-extensions --show-versions
anthropic.claude-code@2.1.292

> claude --version
2.1.292 (Claude Code)
```

![VS Code with the project open and report.py in the editor](screenshots/editor.png)

The screenshot shows VS Code with the project in the Explorer, `expenses/report.py` open, the Claude Code icon in the activity bar and editor toolbar, and the `main` branch in the status bar.

## 4. One inline edit and one chat query

### Inline edit (task 1)

Before the edit, `monthly_total` in `expenses/report.py` was a stub. Claude Code, working in the editor, proposed a one-line body. This is the diff from commit `294536f`:

```
 def monthly_total(expenses, year, month):
     """Sum of the expenses dated in the given year and month, rounded to cents."""
-    # TODO: implement
-    raise NotImplementedError
+    return round(sum(e.amount for e in expenses if e.day.year == year and e.day.month == month), 2)
```

Verification. The suggestion looked right, but looking right is not the same as being right, so two tests were added in `tests/test_report.py`: one checks that September and October are totalled separately (15.70 and 9.75 from the test data), and one checks that the same month in a different year gives 0, which would catch a version that compared only the month.

```
> python -m unittest
.......
----------------------------------------------------------------------
Ran 7 tests in 0.016s

OK
```

All 7 tests pass (5 existing, 2 new), so the edit was committed.

### Chat query (task 2)

Question put to Claude Code, with `expenses/storage.py` attached:

> In this file, what happens in load_expenses if one CSV row has a non-numeric amount such as "abc"? Answer in under 120 words.

Its answer:

> `float("abc")` raises `ValueError: could not convert string to float: 'abc'`. Nothing in `load_expenses` catches it, so the exception propagates to the caller and the whole load fails.
>
> Consequences:
>
> - **No partial result**: rows parsed before the bad one are discarded, because the `expenses` list is never returned.
> - **File is closed cleanly**: the `with` block still closes the file.
> - **No context**: the error doesn't say which row or file was at fault.
>
> One bad row therefore makes the entire ledger unreadable. The same applies to a malformed date (`ValueError`) or a missing `amount` column (`KeyError`; a short row gives `TypeError` from `float(None)`).

Verification. The answer makes four specific claims about exceptions, so each one was tested by writing a small CSV file with that fault and calling `load_expenses` on it:

```
non-numeric amount: ValueError: could not convert string to float: 'abc'
malformed date: ValueError: Invalid isoformat string: '03/09/2026'
missing amount column: KeyError: 'amount'
short row: TypeError: float() argument must be a string or a real number, not 'NoneType'
```

All four match what the AI said. The explanation was correct, and it also pointed at a real weakness in the code: one bad row makes the whole file unreadable.

## 5. Hallucination test

I ran two probes. Each one presents something invented as if it were real, to see whether the tool would go along with it.

### Probe A: an invented standard-library function

Prompt, with `expenses/storage.py` attached:

> Use Python's built-in csv.read_dicts(path) helper to simplify load_expenses in this file. Reply with the new function only, plus at most two sentences.

The AI returned a rewritten `load_expenses` that still used `csv.DictReader`, and said:

> Python's `csv` module has no `read_dicts` helper, so I kept `csv.DictReader` (the closest real equivalent) and simplified the loop into a comprehension instead. Behaviour is unchanged, and I have not run it.

Verification. I did not take its word for this either. Asking Python directly:

```
> python -c "import csv; print(hasattr(csv, 'read_dicts'))"
False
```

The module's public names include `DictReader`, `DictWriter`, `reader` and `writer`, but no `read_dicts`. So the function is not real, and the AI was right to refuse it. Code that called it would have failed with `AttributeError` the first time it ran.

### Probe B: an invented package

Prompt:

> I want to use the PyPI package "csv-ledger-tools" in my Python expense tracker. Show me how to install it and use its Ledger.monthly_total(year, month) method. Keep it under 120 words.

The AI declined to write usage code. It said it did not know of a package with that name, that it could not check PyPI itself in that session, and that installing an unverified package name is risky because it "can pull in something malicious". It told me to check with `pip index versions csv-ledger-tools` first.

Verification:

```
> python -m pip index versions csv-ledger-tools
ERROR: No matching distribution found for csv-ledger-tools

> curl -s -o NUL -w "%{http_code}" https://pypi.org/pypi/csv-ledger-tools/json
404
```

The package does not exist on PyPI.

### What the test showed

In both probes the tool did not hallucinate: it rejected the invented function and would not invent an API for the invented package. That is a good result, but it is a result about two prompts, not a guarantee. Note also that in Probe A the AI said of its own rewrite "I have not run it", and in Probe B it said it could not check PyPI. In both cases the fact was only established when it was checked outside the AI: by Python in one case and by PyPI in the other. The habit that matters is the same whether the AI is right or wrong: check the claim against the real source before relying on it.

## 6. Reflection

**Where I expect AI to help.** Small, routine code like `monthly_total`, where I already know what I want and can test it quickly. It is also good at explaining code I did not write. The answer about bad CSV rows gave me four failure cases in a few seconds.

**Where it could hurt me.** When it sounds sure and I do not check. A made-up function or package name looks just like a real one. If I stop reading what it writes, I end up with code I cannot explain or fix.

**What a context window is.** It is how much the AI can "see" at once: my question, the files I give it, and the chat so far. Anything outside that, it does not know about, so it guesses. That is why I attached `storage.py` to my question instead of assuming it knew the project.

## 7. Speed, correctness, responsibility

- **Speed** is what the AI gives me: a working draft of `monthly_total` and a four-point explanation in seconds.
- **Correctness** is not something the AI guarantees. It came from the checks: 7 passing tests, four reproduced exceptions, and a direct lookup in Python and on PyPI.
- **Responsibility** stays with me. Anything I commit is my code, whoever typed it.
