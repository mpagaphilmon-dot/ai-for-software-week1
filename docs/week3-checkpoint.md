# Week 3 checkpoint: comments are prompts

Philmon · 28 October 2026

## 0. Setup

Same repository as Weeks 1 and 2: a small Python command-line expense tracker (standard library only, Python 3.10).

**The task.** Add a helper to `expenses/report.py` that picks out the expenses in a date range, for example "everything in September". This is the kind of small function an in-editor assistant finishes from a comment.

**How the suggestions were generated.** I used Claude Code 2.1.311 as an inline completion engine. Each run was a new `claude -p` session with **no tools**, started in an empty folder, so it could see only what I pasted in. The prompt was the same as what an editor's ghost-text feature sees: `expenses/models.py` as a neighbouring open tab, the whole of `expenses/report.py`, my comment at the end, and a `<CURSOR>` marker after it. The only instruction was "output only the code to insert at the cursor". So **the comment was the only spec**, which is the situation this checkpoint is about.

To show what the vague comment leaves to chance, I ran it **three times** and the precise comment **twice**. Every file is in `docs/week3/`:

| Path | Contents |
| --- | --- |
| `prompts/vague_comment.txt`, `prompts/precise_comment.txt` | the two comments |
| `prompts/vague_full.txt`, `prompts/precise_full.txt` | the exact text sent to the model |
| `outputs/vague_run1-3.py`, `outputs/precise_run1-2.py` | each suggestion, unedited |
| `accepted_report.diff`, `accepted_tests.diff` | the final accepted change |
| `vague_vs_tests.txt`, `manual_check.txt` | verification output |

---

## 1. The vague comment and the generated suggestion

**Comment:**

```python
# filter expenses by date
```

**Suggestions** (three separate runs):

```python
# run 1
def filter_by_date(expenses, start, end):
    """Return the expenses dated between start and end, inclusive."""
    return [e for e in expenses if start <= e.day <= end]

# run 2
def expenses_between(expenses, start, end):
    """Expenses dated from start to end, inclusive, in chronological order."""
    return sorted((e for e in expenses if start <= e.day <= end), key=lambda e: e.day)

# run 3
def filter_by_date(expenses, start, end):
    """Return the expenses dated from start to end, inclusive."""
    return [e for e in expenses if start <= e.day <= end]
```

Each one looks fine on its own, and that is the risk: had I pressed Tab on any of them, I would have accepted decisions I never made.

## 2. The precise comment and the improved suggestion

**Comment.** It names the data shape, the expected behaviour and the failure mode:

```python
# expenses_between(expenses, start, end) -> list of Expense
# Data shape: `expenses` is a list of Expense records (expenses/models.py) whose
#   `day` is a datetime.date; `start` and `end` are datetime.date objects, not strings.
# Behavior: keep every expense with start <= e.day <= end. Both bounds are
#   INCLUSIVE, so an expense dated exactly on `start` or `end` is kept. Return a
#   new list in the same order as the input (do not sort); never modify the input.
#   An empty input list returns [].
# Failure mode: if start > end, raise ValueError("start must not be after end")
#   instead of silently returning [], which would hide a swapped-argument bug.
```

**Suggestion.** Both runs gave exactly the same code:

```python
def expenses_between(expenses, start, end):
    """Expenses dated from start to end inclusive, in their original order."""
    if start > end:
        raise ValueError("start must not be after end")
    return [e for e in expenses if start <= e.day <= end]
```

**My review before accepting**, line by line against the comment:

| Requirement in the comment | In the suggestion? |
| --- | --- |
| Name and arguments `expenses_between(expenses, start, end)` | ✓ |
| Inclusive at both ends | ✓ `start <= e.day <= end` |
| Same order as input, no sort | ✓ list comprehension, no `sorted` |
| Input not modified | ✓ builds a new list |
| Empty input gives `[]` | ✓ comprehension over nothing (the guard only compares the dates) |
| `start > end` raises `ValueError` with that message | ✓ checked before filtering, so it also fires on an empty list |
| Style matches the file (one-line docstring, no extra imports) | ✓ |

One thing I checked that the comment does not cover: if someone passes strings such as `"2026-09-01"`, comparing them with `e.day` raises `TypeError`. That is loud, not silent, so I am happy with it. **Decision: accepted.**

## 3. The final accepted change

`docs/week3/accepted_report.diff` (in `expenses/report.py`, after `monthly_total`):

```diff
@@ -30,3 +30,19 @@ def average_by_category(expenses):
 def monthly_total(expenses, year, month):
     """Sum of the expenses dated in the given year and month, rounded to cents."""
     return round(sum(e.amount for e in expenses if e.day.year == year and e.day.month == month), 2)
+
+
+# expenses_between(expenses, start, end) -> list of Expense
+# Data shape: `expenses` is a list of Expense records (expenses/models.py) whose
+#   `day` is a datetime.date; `start` and `end` are datetime.date objects, not strings.
+# Behavior: keep every expense with start <= e.day <= end. Both bounds are
+#   INCLUSIVE, so an expense dated exactly on `start` or `end` is kept. Return a
+#   new list in the same order as the input (do not sort); never modify the input.
+#   An empty input list returns [].
+# Failure mode: if start > end, raise ValueError("start must not be after end")
+#   instead of silently returning [], which would hide a swapped-argument bug.
+def expenses_between(expenses, start, end):
+    """Expenses dated from start to end inclusive, in their original order."""
+    if start > end:
+        raise ValueError("start must not be after end")
+    return [e for e in expenses if start <= e.day <= end]
```

