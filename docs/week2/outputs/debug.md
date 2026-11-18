## Verdict: your hypothesis is wrong

`append_expense` does write the row. It opens the file in append mode (`"a"`), and the `with` block closes the file, which flushes it. The new data is on disk. It just ends up in the wrong place.

## Evidence

I reproduced the bug on a temporary copy, so your `handedit.csv` was not changed:

```
before: b'date,category,amount,note\n2026-09-02,food,12.50,lunch'
Added 5.00 to food
food             12.50
total            12.50
after:  b'date,category,amount,note\n2026-09-02,food,12.50,lunch2026-10-23,food,5.00,snack\r\n'
```

The new row's bytes are there, but they're joined onto `lunch`. This is how `csv.DictReader` reads that line:

```
{'date': '2026-09-02', 'category': 'food', 'amount': '12.50',
 'note': 'lunch2026-10-23', None: ['food', '5.00', 'snack']}
```

## Root cause

Append mode writes from the very end of the file. Because your editor saved the file without a final newline, the new row starts on the same line as the last expense. The reader then sees one record with 7 fields: the note becomes `lunch2026-10-23`, and the extra fields go under the key `None`, which `load_expenses` ignores. So the 5.00 is in the file, but the program never sees it.

## Fix: `expenses/storage.py`

Before appending, the code now looks at the file's last byte. If the file isn't empty and doesn't end in `\n` or `\r`, it writes `\r\n` first. That matches the line ending the `csv` module uses for every row it writes. Files that already end in a newline are written exactly as before, and a new regression test checks that byte for byte.

```diff
     path.parent.mkdir(parents=True, exist_ok=True)

+    # A hand-edited file may lack a trailing newline; without one the new
+    # row would be glued onto the end of the last line.
+    needs_newline = False
+    if not is_new and path.stat().st_size > 0:
+        with path.open("rb") as f:
+            f.seek(-1, 2)
+            needs_newline = f.read(1) not in (b"\n", b"\r")
+
     with path.open("a", newline="", encoding="utf-8") as f:
         writer = csv.DictWriter(f, fieldnames=FIELDS)
+        if needs_newline:
+            f.write("\r\n")
         if is_new:
             writer.writeheader()
```

## Tests: `tests/test_storage.py`

```diff
+    def test_append_to_file_without_trailing_newline(self):
+        existing = Expense(date(2026, 9, 2), "food", 12.5, "lunch")
+        added = Expense(date(2026, 9, 3), "food", 5.0, "snack")
+        with tempfile.TemporaryDirectory() as tmp:
+            path = Path(tmp) / "handedit.csv"
+            path.write_bytes(b"date,category,amount,note\n2026-09-02,food,12.50,lunch")
+            append_expense(path, added)
+            self.assertEqual(load_expenses(path), [existing, added])
+
+    def test_append_to_normal_file_is_unchanged(self):
+        added = Expense(date(2026, 9, 3), "food", 5.0, "snack")
+        original = b"date,category,amount,note\r\n2026-09-02,food,12.50,lunch\r\n"
+        with tempfile.TemporaryDirectory() as tmp:
+            path = Path(tmp) / "expenses.csv"
+            path.write_bytes(original)
+            append_expense(path, added)
+            self.assertEqual(
+                path.read_bytes(), original + b"2026-09-03,food,5.00,snack\r\n"
+            )
```

The first test is the regression test for your bug. The second guards the "normal files unchanged" requirement.

## Test output (`python -m unittest -v`)

```
test_monthly_total_does_not_mix_years (tests.test_report.ReportTests) ... ok
test_monthly_total_only_counts_that_month (tests.test_report.ReportTests) ... ok
test_total (tests.test_report.ReportTests) ... ok
test_total_by_category_is_sorted_largest_first (tests.test_report.ReportTests) ... ok
test_total_of_nothing_is_zero (tests.test_report.ReportTests) ... ok
test_append_to_file_without_trailing_newline (tests.test_storage.StorageTests) ... ok
test_append_to_normal_file_is_unchanged (tests.test_storage.StorageTests) ... ok
test_missing_file_is_empty (tests.test_storage.StorageTests) ... ok
test_round_trip (tests.test_storage.StorageTests) ... ok
----------------------------------------------------------------------
Ran 9 tests in 0.146s

OK
```

I also re-ran your exact steps on a fresh copy of `handedit.csv`. It now shows `food 17.50` / `total 17.50`, and the file ends with `...lunch\r\n2026-10-23,food,5.00,snack\r\n`. I didn't run the new regression test against the old code. From the "after" bytes above, though, it would get a single expense with the note `lunch2026-09-03` and fail.

**Your `handedit.csv`:** it's unchanged, but it still has no final newline. The next `add` will now handle that correctly. A file that's already damaged (one where the old code already joined a row onto the last line) is not repaired by this fix and would need a manual edit.
