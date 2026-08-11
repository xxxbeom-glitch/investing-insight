# HANDOFF — L08 numeric unit scale

- status: **STOP** (unit contract landed; live QA not PASS)
- commit: `6112966`
- checkpoint: `e5e6762`
- live run_id: `bac5e73f-6dbe-4b50-8e6b-2671fd663e36`
- Research QA: FAIL
- judgment: REJECT
- GO/tag/cron/Optional: unchanged

## What landed

Shared `apps/api/app/research/numeric_scale.py`. L08 bag and M03 value spans use the same magnitude contract. Billion/raw regression PASS. Grounding FP=0.

## Why live still FAIL

Prose dates (`June 27, 2026`), not billion scale. See `live_result.json` / OPEN_ISSUES.

## Do not

tag / GO / cron / gate relaxation / prompt-hide claims / continue widening this task
