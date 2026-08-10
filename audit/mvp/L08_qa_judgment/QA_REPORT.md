# QA_REPORT

- layer_id: L08
- executed_at: 2026-08-10
- commit_hash: 765c5f0
- previous_layer_commit: fcedd02
- status: PASS
- spec_version: investing-insight-spec-v1.6

## Acceptance Matrix

| ID | Criterion | Evidence | Result |
|----|-----------|----------|--------|
| AC-1 | unsupported numeric claim → FAIL | claim_check unit/integration | PASS |
| AC-2 | QA FAIL → SELECTED blocked | judgment policy | PASS |
| AC-3 | new unsupported fact → FAIL | enforce_judgment_policy | PASS |
| AC-4 | role profile model/effort recorded | qa.py / judgment.py | PASS |
| AC-5 | silent fallback 0 | ModelUnavailableError | PASS |
| AC-6 | selection minimum not forced | policy + prompt | PASS |
| AC-7 | judgment UPDATE forbidden | DB trigger migration 0009 | PASS |
| AC-8 | SELECTED requires bear/risks/invalidation | policy | PASS |

## LLM Metadata (required)

| Role | Profile | Model | Effort | Prompt | Schema |
|------|---------|-------|--------|--------|--------|
| research_qa | llm-profile-v0.1 | gpt-5.6-terra | high | research-qa-prompt-v0.1 | research-qa-output-v0.1 |
| final_judgment | llm-profile-v0.1 | gpt-5.6-terra | high | final-judgment-prompt-v0.1 | final-judgment-output-v0.1 |

Sample live input/output hashes: unknown — revalidated during L10 remediation (see evidence paths in TEST_RESULTS).

## Issue Counts

- P0 open: 0
- P1 open: 0
- P2 open: 0
- P3 open: 0

## Final QA Status

- Blocking Status: **PASS**
- Next layer eligible: yes (L09)
