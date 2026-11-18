**1. Missing file**
- L16-17: if the file doesn't exist, it returns `[]`.
- Nothing in `load_expenses` (L10-30) creates a file or folder, so the file is not created.

**2. Header row**
- L36: `is_new` is set only if the file doesn't exist before the write.
- L41-42: the header is written only when `is_new` is true, so only by the first `append_expense` call on a new path. `load_expenses` never writes one.
- L37: missing parent folders are created first.

**3. Field conversion**

| Field | Load | Save |
|---|---|---|
| date | L24: `date.fromisoformat` | L45: `.isoformat()` |
| category | L25: `.strip().lower()` | L46: written as-is, with no strip or lowercasing |
| amount | L26: `float(...)` | L47: formatted to 2 decimal places (`12.5` → `12.50`) |
| note | L27: empty or missing → `""` | L48: written as-is |

- L7: the column order is `date, category, amount, note`.

**4. On disk after two appends**

Two appends, which I ran with example values (`food`/12.5/`lunch`, then `travel`/3/`bus, return`), produced these exact bytes:
```
date,category,amount,note\r\n2026-10-01,food,12.50,lunch\r\n2026-10-02,travel,3.00,"bus, return"\r\n
```
- L39-40: the file is opened in append mode with `newline=""` and written with `csv.DictWriter`.
- The `\r\n` line endings and the quotes around a note containing a comma come from the `csv` module's defaults. Neither is set explicitly in the code.
