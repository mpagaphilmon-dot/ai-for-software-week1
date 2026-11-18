# Week 2 checkpoint: prompts that reduce guessing

Philmon · 23 October 2026

## 0. Setup

I used the same repository as in Week 1: a small Python command-line expense tracker (standard library only, Python 3.10).

**How the prompts were run.** Every prompt went to Claude Code 2.1.309 (`claude -p`) in a new session. Each session had its own clean copy of the repository, so no run could see another run's prompt, output or edits. After each run I saved the model's reply and a `diff` of what it changed. All of it is in `docs/week2/`:

| Folder | Contents |
| --- | --- |
| `docs/week2/prompts/` | The exact text of every prompt (`p1v` = pair 1 vague, `p1i` = pair 1 improved, and so on) |
| `docs/week2/outputs/` | The model's full reply to each prompt |
| `docs/week2/diffs/` | The code each run changed, compared with the original repository |

**The task I chose** (checkpoint items 1 to 3): a new function in `expenses/report.py` that gives the **average expense per category**. Today `summary` only shows totals.

---

## 1. The vague prompt and the model's output

**Prompt** (`p1v`):

> add an average function to report.py

**Output.** The model replied:

> I added `average(expenses)` to `expenses/report.py`. It returns the mean expense amount rounded to cents, the same way `total` rounds. With no expenses it returns `0` rather than failing with a divide-by-zero error, which matches how `total([])` behaves.
>
> I also added two tests to `tests/test_report.py`: one checks that the three sample expenses average to 8.48, and one checks the empty case. All 9 tests pass.
>
> I didn't connect it to the CLI (`cli.py`), so it's only available in code for now. I can add it as a CLI command if you want.

The code it wrote (`docs/week2/diffs/p1v.diff`):

```python
def average(expenses):
    """Mean expense amount, rounded to cents; zero when there are no expenses."""
    expenses = list(expenses)
    if not expenses:
        return 0
    return round(sum(e.amount for e in expenses) / len(expenses), 2)
```

**What the AI had to guess.** The code is clean and its tests pass, but the prompt left almost every decision to the model:

| Question the prompt did not answer | What the AI guessed |
| --- | --- |
| Average of what: everything, per category, or per month? | One overall average of all expenses |
| What should it be called and what should it return? | `average`, returning a single number |
| What if there are no expenses? | Return `0` |
| Which data should the tests use? | The existing 3-row test list (expected 8.48) |

Each guess is reasonable, but the result is not what I needed. On the real `data/sample.csv` the overall average is **121.26**. One 650.00 rent payment drags it up, so the number says nothing useful about my spending. I could only find this out by running it myself (see section 3).

## 2. The improved prompt and the model's output

**Prompt** (`p1i`). Labels added to show the five parts the assignment asks for:

> **Intent:** the `summary` command shows a total per category. I want a helper that gives the average amount per expense in each category, so I can show it next to the totals later. Only the helper and its tests for now; no CLI change yet.
>
> **Context:** expenses/report.py already has total(), total_by_category() and monthly_total(). Each takes a list of Expense records (expenses/models.py: day, category, amount, note). Categories are already lowercased when they are loaded. Every existing function rounds money to cents with round(x, 2), and total_by_category returns a dict sorted from largest to smallest.
>
> **Task:** add average_by_category(expenses) to expenses/report.py.
>
> **Example** (the rows in data/sample.csv):
> food: 12.50, 48.90, 9.75 -> 71.15 / 3 = 23.7166... -> 23.72
> transport: 3.20, 3.20 -> 3.2
> rent: 650.00 -> 650.0
> average_by_category(...) == {"rent": 650.0, "food": 23.72, "transport": 3.2} (this order)
>
> **Constraints:**
>
> - Standard library only. Python 3.10.
> - Do not change the existing functions, cli.py, storage.py or models.py.
> - Same style as total_by_category: one-line docstring, rounded to cents, sorted largest average first.
> - An empty list returns {} (no ZeroDivisionError).
>
> **Definition of done:**
>
> - The function exists in expenses/report.py.
> - tests/test_report.py has two new tests: the example above, and empty input -> {}.
> - `python -m unittest` passes (run it).
> - Reply with the diff and the test output, nothing else.

