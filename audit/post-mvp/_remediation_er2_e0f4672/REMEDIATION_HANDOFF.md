# REMEDIATION HANDOFF — External Re-review NO-GO e0f4672

- status: ER2 remediation complete (await re-review)
- baseline_nogo: `e0f4672` (`e0f4672f88394aa554a2f6d63a460a702a38c3b9`)
- report: `EXTERNAL_REREVIEW_POST_MVP_e0f4672.md`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- Post-MVP tag: **not created**
- MVP tags: unchanged (`mvp-v0.1-pass` @ e98ff33, `mvp-v0.1-review-pass` @ c1a6692)
- review_candidate: branch HEAD after ER2 commit; bundle `git/HEAD_commit.txt` is SoT

## Blocking findings closed

| ID | Fix | Evidence |
|----|-----|----------|
| ER2-P0-01 | DB trigger freeze of `frozen_context`/lineage; read-time `context_hash` verify | `migrations/0017_er2_remediation.sql`; `verify_frozen_context`; `tests/integration/test_er2_frozen_context.py`; `m03_lineage.json` |
| ER2-P1-01 | Quant exact `(run_id, security_id)` from frozen `bottom_up_run_id`; no UUID-desc borrow; Quant bound into frozen hash | `pick_quant_record` / `load_quant_for_frozen_run`; live `quant_n=0` (absent, not borrowed); `m03_live.json` |
| ER2-P1-02 | Deterministic `final_selector` gate before immutable judgment projection | `final_gate.py`; live gates QA/adversarial/final_selector all PASS; judgment `4e012869-…` |
| ER2-P1-03 | Recorded `governance_evaluations` + `output_hash`; hand-authored PASS JSON rejected | `evaluator.py`; `m06_replay.json` / `m06_holdout.json`; `m06.json` frozen proposal |

## Re-verify order (P0/P1=0 each step)

1. M03 — PASS (mock + live 8-role; final_selector gate PASS; judgment projected)
2. M04 — PASS (eval on that judgment; thesis `UNASSESSED`; horizons INCOMPLETE, no fabricated returns)
3. M05 — PASS (error `8eec5e69-…` linked to judgment `4e012869-…`)
4. M06 — PASS (recorded replay/holdout → attach → approve → freeze; notes/JSON-only blocked)

## Regression

- secret_scan PASS
- pytest 84 passed (full suite, ~223s); unit 65 passed
- Next.js `npm run build` PASS
- `scheduler_enable_allowed: false` on all job summaries

## Stop

Do not enable production cron. Do not start Long-Term Optional. Do not create a Post-MVP PASS tag. Request external re-review on the clean commit bundle.
