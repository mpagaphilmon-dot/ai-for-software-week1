# Week 7 checkpoint: reviewing an agent-produced change and preparing it for release

Philmon · 18 November 2026

**Source code and evidence:** <https://github.com/mpagaphilmon-dot/ai-for-software-week1>. Every `docs/week7/...` path below is in that repository: <https://github.com/mpagaphilmon-dot/ai-for-software-week1/tree/main/docs/week7>.

This submission covers both Week 7 briefs:

- **Part A, activities & checkpoint:** a structured review of an agent-produced change, with findings, a proposed fix, verification, an AI-vs-non-AI timing note and an AI-use declaration.
- **Part B, checkpoint submission:** preparing the same change for release, with a summary, release-readiness checklist, risk register, verification evidence and a release note.

## 0. Setup

**The change.** No peer PR was available, so I used my own agent-produced change. A fresh `claude -p` session (Claude Code 2.1.326, Claude Opus 5.5) worked in an **isolated copy** of the repository with its own git history. It got a short, ticket-style request (`docs/week7/prompts/1_task.txt`) to add an `undo` command that removes the last expense from the CSV file. I chose `undo` deliberately. It's the first command in this project that **deletes data**, so the review and the release checks have something real to bite on.

The agent could read and edit files and run `python -m unittest`, and nothing else. It finished in 12 turns, 71 s, $0.45, and wrote its own PR description (`outputs/1_task_final.md`).

| Path in `docs/week7/` | Contents |
| --- | --- |
| `prompts/1_task.txt`, `prompts/2_fix.txt` | the feature request and the fix request, exactly as sent |
| `outputs/1_task.diff`, `outputs/1_task_final.md` | **the reviewed PR**: the agent's diff and its PR description |
| `outputs/2_fix.diff`, `outputs/2_fix_final.md` | the fix for finding F1 |
| `outputs/*.jsonl`, `*_toolcalls.txt`, `*_clock.txt` | raw logs, tool calls, wall-clock timestamps |
| `probe.py`, `probe_agent_version.txt`, `probe_fixed_version.txt` | my edge-case and fault-injection probe, run before and after the fix |
| `fix_red_green.txt`, `manual_runs.txt` | red/green run of the regression test; manual CLI runs |
| `copy_git_log.txt`, `final.diff` | history of the isolated copy; the full accepted change |

# Part A: structured review

## A1. The PR reviewed

**"Add `undo` command to remove the most recently added expense"**: 5 files, +123 −2 (`outputs/1_task.diff`).

| File | Change |
| --- | --- |
| `expenses/storage.py` | new `remove_last_expense(path)`: finds where the last CSV record starts (using `csv`, so a quoted multi-line note counts as one record), rewrites the file without it, and returns the removed `Expense`, or `None` if there's nothing to remove |
| `expenses/cli.py` | new `undo` subcommand: prints `Removed 12.50 from food (2026-09-02)` or `Nothing to undo`, exit 0 |
| `README.md` | one usage line |
| `tests/test_storage.py`, `tests/test_cli.py` | 4 storage tests, 3 CLI tests |

The core of the reviewed code:
```python
def remove_last_expense(path):
    path = Path(path)
    expenses = load_expenses(path)
    if not expenses:
        return None
    with path.open(newline="", encoding="utf-8") as f:
        lines = f.readlines()
    ...                                   # csv.reader finds last_start, the first line of the last record
    path.write_text("".join(lines[:last_start]), encoding="utf-8", newline="")
    return expenses[-1]
```

## A2. The checklist I ran

I didn't stop at "tests pass, looks good". Each item has a method and a piece of evidence.