**Output.** As instructed, the model replied with only the diff and the test run:

```python
def average_by_category(expenses):
    """Map each category to its average expense, sorted from largest to smallest."""
    totals = defaultdict(float)
    counts = defaultdict(int)
    for e in expenses:
        totals[e.category] += e.amount
        counts[e.category] += 1
    averages = {category: totals[category] / counts[category] for category in totals}
    ranked = sorted(averages.items(), key=lambda item: item[1], reverse=True)
    return {category: round(amount, 2) for category, amount in ranked}
```

```python
    def test_average_by_category_is_rounded_and_sorted_largest_first(self):
        self.assertEqual(
            list(average_by_category(SAMPLE).items()),
            [("rent", 650.0), ("food", 23.72), ("transport", 3.2)],
        )

    def test_average_by_category_of_nothing_is_empty(self):
        self.assertEqual(average_by_category([]), {})
```

```
$ python -m unittest
.........
----------------------------------------------------------------------
Ran 9 tests in 0.043s

OK
```

It also added a `SAMPLE` list to the tests that copies the six rows of `data/sample.csv` (full diff in `docs/week2/diffs/p1i.diff`).

## 3. What changed between the two prompts

| Part | Vague prompt | Improved prompt | Effect on the output |
| --- | --- | --- | --- |
| Intent | none | "average per expense in each category, to show next to the totals" | Per-category function instead of one overall number |
| Context | none | names the existing functions, the `Expense` fields, the rounding and sorting conventions | The new code copies the `total_by_category` pattern (same `defaultdict`, sort and rounding) |
| Example | none | real input and the exact expected dict, in order | Became the first test, so the test checks my numbers, not numbers the AI picked |
| Constraints | none | stdlib only, no other files, empty input gives `{}` | Only `report.py` and its test file changed. Empty input gives `{}`, not `0` |
| Definition of done | none | two named tests, run the suite, reply with diff + test output | The reply is evidence I can check, not a summary |

**Why the improved prompt worked better.** The vague prompt did not get bad code. It got code that answered a different question. The improved prompt took the decisions away from the model: what to compute, what to call it, what to return for edge cases, and what correct looks like. The example did the most. Because I gave the exact expected result, "the tests pass" means "it matches what I worked out by hand", not "it agrees with itself".

**How I verified it** (I did not rely on the model saying the tests passed):

```
> python -m unittest                       # in the improved run's copy
Ran 9 tests ... OK

> python -c "...average_by_category(load_expenses('data/sample.csv'))"
{'rent': 650.0, 'food': 23.72, 'transport': 3.2}     # matches my hand calculation

> python -c "...average(load_expenses('data/sample.csv'))"        # vague version
121.26                                                # technically correct, not useful
```

I kept the improved version: `average_by_category` is now in `expenses/report.py`.

---

## 4. Debugging with a stated hypothesis

**The symptom.** I hand-edited my expenses file. My editor saved it without a newline after the last line. After that, `add` reports success but the expense never shows up:

```
> python -m expenses --file handedit.csv add food 5 --note snack
Added 5.00 to food
> python -m expenses --file handedit.csv summary
food             12.50
total            12.50          # expected 17.50
```

**My hypothesis:** `append_expense` is not actually writing the row, either because the file is opened in the wrong mode or because the write is not flushed before the program exits.

**The debugging prompt** (`debug`, shortened; full text in `docs/week2/prompts/debug.txt`). It gave the model the error, the relevant code and my hypothesis, and it asked the model to **test the hypothesis before fixing anything**:

