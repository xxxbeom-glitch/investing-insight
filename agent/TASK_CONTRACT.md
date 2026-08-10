# Active Task Contract

## Task
- Task ID: M01
- Layer: Post-MVP Milestone 1 — Automation & Deployment

## Goal
M01 AC 구현 완료 후 PITR 확인으로 P1을 닫고 PASS한다. PASS 전 M2 착수 금지.

## Blocker
- [ ] `evidence/supabase_pitr_confirmation.md` → `Status: CONFIRMED`
- [ ] `scripts/backup_supabase_check.py` exit 0
- [ ] OPEN_ISSUES P0=0 P1=0
- [ ] QA_REPORT PASS

## Out of scope
- FRED / M2+
- MVP frozen baseline 수정
- Production cron enable before PITR CONFIRMED
