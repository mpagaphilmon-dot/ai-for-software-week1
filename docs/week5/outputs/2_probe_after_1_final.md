If `start` is after `end`, `expenses_between` raises `ValueError("start must not be after end")`. It does not return an empty list, because an empty list would hide a bug where the two dates were passed in the wrong order. It does not sort anything. It returns a new list holding every expense where `start <= e.day <= end`, counting both end dates, in the same order as the input. It never changes the input list, and an empty input gives `[]`.

**Files I looked at:**
- `CLAUDE.md`: loaded automatically. It says which files count as the source of truth and warns that the `docs/`, `wk*/` and `check/` folders have out-of-date copies of the code.
- `expenses/report.py`: I read the whole file.
- `tests/test_report.py`: I searched it for the `expenses_between` tests. `test_expenses_between_rejects_start_after_end` checks the error and `test_expenses_between_keeps_input_order` checks the order, so both match the code.
- A search across the repo also matched 11 files under `docs/`, such as `docs/week3/outputs/precise_run1.py` and `vague_run2.py`. I saw their names in the search results but didn't open them.

**Authoritative source:** `expenses/report.py:44-48`. Section 1 of `CLAUDE.md` says the real behaviour is defined in `expenses/*.py`, and that the `docs/` files are coursework archives and rejected AI drafts. Some of them define functions with the same names but different behaviour, so I left them out on purpose. I used the tests only to confirm what the code does, not as a second definition.