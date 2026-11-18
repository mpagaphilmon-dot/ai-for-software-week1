import subprocess, sys
from pathlib import Path

MUTANTS = [
    ("M1 total line sums every month", "expenses/cli.py",
     "monthly_total(expenses, year, month):>9.2f", "total(expenses):>9.2f"),
    ("M2 month filter ignores the year", "expenses/report.py",
     "e.day.year == year and e.day.month == month]", "e.day.month == month]"),
    ("M3 shape check removed from year_month", "expenses/cli.py",
     'if not (len(text) == 7 and text.isascii() and text[4] == "-" and text[:4].isdigit() and text[5:].isdigit()):', "if False:"),
    ("M4 default month is always January", "expenses/cli.py",
     "year, month = today.year, today.month", "year, month = today.year, 1"),
    ("M5 categories sorted alphabetically", "expenses/cli.py",
     "for category, amount in total_by_category(expenses_in_month(expenses, year, month)).items():",
     "for category, amount in sorted(total_by_category(expenses_in_month(expenses, year, month)).items()):"),
    ("M6 R8 month-range check removed", "expenses/report.py",
     "if not 1 <= month <= 12:", "if False:"),
    ("M7 category lines use every month", "expenses/cli.py",
     "total_by_category(expenses_in_month(expenses, year, month))", "total_by_category(expenses)"),
    ("M9 ties broken by name (largest first kept)", "expenses/cli.py",
     "for category, amount in total_by_category(expenses_in_month(expenses, year, month)).items():",
     "for category, amount in sorted(total_by_category(expenses_in_month(expenses, year, month)).items(), key=lambda kv: (-kv[1], kv[0])):"),
    ("M8 isascii guard removed", "expenses/cli.py",
     "text.isascii() and ", ""),
]

for name, file, old, new in MUTANTS:
    p = Path(file)
    raw = p.read_bytes(); src = raw.decode("utf-8")
    assert src.count(old) == 1, name
    p.write_bytes(src.replace(old, new).encode("utf-8"))
    r = subprocess.run([sys.executable, "-m", "unittest"], capture_output=True, text=True)
    p.write_bytes(raw)
    failed = sorted({l.split()[1] for l in r.stderr.splitlines() if l.startswith(("FAIL:", "ERROR:"))})
    verdict = "KILLED  " if r.returncode else "SURVIVED"
    print(f"{verdict} {name}")
    for t in failed:
        print(f"           caught by {t}")
