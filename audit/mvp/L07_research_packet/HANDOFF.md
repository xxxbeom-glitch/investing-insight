# HANDOFF

- layer_id: L07
- layer_name: research_packet
- status: PASS
- completed_at: 2026-08-10T21:03:40+09:00
- commit_hash: 960457c
- previous_layer_commit: 7f78093
- handoff_hash_commit: fcedd02
- spec_version: investing-insight-spec-v1.6

## Acceptance Criteria Result

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 | PASS | packet snapshot evidence only |
| AC-2 | PASS | evidence IDs on numeric facts |
| AC-3 | PASS | input/output schema |
| AC-4 | PASS | model+effort recorded |
| AC-5 | PASS | profile/prompt/hashes recorded in code path |
| AC-6 | PASS | ModelUnavailableError (no silent fallback) |
| AC-7 | PASS | unsupported_or_missing required |

## Issue Counts

- P0: 0
- P1: 0
- P2: 0
- P3: 0

## Config / Schema / LLM Versions

- llm_profile: llm-profile-v0.1
- company_research: gpt-5.6-terra / reasoning_effort=medium
- prompt: company-research-prompt-v0.1 (`config/prompts/company_research.v0.1.txt`)
- research_limits: research-limits-v0.1
- schemas: company-analysis-input-v0.1, company-analysis-output-v0.1
- packet_version: packet-v0.1
- migration: 0008_research_llm.sql

## Commands to Reproduce

```text
$env:PYTHONPATH="apps\api"
.\apps\api\.venv\Scripts\python.exe -m pytest tests/unit/test_research_schema.py tests/integration/test_research_packet.py -q
```

## Next Layer Eligibility

- eligible: **yes**
- next: L08 Research QA & Final Judgment

## Notes for Next Layer

- Research QA / Final Judgment roles use high effort; do not reuse company_research medium profile.
