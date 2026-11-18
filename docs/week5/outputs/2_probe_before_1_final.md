If `start` is after `end`, `expenses_between` raises `ValueError("start must not be after end")`. It does not return an empty list. The comment above the function says this is on purpose, so a call with the dates swapped fails loudly instead of quietly returning nothing. It does not sort: it returns a new list holding every expense with `start <= e.day <= end` (both dates included), in the same order as the input, and leaves the input list unchanged (`expenses/report.py:44-48`).

**Files I looked at**

- `expenses/report.py`: opened and read in full.
- `tests/test_report.py`: opened and read in full. `test_expenses_between_rejects_start_after_end` (line 76) checks for the `ValueError`, and `test_expenses_between_keeps_input_order` (line 61) checks that a shuffled input comes back in the same shuffled order, not sorted.
- These files only appeared in a repo-wide search for `expenses_between`. I saw the matching lines but did not open them:
  - `docs/week3-checkpoint.md`
  - `docs/week3/accepted_report.diff` and `docs/week3/accepted_tests.diff`
  - `docs/week3/vague_vs_tests.txt`
  - `docs/week3/prompts/precise_comment.txt` and `docs/week3/prompts/precise_full.txt`
  - `docs/week3/outputs/precise_run1.py`, `precise_run2.py` and `vague_run2.py`
  - `docs/week4/verification.txt`
  - `docs/week4/outputs/1_original_plan.jsonl`

**Which one is authoritative:** `expenses/report.py`. It is the module the code actually imports and the tests run against, so it decides what the function really does. The files under `docs/` are records of earlier work: diffs, prompts, and AI-generated drafts. Some of those drafts are known to behave differently; `vague_vs_tests.txt` records them failing the start-after-end and input-order tests. I used the tests in `tests/test_report.py` to confirm my reading of the code, not as the definition itself.