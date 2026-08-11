# OPEN_ISSUES

## Blocking for AC-6 (not fixed here — STOP)

- L08 still treats English calendar fragments as financial quantities: `June 27, 2026` → `27` + `2026`; `July 9, 2026` → `9` + `2026`.
- Live AAPL `bac5e73f` Research QA FAIL / REJECT for this reason.
- Next (separate): recognize month-name dates as non-quantities, fail-closed, with regression. Do not loosen numeric matching.

## Not this task

- GO / tag / cron / PITR / hosted / Optional
- Dual-path merge of claim_support + claim_check
- M03 `Assets were …` value_value_copula (metric_key display vs field `value`)
