# HANDOFF

- layer_id: L08
- layer_name: qa_judgment
- status: PASS
- completed_at: 2026-08-10T21:10:20+09:00
- commit_hash: 765c5f0
- previous_layer_commit: fcedd02
- handoff_hash_commit: cb6762a
- spec_version: investing-insight-spec-v1.6

## Acceptance Criteria Result

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 | PASS | claim_check |
| AC-2 | PASS | QA FAIL blocks SELECTED |
| AC-3 | PASS | unsupported new fact FAIL |
| AC-4 | PASS | role profile recorded |
| AC-5 | PASS | no silent fallback |
| AC-6 | PASS | no selection minimum |
| AC-7 | PASS | immutable judgment trigger |
| AC-8 | PASS | SELECTED bear/risk/invalidation |

## Issue Counts

- P0: 0
- P1: 0
- P2: 0
- P3: 0

## Config / Schema / LLM Versions

- llm_profile: llm-profile-v0.1
- research_qa: gpt-5.6-terra / high / research-qa-prompt-v0.1 / research-qa-output-v0.1
- final_judgment: gpt-5.6-terra / high / final-judgment-prompt-v0.1 / final-judgment-output-v0.1
- migration: 0009_qa_judgment.sql

## Commands to Reproduce

```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe -m pytest tests/unit/test_claim_check.py tests/integration/test_qa_judgment.py -q
```

## Next Layer Eligibility

- eligible: **yes**
- next: L09 PC Web Vertical Slice