| # | Check | How | Result |
| --- | --- | --- | --- |
| 1 | **Correctness**: does it do what was asked? | read the diff; manual runs on a copy of `data/sample.csv` | ✓ removes the last row, prints it; rest of the file byte-identical (`manual_runs.txt`) |
| 2 | **Boundary cases**: empty, header-only, missing file, trailing blank lines, no final newline, multi-line note, CRLF and LF files, last row removed until empty | agent tests + `probe.py` + manual runs | ✓ all handled; missing file not created |
| 3 | **Failure behaviour**: what happens to the data when something goes wrong? | `probe.py`: bad UTF-8, unparseable row, **write failing mid-rewrite** | ✗ **F1**: a failed write destroys the whole ledger. Bad input raises before any write (file intact) ✓ |
| 4 | **Dependencies / APIs** | grep new imports; check API behaviour (`Path.write_text` truncates first, `Path.replace` is atomic on one filesystem, `unlink(missing_ok=)` needs 3.8+) | ✓ stdlib only (`csv`, `pathlib`; tests add `unittest.mock`); within CLAUDE.md §7 |
| 5 | **Module rules** (CLAUDE.md §2, §4) | read diff | ✓ `storage.py` doesn't print; `cli.py` does no arithmetic; no `sys.exit` / swallowed errors |
| 6 | **Security** | threat model for a local single-user CLI: path handling, injection, untrusted file content | ✓ no new input surface (no arguments); `--file` already existed. Note F3 (file permissions) |
| 7 | **Secrets** | grep `final.diff` for password/token/key/URL patterns | ✓ none |
| 8 | **Tests**: do they test real behaviour? | read each test; asked "would it fail if the code were wrong?" | ✓ byte-level file checks, exact messages; multi-line test would catch "drop the last *line*". ✗ nothing tests a failed write (gap behind F1) |
| 9 | **Licence / IP** | look for copied code, unusual idioms, licence headers; check the log for web access | ✓ the agent had no web tools (`toolcalls.txt`); code is generic stdlib usage, no headers or attributable snippets |
| 10 | **Scope**: only what was asked? | `--stat`, diff read | ✓ 5 files, no unrelated edits |
| 11 | **Agent honesty**: do the PR description and log match? | compared `*_final.md` with `*_toolcalls.txt` and the raw log | ✓ claims match (48 tests OK); see A3 note on the fix run |
| 12 | **Performance** | 100 000-row ledger in `probe.py` | ✓ 1.6–2.1 s; reads the file twice, acceptable for a personal ledger |

## A3. Findings

**F1 (high, substantive): a failed rewrite deletes the entire ledger.** `path.write_text(...)` opens the file in `"w"` mode, which **truncates it to zero bytes before writing anything**. If the write then fails, for example because the disk is full, the user presses Ctrl-C, or antivirus or a sync client (OneDrive, Dropbox) locks the file partway through, the user loses **every expense**, not just the one they meant to undo.

*Evidence* (`probe_agent_version.txt`): with `open(..., "w")` failing on its first write, `undo` on a 2-row ledger left **0 of 2** rows.
```
write fails mid-undo (disk full)   OSError: No space left on device; expenses left in ledger: 0 of 2
```
*Why it matters more than it looks:* `add` only appends, so its worst failure is one damaged last row. `undo` is the first operation that rewrites the whole file, which turns a local failure into total data loss. The file is usually the user's **only copy**. None of the agent's 7 tests could catch this, because none of them makes I/O fail.

**F2 (low): fixed temporary file name.** *(introduced by the fix)* The fix writes to `<ledger>.tmp`. If the user happens to have a file with exactly that name, it's overwritten and then deleted. This is unlikely and isn't fixed. It's recorded in the risk register.

**F3 (low, not verified here): file permissions aren't carried over.** *(introduced by the fix)* On Linux and macOS, the replacement file gets the default permissions, so a ledger the user had restricted to `chmod 600` could become readable by other local users after an `undo`. I reasoned this from how `os.replace` works but couldn't test it on this Windows machine. It's recorded as a privacy risk.

**F4 (design note, accepted): "most recently added" means "last row".** If the user hand-edits or sorts the file, `undo` removes whatever is last, not what they added last. The message prints the removed expense, so the user can see what happened. **But the message leaves out the note**, so a mistaken `undo` can't be fully reconstructed from the output. This is recorded as a follow-up.

**Review note on the fix run (not a defect).** The fix agent tried a compound command, `python -m unittest ...; git stash push ...; ...`, to check that its new test fails on the old code. The allowlist only permitted `python -m unittest`, and the command was **denied** (`permission_denials` in `outputs/2_fix.jsonl`). The agent then reported truthfully: "I didn't run the new test against the old code." So I ran that red check myself (A5). Two things were confirmed: the permission boundary held, and the agent's final message matched what it had actually done.

## A4. Proposed fix (stretch) and why it doesn't widen scope

