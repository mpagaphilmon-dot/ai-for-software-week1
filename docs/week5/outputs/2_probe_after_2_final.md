If `start` is after `end`, `expenses_between` raises `ValueError("start must not be after end")`. It does not return an empty list, because an empty result would hide a bug where the two dates were passed in the wrong order. It does not sort: it returns a new list of the expenses where `start <= e.day <= end`, in the same order as the input, and leaves the input list unchanged. Both bounds are inclusive, so an expense dated exactly on `start` or `end` is kept, and an empty input gives `[]`.

**Files I looked at:**
- `CLAUDE.md` (the repo rules, loaded automatically). Section 1 says which files define the code and which are out-of-date archives.
- `expenses/report.py`: the function and its comment block, lines 35–48.
- `tests/test_report.py`: I searched it for `expenses_between`. It has tests for inclusive bounds, keeping input order, not changing the input, empty input, and the `ValueError` when `start` is after `end`.

**Which one I treated as authoritative:** `expenses/report.py`. `CLAUDE.md` says that file is the source of truth for what the code does. It also warns that `docs/`, `wk*/` and `check/` contain old copies and rejected drafts with the same function names but different behaviour. So I didn't search the whole repo and didn't open any of those folders. The tests agree with `report.py`.