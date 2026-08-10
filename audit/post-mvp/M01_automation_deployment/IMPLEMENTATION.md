# IMPLEMENTATION — M01 Automation & Deployment

- milestone_id: M01
- status: IMPLEMENT (AC-5 PITR operator gate open)
- branch: post-mvp/phase-1

## Built
1. Deploy: `deploy/Dockerfile.api`, `deploy/docker-compose.yml`, `docs/ops/RUNBOOK_DEPLOY.md`, `deploy/cron.examples.txt` (commented)
2. Job ledger: `migrations/0010_ops_jobs.sql`, `apps/api/app/ops/jobs.py`
3. Daily ingest CLI: `scripts/run_daily_ingest.py`
4. Biweekly research CLI: `scripts/run_biweekly_research.py`
5. Free-plan backup: `scripts/backup_free_plan.py` + `backup_supabase_check.py`
6. Ops health: `GET /v1/ops/health`, Web `/ops` (`backup_ready`, schedulers blocked)

## Explicit
- PITR not available on Free — evidence says `PITR_UNAVAILABLE` (not fake CONFIRMED)
- Production schedulers remain disabled

## MVP baseline
- Tags untouched; L00–L10 audit PASS docs not edited
