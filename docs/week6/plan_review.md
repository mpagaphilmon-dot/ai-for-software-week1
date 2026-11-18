# My review of the agent's plan (outputs/2_plan_final.md)

Verdict: **approved with 4 amendments.** No code written yet.

| # | Plan item | Decision | Why |
| --- | --- | --- | --- |
| 1 | `expenses_in_month` in `report.py`, matching on `e.day.year`/`e.day.month` | accept | Pure, no boundary maths, no `calendar`. Matches the spec constraint. |
| 2 | Extra `ValueError` for month outside 1-12 (not in spec) | **accept, and add to spec as R8** | CLAUDE.md section 4: never return an empty result to hide bad arguments. The agent flagged the addition itself instead of slipping it in. |
| 3 | Shape check in `year_month` (`len == 7`, `-` at index 4, ASCII digits) on top of `fromisoformat` | accept | Spec says "exactly YYYY-MM"; README promises 3.10+. On 3.10 I checked `202609`, `2026-W01`, `2026-9`, full-width digits: all already rejected. I could **not** check 3.11+ (no working interpreter here), so the guard is insurance, not a proven fix. |
| 4 | `date.today()` called once | accept | Avoids the midnight mixed-date bug. |
| 5 | Report tests (5) and CLI tests (7) | accept with amendments A-C | They map to R1-R7. |
| 6 | README usage line | accept | CLAUDE.md section 8. |

**Amendments**
- **A.** Rejection subtests must also include `202609` and the empty string `""`, so the shape check is actually exercised.
- **B.** At least one rejection test asserts the **full** message `invalid month: '2026-13', expected YYYY-MM`, not just `invalid month`. A substring test would also pass for an unrelated message such as "invalid month range".
- **C.** The October CLI test must check the **order** of lines (food before transport), not just their presence.
- **D.** Name the subparser variable `month_cmd`, not `month`, in `build_parser` so it isn't confused with the argument of the same name in `main`.

Not adopted: nothing. Rejected: nothing. Risks the plan named that I accept as-is: two filters for one month (risk 2, guarded by acceptance tests), midnight flake in the "today" test (risk 5).
