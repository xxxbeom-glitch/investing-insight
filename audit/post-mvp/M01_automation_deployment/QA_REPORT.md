# QA_REPORT — M01 (not PASS yet)

- status: **IN_PROGRESS**
- P0: 0
- P1: 1 (PITR confirmation)

## Acceptance
| ID | Result | Notes |
|----|--------|-------|
| AC-1 | PASS | deploy packaging + RUNBOOK_DEPLOY |
| AC-2 | PASS | ops_jobs + unit |
| AC-3 | PASS | daily dry-run |
| AC-4 | PASS | biweekly dry-run |
| AC-5 | **FAIL** | awaiting operator CONFIRMED |
| AC-6 | PASS (gate held) | cron examples commented; enable blocked |
| AC-7 | PASS | /v1/ops/health + /ops build |
| AC-8 | FAIL | P1 open |
| AC-9 | PASS | tags untouched |

## Next
Operator fills `evidence/supabase_pitr_confirmation.md` → re-run backup check → close P1 → M01 PASS → then enable schedulers.