> Bug: after I hand-edit my expenses file and then run `add`, the new expense disappears. *[steps and output as above]*
>
> My hypothesis: append_expense is not actually writing the row. Maybe the file is opened in the wrong mode, or the write is not flushed before the program exits.
>
> Relevant code: expenses/storage.py (append_expense and load_expenses).
>
> Please test my hypothesis against the code BEFORE fixing anything: reproduce the bug, look at the actual bytes in the file, and tell me whether my hypothesis is right or wrong, with the evidence. If it is wrong, find the real cause.
>
> Then fix it: smallest change, in expenses/storage.py only, standard library only. Normal files (ending in a newline) must be written exactly as before. Add a regression test to tests/test_storage.py.
>
> Done = `python -m unittest` passes. Reply with: verdict on my hypothesis, evidence, root cause, the diff, and the test output.

**The model's verdict: my hypothesis was wrong.** From its reply:

> `append_expense` does write the row. It opens the file in append mode (`"a"`), and the `with` block closes the file, which flushes it. The new data is on disk. It just ends up in the wrong place.

**Evidence it gathered.** These are the bytes on disk before and after the `add`, and what `csv.DictReader` makes of the merged line:

```
before: b'date,category,amount,note\n2026-09-02,food,12.50,lunch'
after:  b'date,category,amount,note\n2026-09-02,food,12.50,lunch2026-10-23,food,5.00,snack\r\n'

{'date': '2026-09-02', 'category': 'food', 'amount': '12.50',
 'note': 'lunch2026-10-23', None: ['food', '5.00', 'snack']}
```

**Root cause.** Append mode writes at the very end of the file. With no final newline, the new row is glued onto the last line. The reader sees one record with seven fields: the note becomes `lunch2026-10-23`, and the new expense's fields go under the key `None`, which `load_expenses` ignores. The row was written; it was just unreadable.

**The fix** (`expenses/storage.py`): before appending, check the last byte and add a line break if one is missing.

```python
    # A hand-edited file may lack a trailing newline; without one the new
    # row would be glued onto the end of the last line.
    needs_newline = False
    if not is_new and path.stat().st_size > 0:
        with path.open("rb") as f:
            f.seek(-1, 2)
            needs_newline = f.read(1) not in (b"\n", b"\r")

    with path.open("a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        if needs_newline:
            f.write("\r\n")
```

The model added two tests: a regression test for the missing newline, and a byte-for-byte test that a normal file is appended exactly as before.

**How I verified it.** The model said: *"I didn't run the new regression test against the old code."* So I ran it myself:

```
# new tests + ORIGINAL storage.py
FAIL: test_append_to_file_without_trailing_newline
Ran 4 tests ... FAILED (failures=1)          # the test does catch the bug

# new tests + FIXED storage.py, and the original steps again
> python -m expenses --file r.csv add food 5 --note snack
Added 5.00 to food
> python -m expenses --file r.csv summary
food             17.50
total            17.50
> python -m unittest
Ran 14 tests ... OK                          # whole suite, with all Week 2 changes
```

**Conclusion.** My hypothesis (the row is not written or not flushed) was wrong, and the evidence on disk proved it. The real cause was a missing line break between the old last line and the new row. Because the prompt asked for a verdict before a fix, the model could not simply agree with me and "fix" something that was not broken, such as adding a `flush()`. That change would have looked plausible and fixed nothing.

## 5. A rule that could have been lost by over-dumping context

**The rule:** *"Normal files (ending in a newline) must be written exactly as before."*

It is one line in the debugging prompt, and it matters most. There are easier fixes that also make the bug go away, for example reading every row and rewriting the whole file. That would change line endings and quoting in every hand-edited file, and on a large file it is slow and risks losing data mid-write. If I had pasted the whole repository, the Week 1 write-up and all earlier outputs into the prompt, this one sentence would have been buried among thousands of lines of unrelated text, and the model could have chosen the rewrite approach. Because the prompt was short and the rule stood out, the model wrote a byte-for-byte test just for it (`test_append_to_normal_file_is_unchanged`).

