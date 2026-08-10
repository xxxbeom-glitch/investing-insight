# IMPLEMENTATION — M01 Automation & Deployment

- milestone_id: M01
- status: IMPLEMENT (AC-5 PITR operator gate open)
- branch: post-mvp/phase-1

## Built
1. Deploy: `deploy/Dockerfile.api`, `deploy/docker-compose.yml`, `docs/ops/RUNBOOK_DEPLOY.md`, `deploy/cron.examples.txt` (commented)
2. Job ledger: `migrations/0010_ops_jobs.sql`, `apps/api/app/ops/jobs.py`
3. Daily ingest CLI: `scripts/run_daily_ingest.py` (market+SEC, dry-run, fail-closed)
4. Biweekly research CLI: `scripts/run_biweekly_research.py` (dry-run + live path)
5. Backup gate: `scripts/backup_supabase_check.py` + evidence template
6. Ops health: `GET /v1/ops/health`, Web `/ops`

## Not yet (blocked)
- Production cron enable — requires `Status: CONFIRMED` in PITR evidence
- Live hosted URL cutover — operator deploys using runbook

## MVP baseline
- Tags untouched; L00–L10 audit PASS docs not edited
