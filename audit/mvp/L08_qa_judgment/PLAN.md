# PLAN

- layer_id: L08
- layer_name: qa_judgment
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T21:03:43+09:00 (after previous_layer_commit fcedd02)
- status: PASS (frozen)
- previous_layer_commit: fcedd02
- commit_hash: 765c5f0 (PASS; HANDOFF hash recorded in cb6762a)

## Goal

Research를 엄격 검수하고 최종 Judgment를 immutable하게 저장한다. SELECTED는 risk+bear+invalidation 필수; QA FAIL → SELECTED 불가.

## In Scope

- Deterministic claim/evidence checker
- Research QA role + Final Judgment role
- Immutable judgment (DB trigger)
- Schemas + prompts for QA/judgment
- migration `0009_qa_judgment.sql`

## Out of Scope

- PC Web (L09)
- Forced minimum selection count
- Mutating past judgments

## Baseline LLM (from config at PASS)

### Research QA

- llm_profile_version: `llm-profile-v0.1`
- role: `research_qa`
- model: `gpt-5.6-terra`
- reasoning_effort: `high`
- prompt_version: `research-qa-prompt-v0.1`
- prompt file: `config/prompts/research_qa.v0.1.txt`
- output schema: `research-qa-output-v0.1` (`research_qa_output.v0.1`)

### Final Judgment

- llm_profile_version: `llm-profile-v0.1`
- role: `final_judgment`
- model: `gpt-5.6-terra`
- reasoning_effort: `high`
- prompt_version: `final-judgment-prompt-v0.1`
- prompt file: `config/prompts/final_judgment.v0.1.txt`
- output schema: `final-judgment-output-v0.1` (`final_judgment_output.v0.1`)

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | unsupported numeric claim fixture rejected/flagged | yes |
| AC-2 | QA FAIL → SELECTED 불가 | yes |
| AC-3 | final model이 evidence 없는 새 fact 추가 시 FAIL | yes |
| AC-4 | role profile mismatch 0 | yes |
| AC-5 | silent fallback 0 | yes |
| AC-6 | selection minimum 강제 없음 | yes |
| AC-7 | judgment overwrite 0 | yes |
| AC-8 | SELECTED risk+bear+invalidation required | yes |

## Expected Files

- `apps/api/app/research/{claim_check,qa,judgment}.py`
- `config/prompts/research_qa.v0.1.txt`, `final_judgment.v0.1.txt`
- `migrations/0009_qa_judgment.sql`
- `tests/unit/test_claim_check.py`, `tests/integration/test_qa_judgment.py`
- `audit/mvp/L08_qa_judgment/**`

## Tests to Write First

- claim_check FAIL on unsupported numeric
- QA FAIL blocks SELECTED
- immutable UPDATE forbidden
- SELECTED required fields

## Risks

- Optional LLM tightening vs deterministic claim_check authority
- Live model availability (Fail Closed)

## Notes

- Profile/prompt/schema recovered from `config/llm_profiles.v0.1.yaml` + prompt files + code constants at PASS.
