I've written the plan but haven't changed any code yet, since plan mode is on. The plan is at `C:\Users\Administrator\.claude\plans\add-input-validation-to-wobbly-stearns.md`. The approve-plan tool isn't available in this session, so please reply to approve it or ask for changes.

**What's wrong now:**
- **Amounts:** `add` takes `nan`, `inf`, `-50`, `0` and huge values. `12.345` is accepted and quietly rounded when written to the file.
- **Category and note:** a category can be empty, contain line breaks, or be `total`, which clashes with the summary's total row. Notes can contain line breaks or control characters and have no length limit.
- **Dates:** future dates are accepted.
- **Loading the file:** a bad header or row stops the program with a raw Python error and no line number. Bad rows written by hand (NaN or negative amounts) load fine and throw off the totals.

**The plan:**
1. **Rules on every expense** (`models.py`): a check runs whenever an `Expense` is created, whether it comes from the command line, the CSV file or code. The amount must be a real number above 0, at most 1,000,000, with no more than 2 decimal places. The category is trimmed and lower-cased, can't be empty, has at most 30 characters (letters, digits, spaces, `_` and `-` only) and can't be `total`. The note is trimmed, has at most 200 characters and no control characters. The date must be a plain date from 1900 or later. Any failure raises `InvalidExpense` with a readable message.
2. **Input helpers** (new `validation.py`): `parse_amount`, `parse_date` and `not_in_future`. These give clear messages for bad text input, and the future-date check is only applied on `add`.
3. **Command line** (`cli.py`): uses those helpers. Errors print `error: …` to stderr and exit with a non-zero code instead of showing a traceback, and nothing is written to the file.
4. **Loading** (`storage.py`): checks the header and every row, and stops with a `LedgerError` that names the file and line, such as `expenses.csv, line 7: amount must be greater than 0`. It refuses to load a bad file rather than skipping rows, because skipped rows would make the totals wrong without anyone noticing.
5. **Tests:** a new `test_models.py`, plus new cases in the command-line and storage tests, including checks that a rejected `add` never creates or changes the file. The existing tests should pass unchanged.

**Decisions you should check:**
- Negative amounts (such as refunds) and zero are rejected.
- Future dates are rejected on `add`; today's date is allowed.
- A bad ledger file stops with an error instead of skipping the bad rows.
- Amounts stay as floats rather than switching to `Decimal`.
- The limits are 1,000,000 for amounts, 30 characters for categories and 200 for notes.