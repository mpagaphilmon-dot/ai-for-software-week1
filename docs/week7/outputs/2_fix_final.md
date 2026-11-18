**Diff summary**

- **`expenses/storage.py`** (+8 −1, in `remove_last_expense` only): the kept bytes now go to `expenses.csv.tmp`, written next to the ledger with the same `write_text(..., encoding="utf-8", newline="")` call as before. `tmp.replace(path)` then swaps it in. A `try/finally` deletes the temp file with `unlink(missing_ok=True)` and lets the error carry on up. It uses pathlib only, and on success the bytes written and the return value are unchanged.
- **`tests/test_storage.py`** (+21): imports `unittest.mock` and adds `test_remove_last_failed_write_keeps_file`. The test patches `Path.write_text` to empty the file it is writing and then raise `OSError("disk full")`, which mimics a failed `open(..., "w")`. It checks that `OSError` is raised, that the ledger is byte-for-byte unchanged, and that no `.tmp` file is left in the folder.
- **Also in the diff:** `expenses/__pycache__/storage.cpython-310.pyc` and `tests/__pycache__/test_storage.cpython-310.pyc`. Git tracks these and running the tests rebuilt them. Revert them before committing.

`python -m unittest`: all 49 tests pass. I didn't run the new test against the old code. The old code calls `write_text` straight on the ledger, so the patch would empty it and the test would fail.

Nothing is committed.