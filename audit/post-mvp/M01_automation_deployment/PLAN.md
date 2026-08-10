# PLAN — Post-MVP Milestone 1 Automation & Deployment

- milestone_id: M01
- spec: investing-insight-spec-v1.6 / 08_POST_MVP_ROADMAP.md Milestone 1
- branch: post-mvp/phase-1
- previous: G00 @ 24092ec
- baseline_tags: mvp-v0.1-pass @ e98ff33 · mvp-v0.1-review-pass @ c1a6692
- status: PLAN

## Goal
Gate 0 PASS 이후 상시운영 기반을 만든다. MVP frozen baseline은 수정하지 않는다.

## In (roadmap order)
1. Hosted PC Web deployment packaging + access-control runbook
2. Daily market/SEC ingest scheduler entrypoints + job ledger
3. Biweekly research scheduler entrypoint + job ledger
4. Backup/restore automation script + PITR evidence gate
5. Operational health dashboard (API + PC Web)

## Out
- FRED / Top-down (M2)
- Multi-agent (M3+)
- Broker / timing / portfolio (Long-Term Optional)
- Changing L00–L10 PASS audit documents
- Moving MVP tags

## Blocking Acceptance
| ID | Criterion | How to test |
|----|-----------|-------------|
| AC-1 | Deploy artifacts: API Dockerfile + compose + `RUNBOOK_DEPLOY.md` (reverse-proxy ACL) | file review + `docker build` optional |
| AC-2 | `ops_jobs` migration + job helper; failed jobs persist job_id/stage/error_code/retry_count | migrate + unit |
| AC-3 | `scripts/run_daily_ingest.py` runs market+SEC sample; non-zero exit on failure; no secret in stdout | pytest/integration dry |
| AC-4 | `scripts/run_biweekly_research.py` wraps research path with job ledger; fail-closed | unit + dry flags |
| AC-5 | `scripts/backup_supabase_check.py` + PITR confirmation evidence (hostname/retention only) | script + evidence file |
| AC-6 | Cron/scheduler examples documented; **production enable blocked until AC-5 PASS** | file review |
| AC-7 | `GET /v1/ops/health` + Web `/ops` shows recent jobs / health flags | API + build |
| AC-8 | P0=0 P1=0 | OPEN_ISSUES |
| AC-9 | MVP tags untouched | `git rev-list` |

## Implementation slices
1. Schema + job helpers + daily/biweekly CLIs
2. Deploy packaging + backup check + cron examples
3. Ops health API/UI
4. PITR evidence (operator) → enable note
5. TEST/QA → PASS

## Risks
- Full-universe daily ingest cost/time → default `--limit` sample; universe mode explicit
- Enabling cloud schedulers before PITR → forbidden by AC-6
- Scope creep into M2 → refuse

## Tests first
- `tests/unit/test_ops_jobs.py`
- extend readiness / secret scan still PASS
