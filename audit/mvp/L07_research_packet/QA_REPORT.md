# QA_REPORT

- layer_id: L07
- executed_at: 2026-08-10
- commit_hash: 960457c
- previous_layer_commit: 7f78093
- status: PASS
- spec_version: investing-insight-spec-v1.6

## Acceptance Matrix

| ID | Criterion | Evidence | Result |
|----|-----------|----------|--------|
| AC-1 | packet snapshot evidence only | packet builder + integration | PASS |
| AC-2 | numeric facts evidence IDs | packet/tests | PASS |
| AC-3 | input/output schema PASS | schema_validate + unit | PASS |
| AC-4 | requested/executed model+effort 기록 | llm_executions columns / runner | PASS |
| AC-5 | profile/prompt/input/output hash 기록 | company_research.py insert/update | PASS |
| AC-6 | silent model fallback 0 | ModelUnavailableError path | PASS |
| AC-7 | unsupported_or_missing explicit | output schema required field | PASS |

## LLM Metadata (required)

| Field | Value | Source |
|-------|-------|--------|
| llm_profile_version | llm-profile-v0.1 | config/llm_profiles.v0.1.yaml |
| role | company_research | same |
| model | gpt-5.6-terra | same |
| reasoning_effort | medium | same |
| prompt_version | company-research-prompt-v0.1 | research_limits + code |
| input schema | company-analysis-input-v0.1 | packages/schemas |
| output schema | company-analysis-output-v0.1 | packages/schemas |
| sample live input/output hash | unknown — revalidated during L10 remediation | tests exercise hash fields |

## Issue Counts

- P0 open: 0
- P1 open: 0
- P2 open: 0 (live gateway naming tracked at L10)
- P3 open: 0

## Final QA Status

- Blocking Status: **PASS**
- Next layer eligible: yes (L08)
