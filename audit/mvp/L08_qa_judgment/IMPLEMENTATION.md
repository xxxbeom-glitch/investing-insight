# IMPLEMENTATION

- layer_id: L08
- status: PASS
- completed_at: 2026-08-10T21:10:20+09:00
- commit_hash: 765c5f0
- previous_layer_commit: fcedd02
- spec_version: investing-insight-spec-v1.6

## What Changed

- `claim_check.py` deterministic numeric grounding
- `qa.py` / `judgment.py` + policy enforcement
- prompts `research_qa.v0.1.txt`, `final_judgment.v0.1.txt`
- migration `0009_qa_judgment.sql` (immutable judgment trigger)

## LLM Execution Contract (recorded by code)

| Role | Model | Effort | Prompt version | Schema version |
|------|-------|--------|----------------|----------------|
| research_qa | gpt-5.6-terra | high | research-qa-prompt-v0.1 | research-qa-output-v0.1 |
| final_judgment | gpt-5.6-terra | high | final-judgment-prompt-v0.1 | final-judgment-output-v0.1 |

Shared: `llm_profile_version=llm-profile-v0.1`; silent fallback forbidden.

## Files Changed (from `git show --stat 765c5f0`)

- `apps/api/app/research/{__init__,claim_check,qa,judgment}.py`
- `config/prompts/research_qa.v0.1.txt`, `final_judgment.v0.1.txt`
- `migrations/0009_qa_judgment.sql`
- `tests/unit/test_claim_check.py`, `tests/integration/test_qa_judgment.py`
- audit + TASK_CONTRACT + active-track
- Totals: 18 files, +727 / −8

## Commands Run

```text
# historical
# claim_check + qa_judgment tests — 3 passed
pytest tests -q   # 44 passed
```

## Deviations from PLAN

- none recorded