The same applies to pair 1: the line "total_by_category returns a dict sorted from largest to smallest" is why the new function sorts its results. In a large paste, that convention would only be implied by code, and the model might have missed it.

---

## 6. Complete Week 2 exercises: three prompt rewrites

### Pair 1: new function
Covered in sections 1 to 3 above.

### Pair 2: explain an unfamiliar file (`expenses/storage.py`)

This pair also covers exercise 3: use chat to explain a file, then verify the explanation against the code.

**Weak prompt** (`p2v`): `explain storage.py`

**Output** (shortened; full text in `docs/week2/outputs/p2v.md`). A long, general tour of the file: the CSV format, `load_expenses`, `append_expense`, then a "things worth knowing" list. That list included one real problem: *"An empty file loses its first expense. If the file exists but has 0 bytes, `is_new` is `False`, so no header gets written."* It also gave design advice (use `Decimal`, add error handling) that I had not asked for.

**Improved prompt** (`p2i`):

> **Intent:** I am new to this repo and I will soon add a "delete expense" feature, which means changing expenses/storage.py. Before I touch it I need to know exactly how it reads and writes the CSV file.
>
> Explain expenses/storage.py by answering these questions:
> 1. What does load_expenses return if the file does not exist? Does it create the file?
> 2. When is the header row written?
> 3. How is each field converted on load and on save (date, category, amount, note)?
> 4. What does the file look like on disk after two calls to append_expense on a new path? Show the exact text.
>
> **Constraints:** under 220 words. Every claim must cite the line number it comes from. If something is not in the code, say "not in the code" instead of guessing. Explain only; do not suggest or make changes.
>
> **Example** of the format I want for each point:
>
> - L13-14: missing file -> returns [] and does not create the file.

**Output** (in full in `docs/week2/outputs/p2i.md`): four short sections, each with line references, and a field table:

| Field | Load | Save |
|---|---|---|
| date | L24: `date.fromisoformat` | L45: `.isoformat()` |
| category | L25: `.strip().lower()` | L46: written as-is, with no strip or lowercasing |
| amount | L26: `float(...)` | L47: formatted to 2 decimal places (`12.5` → `12.50`) |
| note | L27: empty or missing → `""` | L48: written as-is |

It ended with the exact bytes after two appends:
`date,category,amount,note\r\n2026-10-01,food,12.50,lunch\r\n2026-10-02,travel,3.00,"bus, return"\r\n`

Note that the model did not just copy my format example: it corrected the line numbers in it (my example said L13-14, but the code is at L16-17).

**Verification against the code.**

| Claim | How I checked | Result |
| --- | --- | --- |
| Missing file returns `[]` at L16-17, file not created | read lines 16-17; called `load_expenses` on a missing path, then checked `exists()` | `[] False` ✓ |
| Header written only when new (L36, L41-42) | read the lines | ✓ |
| Field conversions at L24-27 and L45-48 | read the lines | ✓ |
| `append_expense` writes the category as-is | appended `" Food "` directly | saved as ` Food ` ✓ (the CLI lowercases it before calling) |
| Exact bytes after two appends | ran the same two appends | byte-for-byte match ✓ |
| (weak output) empty file loses its first expense | appended to a 0-byte file, then loaded it | file is `2026-09-02,food,1.00,\r\n` with no header; load returns `[]` ✓ |

**What changed and why it worked better.** The weak prompt got a correct but unfocused essay that mixed explanation with advice, with nothing tied to specific lines, so checking it meant rereading the whole file. The improved prompt said why I needed the explanation (a future delete feature), asked four specific questions, required line numbers and banned guessing. Every claim in the answer could be checked in seconds, and I checked them all. One honest note: the weak prompt's wider scope turned up the empty-file bug, which the focused prompt did not cover because I did not ask. Focused prompts give answers I can check, but they only cover the questions I thought to ask. (I fixed the empty-file bug afterwards; see section 7.)

### Pair 3: tests for the CLI

**Weak prompt** (`p3v`): `write tests for the cli`

