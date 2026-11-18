"""Edge-case and fault-injection probe for remove_last_expense / undo.

Usage: python docs/week7/probe.py <repo root to test>
Each case builds its own temp file; nothing in data/ is touched.
"""
import io
import sys
import tempfile
import time
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

sys.path.insert(0, sys.argv[1])
from expenses.cli import main  # noqa: E402
from expenses.storage import load_expenses, remove_last_expense  # noqa: E402

HEADER = b"date,category,amount,note\r\n"
ROWS = HEADER + b"2026-09-02,food,12.50,lunch\r\n2026-09-03,transport,3.20,bus\r\n"


def case(name, content, check):
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "e.csv"
        path.write_bytes(content)
        try:
            removed = remove_last_expense(path)
            result = check(removed, path.read_bytes())
        except Exception as exc:  # report, don't hide: this is a probe
            result = f"raised {type(exc).__name__}: {exc}; file intact: {path.read_bytes() == content}"
        print(f"{name:<46} {result}")


def same(expected):
    return lambda removed, after: "ok" if after == expected else f"UNEXPECTED file: {after!r}"


print(f"--- probing {sys.argv[1]}")
case("CRLF file (what `add` writes)", ROWS, same(HEADER + b"2026-09-02,food,12.50,lunch\r\n"))
case("trailing blank lines", ROWS + b"\r\n\r\n", same(HEADER + b"2026-09-02,food,12.50,lunch\r\n"))
case("header + blank lines only", HEADER + b"\r\n\r\n", lambda r, a: "ok (None)" if r is None else f"removed {r}")
case("non-UTF-8 byte in a note", ROWS + b"2026-09-04,food,1.00,caf\xe9\r\n", lambda r, a: f"removed {r}")
case("unparseable last row", ROWS + b"not-a-date,food,1,x\r\n", lambda r, a: f"removed {r}")

# Fault injection: the disk fills up (or the user hits Ctrl-C) while the file is
# being rewritten. Simulated by letting open(..., "w") truncate the real file and
# then failing on the first write, which is what a full disk looks like.
real_open = Path.open


def failing_open(self, mode="r", *args, **kwargs):
    f = real_open(self, mode, *args, **kwargs)
    if "w" in mode:
        def boom(*a, **k):
            raise OSError(28, "No space left on device")
        f.write = boom
    return f


for label, exc in [("write fails mid-undo (disk full)", None)]:
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "e.csv"
        path.write_bytes(ROWS)
        out = io.StringIO()
        try:
            with mock.patch.object(Path, "open", failing_open), redirect_stdout(out):
                main(["--file", str(path), "undo"])
            outcome = "no error"
        except OSError as e:
            outcome = f"OSError: {e.strerror}"
        survivors = load_expenses(path) if path.exists() else None
        leftovers = sorted(p.name for p in Path(tmp).iterdir())
        print(f"{label:<46} {outcome}; expenses left in ledger: {len(survivors)} of 2; files: {leftovers}")

# Size: undo on a 100 000-row ledger.
with tempfile.TemporaryDirectory() as tmp:
    path = Path(tmp) / "e.csv"
    path.write_bytes(HEADER + b"2026-09-02,food,12.50,lunch\r\n" * 100_000)
    t = time.perf_counter()
    remove_last_expense(path)
    print(f"{'100 000-row ledger':<46} {time.perf_counter() - t:.2f} s, rows left {len(load_expenses(path))}")
