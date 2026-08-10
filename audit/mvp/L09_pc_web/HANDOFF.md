# HANDOFF

- layer_id: L09
- layer_name: pc_web
- status: PASS
- completed_at: 2026-08-10T21:18:49+09:00
- commit_hash: eb2002c
- previous_layer_commit: cb6762a
- handoff_hash_commit: 3dfda44
- spec_version: investing-insight-spec-v1.6

## Acceptance Criteria Result

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 | PASS | evidence navigation pages/API |
| AC-2 | PASS | runs list/detail |
| AC-3 | PASS | QA FAIL visibility |
| AC-4 | PASS | min-width 1280 |
| AC-5 | PASS | LLM profile/model/effort visible |
| AC-6 | PASS | no raw secrets in UI |

## Issue Counts

- P0: 0
- P1: 0
- P2: 1 (browser e2e automation)
- P3: 0

## Config / Schema Versions

- llm_profile display: llm-profile-v0.1
- PC Web only (no mobile)

## Commands to Reproduce

```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe -m pytest tests/integration/test_reads_api.py -q
cd apps\web; npm run build
```

## Next Layer Eligibility

- eligible: **yes**
- next: L10 MVP All-Pass Freeze