I wrote F1 up as a finding with the reproduction and constraints (`prompts/2_fix.txt`), and a fresh agent session applied it (9 turns, 44 s, $0.27, `outputs/2_fix.diff`):

```diff
-    path.write_text("".join(lines[:last_start]), encoding="utf-8", newline="")
+    # Write to a sibling file and swap it in, so a failed write can't
+    # truncate the ledger; replace() is atomic on the same filesystem.
+    tmp = path.with_name(path.name + ".tmp")
+    try:
+        tmp.write_text("".join(lines[:last_start]), encoding="utf-8", newline="")
+        tmp.replace(path)
+    finally:
+        tmp.unlink(missing_ok=True)
```
plus one regression test, `test_remove_last_failed_write_keeps_file`, which makes `write_text` truncate and raise, then checks that the ledger is byte-for-byte unchanged and no `.tmp` file is left behind.

**Why it fixes F1:** the ledger is never opened for writing. Until `replace` runs, the original is untouched, and `replace` is a single rename, so the old file is swapped for the new one completely or not at all. If the write fails, the original stays and the temp file is cleaned up.

**Why it doesn't widen scope:**
- one function changes, and only its last line;
- the bytes written, the return value, the CLI output and every other function stay the same;
- no new module (`pathlib` only, as CLAUDE.md §7 requires; `os`, `tempfile` and `shutil` are deliberately not used);
- `try/finally` re-raises the error rather than swallowing it (CLAUDE.md §4);
- F2, F3 and F4 are deliberately **not** fixed here. Each would need a design decision (unique temp names need `tempfile`; copying permissions; changing the message format).

## A5. Tests and verification I ran

| Check | Result | Evidence |
| --- | --- | --- |
| Agent's suite in the isolated copy | 48 tests OK | `outputs/1_task_final.md`, re-run by me |
| **Red:** the new regression test against the agent's original `storage.py` | **fails**: `AssertionError: b'' != b'date,category,...'` | `fix_red_green.txt` |
| **Green:** full suite with the fix | 49 tests OK | `fix_red_green.txt` |
| My probe, using a **different fault mechanism** (`Path.open` patched, not `write_text`) | before: 0 of 2 rows left → after: **2 of 2**, no temp file left | `probe_*_version.txt` |
| Probe edge cases (CRLF, blank lines, header-only, bad UTF-8, bad row) | identical before and after the fix; bad input raises **before** writing, file intact | same |
| Full suite in the real repo after applying `final.diff` | **49 tests OK** (41 before this week + 8) | run in repo root |
| Manual CLI runs on a temp copy of `data/sample.csv` | see below | `manual_runs.txt` |

Manual runs (`manual_runs.txt`):
- `undo` → `Removed 9.75 from food (2026-10-04)`, exit 0, and the file equals the original minus its last line, **LF endings kept**;
- `add food 4.20 --note "coffee, large"` then `undo` → the quoted note round-trips and is removed cleanly;
- 6 × `undo` → all 6 rows removed, then `Nothing to undo` (exit 0), header kept;
- `undo` on a missing file → `Nothing to undo`, file **not** created;
- `undo 3` → rejected, exit 2;
- no `.tmp` left in the folder, and `git status data/` empty (real data untouched).

## A6. Timing note: AI vs non-AI

Both tasks are the same size: a change of about 8 lines to one function, plus one test.

**Task 1 (with AI): fix F1 + regression test.** Timed from the clock logs (`outputs/2_fix_clock.txt`).

| Phase | Time |
| --- | --- |
| Prompting: writing `2_fix.txt` from the finding | 0:17 |
| Agent run (wall clock) | 0:49 |
| Review: reading the diff, red/green, re-running the probe | 0:21 |
| Debugging | 0 |
| Rework | 0 (accepted as is) |
| **Total** | **≈ 1:27**, plus $0.27 |

For comparison, the same clock log for the **`undo` feature itself** (`outputs/1_task_clock.txt`, `1_task_toolcalls.txt`):

| Phase | Time |
| --- | --- |
| Agent run (wall clock) | 1:20 (agent reported 1:11, 12 turns) |
| First review pass: reading the diff and the tests | 0:49 |
| Probe + fault injection that found F1 | ≈ 1 min (between the review start and the fix prompt) |
| Rework | the F1 fix above (1:27) |
| **Total, feature + review + fix** | **≈ 4:40**, $0.72 in agent cost |

