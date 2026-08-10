# Production Readiness Review (Gate 0)

Spec: `investing-insight-spec-v1.6/08_POST_MVP_ROADMAP.md` Gate 0  
Baseline: `mvp-v0.1-review-pass` @ `c1a6692`  
Date: 2026-08-11

## Summary

| Topic | Status | Notes |
|-------|--------|-------|
| Supabase backup/restore | READY(Free dump) | Free: no PITR. AC-5 = logical dump→verify→restore-drill. See RUNBOOK_BACKUP_RESTORE.md |
| Secret rotation | READY(doc) | `.env.local` + server-only keys; rotation steps documented. No secret in git/UI. |
| Provider quotas/cost | READY(doc) | Massive rate limit, SEC ≤10 r/s, OpenAI Responses cost tracked via llm_executions. |
| Scheduler failure handling | GAP→M1 | MVP is manual ingest; no cloud scheduler yet. Design constraints captured for M1. |
| Retry/dead-letter/quarantine | READY(code) | `data_quarantine`, Data QA fail-closed, LLM fail-closed (no silent fallback). |
| Monitoring/alerting | PARTIAL | Local `/health*` + Audit UI; no external alerting yet → M1. |
| Deploy access control | GAP→M1 | Local PC only today; hosted access policy deferred to M1. |
| Operational runbook | READY(doc) | See `docs/ops/RUNBOOK_*.md` |

**Milestone 1 GO/NO-GO:** **GO with prerequisites** — may start M1 design/implementation of hosted deploy + schedulers **only after** Supabase backup/PITR confirmation is recorded in M1 PLAN evidence. Gate 0 itself is PASS as a review gate.

## Topic detail

### 1. Supabase backup/restore — READY(Free dump)
- System of record: Supabase PostgreSQL (`SUPABASE_DB_URL` pooler).
- Free plan: Automatic Backup/PITR unavailable — do not fake CONFIRMED.
- Readiness: `scripts/backup_free_plan.py readiness` + evidence under M01 audit.
- See `RUNBOOK_BACKUP_RESTORE.md`.
- Production schedulers remain disabled until an explicit later ops decision (not unlocked by dump PASS alone).
### 2. Secret rotation — READY(doc)
- Secrets: `OPENAI_API_KEY`, `MASSIVE_API_KEY`, `SUPABASE_SECRET_KEY`, `SUPABASE_DB_URL`, `SEC_USER_AGENT`.
- Never commit; never `NEXT_PUBLIC_*` for secret keys.
- Rotation: replace in `.env.local` / secret store → restart API → run `scripts/production_readiness_check.py` + `/health/config`.

### 3. Provider quotas/cost — READY(doc)
- Massive: client throttle + 429 retry (`MassiveClient`).
- SEC: rate limiter ≤10 req/s.
- OpenAI: profile versions in `config/llm_profiles.v0.1.yaml`; executions stored with model/effort/hashes.

### 4. Scheduler failure handling — GAP→M1
- MVP: manual scripts only.
- M1 must define: job identity, idempotent ingest, alert on failure, no silent skip.

### 5. Retry / dead-letter / quarantine — READY(code)
- Quarantine table + Data QA runner fail-closed.
- Snapshot/quant/research refuse future leakage / unsupported claims.

### 6. Monitoring/alerting — PARTIAL
- `/health`, `/health/db`, `/health/config`, PC Audit UI.
- External pager/Slack: not in Gate 0; required in M1 health dashboard work.

### 7. Deploy access control — GAP→M1
- Local bind 127.0.0.1 for API.
- Hosted auth/ACL: M1.

### 8. Operational runbook — READY(doc)
- Linked runbooks under `docs/ops/`.
