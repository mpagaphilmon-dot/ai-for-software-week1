I added `average(expenses)` to `expenses/report.py`. It returns the mean expense amount rounded to cents, the same way `total` rounds. With no expenses it returns `0` rather than failing with a divide-by-zero error, which matches how `total([])` behaves.

I also added two tests to `tests/test_report.py`: one checks that the three sample expenses average to 8.48, and one checks the empty case. All 9 tests pass.

I didn't connect it to the CLI (`cli.py`), so it's only available in code for now. I can add it as a CLI command if you want.