*Caveat:* these are wall-clock times from the log files. The prompting and checking were done by my assistant (Claude Code, interactive), so they're machine speed, not human reading speed.

**Task 2 (without AI): `undo --dry-run`, done by hand.** It prints `Would remove 12.50 from food (2026-09-02)`, leaves the file untouched and has one CLI test. It's the same size as Task 1.

| Phase | Time |
| --- | --- |
| **Total (planning, coding, debugging, rework)** | **2:00**, timed by me as one block; the phases weren't timed separately |

**Takeaway:** for a change this small, the two approaches took about the same time: 1:27 with AI against 2:00 by hand. AI saves little when the change is a few lines. Writing the code was the cheapest phase either way. What took the effort was the review: F1 was found only by deliberately making the write fail, which none of the agent's own tests did. Next time I'll time the phases separately, so I can see where the minutes go.

## A7. AI-use declaration

- **Agent under review:** Claude Code 2.1.326 (Claude Opus 5.5), run non-interactively (`claude -p`) in an isolated copy, for two steps: the `undo` feature and the F1 fix. Prompts, logs and diffs are included unchanged.
- **Assistant:** I used Claude Code interactively as my assistant to write the prompts, run the agent, write `probe.py`, run the checklist and verification, and draft this write-up.
- **Done without AI:** the timing comparison task (A6, Task 2, `undo --dry-run`), done by hand in a throwaway copy and not shipped.
- **Human decisions:** choosing a data-deleting change to review; treating F1 as release-blocking; the fix constraint (pathlib only, no behaviour change); leaving F2–F4 as recorded risks instead of widening the fix; the release approval in Part B.

# Part B: release readiness

## B1. Summary of the change

Adds `python -m expenses undo`, which removes the last expense in the ledger and prints what it removed (`Removed 12.50 from food (2026-09-02)`), or `Nothing to undo`. The rewrite is all-or-nothing: the new contents go to a temporary file that atomically replaces the ledger, so a failure leaves the original intact. Standard library only. 7 + 1 new tests, README usage line. Full diff: `docs/week7/final.diff` (+152 lines across 5 files).

## B2. Release-readiness checklist

| Area | Item | Status |
| --- | --- | --- |
| **Tests** | full suite green on Python 3.10 (49 tests) | ✓ |
| | regression test for F1 shown red before the fix, green after | ✓ |
| | edge cases probed beyond the suite (`probe.py`) | ✓ |
| | tested on Linux/macOS | ✗ **not done**: Windows only; F3 unverified |
| **Review** | structured checklist (A2), findings recorded (A3) | ✓ |
| | blocking finding F1 fixed and re-verified | ✓ |
| | human sign-off on the final diff | ☐ **required, see B6** |
| **Security / privacy** | no new arguments or input surface; no network; no secrets in diff | ✓ |
| | no telemetry added (expense data stays local) | ✓ |
| | file permissions after `undo` on POSIX (F3) | ⚠ residual risk, documented |
| **Data handling** | only the last record is removed; other bytes identical (LF/CRLF kept) | ✓ |
| | failed write leaves ledger intact (atomic replace) | ✓ |
| | invalid file content raises **before** any write | ✓ |
| | missing file not created; `data/` untouched by tests | ✓ |
| | removed note not shown, so a mistaken undo can't be fully re-added (F4) | ⚠ documented; follow-up |
| **Dependencies** | no new packages; only `csv`, `pathlib` (+ `unittest.mock` in tests); no `requirements.txt` | ✓ |
| | `Path.unlink(missing_ok=)` needs 3.8+; README promises 3.10+ | ✓ |
| **Rollback** | code: one revert of the change, no schema or file-format change, so old versions read the same CSV | ✓ |
| | data: `undo` itself can't be rolled back by reverting code; recovery is re-`add` from the printed line + note from backup | ⚠ in release note |
| **Monitoring** | no telemetry by design; signals are user reports and a stray `*.csv.tmp` file (a sign of an interrupted undo) | ✓ defined |

## B3. Risk register