I kept the comment in the code because it is now the function's spec. I also added five tests to `tests/test_report.py` (`docs/week3/accepted_tests.diff`), one for each rule in the comment:

```python
    def test_expenses_between_includes_both_bounds(self):
        self.assertEqual(
            expenses_between(SAMPLE, date(2026, 9, 3), date(2026, 9, 15)),
            SAMPLE[1:4],
        )

    def test_expenses_between_keeps_input_order(self):
        shuffled = [SAMPLE[5], SAMPLE[0], SAMPLE[4]]
        self.assertEqual(
            expenses_between(shuffled, date(2026, 9, 1), date(2026, 10, 31)),
            shuffled,
        )

    def test_expenses_between_does_not_modify_input(self):
        expenses = list(SAMPLE)
        expenses_between(expenses, date(2026, 10, 1), date(2026, 10, 1))
        self.assertEqual(expenses, SAMPLE)

    def test_expenses_between_of_nothing_is_empty(self):
        self.assertEqual(expenses_between([], date(2026, 9, 1), date(2026, 9, 30)), [])

    def test_expenses_between_rejects_start_after_end(self):
        with self.assertRaisesRegex(ValueError, "start must not be after end"):
            expenses_between(SAMPLE, date(2026, 10, 1), date(2026, 9, 1))
```

The tests are mine, not the assistant's. If the tool writes both the code and the tests, the tests only show that the code agrees with itself.

## 4. Review: what the vague version guessed, and what the precise version constrained

| Hidden decision | Vague comment: what the tool guessed | Precise comment: what it constrained |
| --- | --- | --- |
| Function name | `filter_by_date` twice, `expenses_between` once: **not stable between runs** | `expenses_between`, every time |
| Type of `start` / `end` | assumed `date` without saying so | stated as `datetime.date`, not strings |
| Are the bounds inclusive? | yes in all three, but nothing in my comment said so: a coin I did not see being tossed | inclusive at both ends, with the reason |
| Order of results | run 2 **sorted by date**; runs 1 and 3 kept input order | same order as input, explicitly "do not sort" |
| Swapped dates (`start > end`) | all three **silently return `[]`** | raises `ValueError` with a fixed message |
| Empty input | `[]` (by accident of the code) | `[]` (by requirement) |

**What this shows.** My vague comment was not a description of the code; it was a prompt, and a weak one. The tool did not refuse or ask. It filled every gap with a plausible guess, and the guesses changed from run to run. The worst one is the failure mode. With swapped dates, every vague suggestion returns an empty list, which looks just like "you spent nothing in that period". In a report, that is a wrong answer that looks right. The precise comment did not make the tool smarter. It took the decisions away from the tool and made them mine, and then two runs agreed exactly.

## 5. Verification

**a) Tests on the accepted code** (whole suite, including all Week 2 changes):

```
> python -m unittest
....................
----------------------------------------------------------------------
Ran 20 tests in 0.159s

OK
```

**b) Do the tests actually catch the guesses?** I put each vague suggestion into a copy of the repository instead of the accepted code (renamed to `expenses_between` so the same tests could run) and ran the report tests (`docs/week3/vague_vs_tests.txt`):

```
vague_run1:  FAIL test_expenses_between_rejects_start_after_end      FAILED (failures=1)
vague_run2:  FAIL test_expenses_between_keeps_input_order
             FAIL test_expenses_between_rejects_start_after_end      FAILED (failures=2)
vague_run3:  FAIL test_expenses_between_rejects_start_after_end      FAILED (failures=1)
```

So the tests are not just agreeing with the accepted code. They fail on exactly the guesses described in section 4.

**c) Manual check on the real data** (`data/sample.csv`, `docs/week3/manual_check.txt`):

```
> python -c "...expenses_between(load_expenses('data/sample.csv'), date(2026,9,1), date(2026,9,30))..."
2026-09-02 food 12.5
2026-09-03 transport 3.2
2026-09-10 food 48.9
2026-09-15 rent 650.0
September total: 714.6
swapped -> ValueError start must not be after end
```

By hand: the September rows are 12.50 + 3.20 + 48.90 + 650.00 = **714.60** ✓. The two October rows are left out ✓, and swapped dates fail loudly ✓.

## 6. What I learned

- **A comment in front of an assistant is a prompt.** "filter expenses by date" read like documentation to me. To the tool it was an under-specified request, and it answered with guesses.
- **The tool will not ask.** Ghost text has no "did you mean inclusive?" step. Anything the comment does not settle gets settled quietly, and it may be settled differently next time (run 2 sorted, runs 1 and 3 did not).
- **Name the failure mode.** The most dangerous guess was the silent `[]` on swapped dates, because it looks like a valid result. Writing the failure into the comment turned a silent bug into an error.
- **Accepted code is still reviewed code.** I accepted the precise suggestion only after checking it line by line against the comment, writing my own tests, and showing that those tests fail on the vague versions.
