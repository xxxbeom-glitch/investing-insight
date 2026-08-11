# REMEDIATION HANDOFF — External Review NO-GO c374ef0

- status: remediation complete (await re-review)
- baseline_review: `EXTERNAL_REVIEW_POST_MVP_c374ef0.md`
- branch: `post-mvp/phase-1`
- production cron: **DISABLED**
- Long-Term Optional: **NOT STARTED**
- MVP tags: unchanged (`mvp-v0.1-pass` @ e98ff33, `mvp-v0.1-review-pass` @ c1a6692)

## Blocking findings closed

| ID | Fix | Evidence |
|----|-----|----------|
| ER-P0-01 | Snapshot seal + no post-hash `snapshot_items`; context on `multi_agent_runs.context_hash` | migration `0016`; late-insert blocked; M03 mock/live |
| ER-P1-01 | CPI via FRED `units=pc1` / `value_unit=yoy_pct` (`fred-series-v0.2`) | `m02_topdown.json`; DB inflation ~3.46 yoy_pct |
| ER-P1-02 | Evidence bundle + deterministic QA + role prompts + live 8-role | `m03_multi_agent_live.json` judgment `2fefdc00-…` |
| ER-P1-03 | Final Selector → immutable `judgments` + `multi_agent_run_id` | judgment row + M04 eval on that id |
| ER-P1-04 | `thesis_correctness=UNASSESSED`; prices capped `<= as_of`; sector re-scoped | `performance-rules-v0.2`; `m04_performance.json` |
| ER-P1-05 | replay/holdout PASS artifacts required; notes-only rejected | `m06_governance.json` |

## Re-verify order (P0/P1=0 each step)

1. M02 — PASS
2. M03 — PASS (mock + live)
3. M04 — PASS (lineage + UNASSESSED)
4. M05 — PASS (error linked to multi-agent judgment)
5. M06 — PASS (attach-evals → approve → freeze)

## P2 (non-blocking, unchanged policy)

- ER-P2-01 hosted deploy re-scope still documented
- Sector benchmark deferred until sector tag exists
- Lab prices may leave horizons INCOMPLETE (no fabricated returns)

## Stop

Do not enable production cron. Do not start Long-Term Optional. Request external re-review on clean commit bundle.