**Output** (full in `docs/week2/outputs/p3v.md` and `diffs/p3v.diff`): a 99-line `tests/test_cli.py` with 8 tests covering `add`, `list`, `summary` and bad arguments. They passed. But the AI chose the scope on its own, and by its own account one test, the one comparing against `date.today()`, *"could fail if the run happens to cross midnight"*: a flaky test I never asked for.

**Improved prompt** (`p3i`):

> **Intent:** expenses/cli.py has no tests. I want a few tests that would catch it if the `add` and `summary` commands broke, without touching my real data file.
>
> **Context:** cli.main(argv) takes a list of arguments and returns an exit code; it prints with print(). The --file option picks the CSV file. The existing tests use unittest and tempfile.TemporaryDirectory.
>
> **Task:** create tests/test_cli.py with exactly these three tests:
> 1. `add` then `summary` on a temporary file. **Example:** main(["--file", path, "add", "Food", "12.5", "--note", "lunch"]) returns 0 and prints "Added 12.50 to food"; then `summary` prints a line starting with "food" containing "12.50", and a "total" line containing "12.50".
> 2. `add` normalises the category: " Food " is stored as "food" (check with storage.load_expenses).
> 3. `add` with a non-numeric amount ("abc") exits with SystemExit code 2 (argparse's behaviour).
>
> **Constraints:** unittest and the standard library only (redirect_stdout / redirect_stderr). No pytest, no mocking libraries. Never read or write data/expenses.csv; always pass --file with a temp path. Do not change any file except the new tests/test_cli.py.
>
> **Definition of done:** `python -m unittest` passes (run it) and you reply with the new file and the test output.

**Output** (full in `docs/week2/outputs/p3i.md`): exactly the three tests, all passing (10 tests in total), plus a note that it had confirmed `data/` still held only `sample.csv` after the run. It named two checks it added beyond the spec (exactly one `food` line; no file created on a bad amount). Both stay inside the new file.

**What changed and why it worked better.** "Write tests" has no natural stopping point, so the AI picked one. The improved prompt said what the tests are for (catch `add`/`summary` breaking), listed exactly which tests to write with a concrete example of the expected output, and protected my real data file. The result is smaller, has no time-dependent test, and each test maps to one requirement I can name. **Verified:** I ran `python -m unittest` in that copy (OK) and again after copying the file into the repository (14 tests, OK).

---

## 7. What ended up in the repository

| File | Change | Came from |
| --- | --- | --- |
| `expenses/report.py` | new `average_by_category` | pair 1, improved prompt |
| `tests/test_report.py` | 2 new tests | pair 1, improved prompt |
| `expenses/storage.py` | adds a missing final newline before appending | debugging prompt |
| `tests/test_storage.py` | 2 new tests (regression + unchanged normal file) | debugging prompt |
| `expenses/storage.py` | an existing empty file is treated as new, so the header is written | empty-file bug found by the weak `storage.py` explanation (pair 2), fixed by me |
| `tests/test_storage.py` | 1 new test: appending to an empty file keeps the expense (fails on the old code) | same |
| `tests/test_cli.py` | new, 3 tests | pair 3, improved prompt |

```
> python -m unittest
...............
----------------------------------------------------------------------
Ran 15 tests in 0.069s

OK
```

The outputs of the weak prompts were saved as evidence but not added to the code.

## 8. What I learned

- **A vague prompt does not get wrong code. It gets code for a question the AI chose.** All three weak prompts produced working, tested code. Each one solved a slightly different problem from mine.
- **A concrete example works best when it has the expected answer.** With the expected result in the prompt, a passing test means it matches my numbers, not just the AI's own.
- **A stated hypothesis plus "test it first" stops the AI from just agreeing with me.** My hypothesis was wrong, and the prompt made the model prove that with the bytes on disk before it touched the code.
- **Verification is still my job.** The model told me what it had not checked (running the regression test against the old code). I ran that check, and it is what proves the test catches the bug.
