# HANDOFF — M01 (blocked on PITR)

- status: IN_PROGRESS (P1 open)
- do_not_start: Milestone 2 until M01 PASS

## Waiting on
Operator confirmation in:
`audit/post-mvp/M01_automation_deployment/evidence/supabase_pitr_confirmation.md`

Set first status line to `Status: CONFIRMED` after verifying Supabase backups/PITR (hostname/retention only).

## After confirmation
1. `python scripts/backup_supabase_check.py` → exit 0
2. Close M01-P1-01
3. Complete QA PASS + commit
4. Optionally set `OPS_PITR_CONFIRMED=true` in hosted env
5. Enable cron from `deploy/cron.examples.txt`