| # | Risk | Likelihood | Impact | Mitigation | Residual / owner |
| --- | --- | --- | --- | --- | --- |
| R1 | **Ledger lost when a rewrite fails** (disk full, Ctrl-C, file lock) | low | **high**: all data | atomic temp-file + `replace` (F1 fix); regression test; probe with a second fault mechanism | low; re-check if storage ever moves off the local filesystem |
| R2 | **User undoes the wrong expense** (double run, or file was hand-sorted) | medium | medium: one row lost, note unrecoverable | message prints date, category and amount; "last row" documented in release note | **open**: follow-up to print the note, or add `--dry-run` |
| R3 | **Permissions loosened on POSIX** (`chmod 600` ledger becomes world-readable) | low | medium: privacy of spending data | documented; Windows unaffected | **open, unverified**: test on Linux before claiming POSIX support |
| R4 | **Collision with an existing `<ledger>.tmp`** | very low | low: that file is overwritten and deleted | documented | accepted |
| R5 | **Sync clients or antivirus lock the file** during `replace` (Windows) | low | low: `undo` fails with `PermissionError`, ledger intact | atomic replace means failure is safe; error is not swallowed | accepted; user re-runs |
| R6 | **Tests pass for the wrong reason** | low | medium | red/green check, byte-level asserts, independent probe | low |

## B4. Evidence of verification

Summarised in A5. The files are `fix_red_green.txt`, `probe_agent_version.txt` → `probe_fixed_version.txt` (0 of 2 → 2 of 2 rows after a failed write), `manual_runs.txt`, and the 49-test green run in the real repository.

## B5. Release note / team handoff

> **expenses: new `undo` command**
>
> `python -m expenses undo` removes the **last row** of the ledger and prints it, e.g. `Removed 12.50 from food (2026-09-02)`. On an empty or missing ledger it prints `Nothing to undo` and changes nothing.
>
> - **Safe on failure:** the ledger is rewritten through a temp file and an atomic replace, so a crash or full disk leaves it unchanged. If you see a stray `expenses.csv.tmp`, an undo was interrupted; the ledger itself is fine and the temp file can be deleted.
> - **Know before you use it:** it removes the *last row*, not necessarily what you typed last if you hand-edit the file. The output doesn't show the note, so keep your own backup if notes matter. There is no redo: to restore, `add` the printed values again with `--date`.
> - **Rollback:** revert the commit. The file format is unchanged, so older versions read the same CSV.
> - **Not yet verified:** behaviour on Linux/macOS (file permissions after undo, R3).
> - **Tests:** 49 green on Python 3.10 (+8 new). Review notes and evidence: `docs/week7-checkpoint.md`.

## B6. What a human must still approve before shipping

The AI wrote the code and ran the checks, but some decisions can't be handed to it, because they're about responsibility rather than correctness. Before this goes out, a person has to say "yes" to each of these:

| # | Decision | Why the AI can't make it | What "yes" means |
| --- | --- | --- | --- |
| 1 | **The code itself** | Tests only show what they test; F1 got past 7 passing tests | I read `docs/week7/final.diff` myself and agree it does only what the release note says |
| 2 | **The leftover risks** (R2 wrong row undone, R3 permissions on Linux/macOS) | Whether a risk is acceptable is a judgement, not a fact | I accept them for this release: ship on Windows now, and test R3 on Linux before claiming Linux/macOS support |
| 3 | **What users are told** | The release note is a promise to users | I agree with the wording that `undo` removes the *last row* and that there is no redo |
| 4 | **Actually shipping** (commit and push) | The assistant was told not to commit | I make the commit and push it myself |

Until all four have a "yes", the change is *ready* but not *released*.

## What I learned

- **The bug that mattered wasn't visible in the diff's logic.** Every line of `remove_last_expense` was correct. The defect was in what `write_text` does *before* it writes. I only saw it by asking "what happens to the data if this fails?" and then forcing it to fail.
- **Green tests had nothing to say about failure.** The agent's 7 tests were good tests of the happy path and the edge cases. None of them could have caught F1, because none made I/O fail.
- **A fix should be checked by a different method than the one that wrote it.** The agent's regression test patches `write_text`; my probe patches `open`. The fix passing both makes it much less likely to be tuned to its own test.
- **Reading the raw log is part of review.** The agent's summary said it skipped the red check. The log showed *why*: its sandbox denied the command. Both the honesty and the permission boundary were worth confirming, not assuming.
- **Shipping is more than merging.** Writing the rollback row showed that reverting code can't undo a user's `undo`, and that fact belongs in the release note, not just in the code.
