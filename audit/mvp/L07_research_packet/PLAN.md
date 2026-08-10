# PLAN

- layer_id: L07
- layer_name: research_packet
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10T20:56:27+09:00 (after previous_layer_commit 7f78093)
- status: PASS (frozen)
- previous_layer_commit: 7f78093
- commit_hash: 960457c (PASS; HANDOFF hash recorded in fcedd02)

## Goal

상위 후보를 동적 JSON research packet으로 만들고 OpenAI Responses adapter로 Company Research를 기록한다 (Fail Closed, no silent model fallback).

## In Scope

- packet builder (snapshot evidence only)
- `company_analysis_input` / `company_analysis_output` schemas
- token/context budget via `config/research_limits.v0.1.yaml`
- OpenAI Responses API adapter
- Company Research role from `config/llm_profiles.v0.1.yaml`
- prompt `config/prompts/company_research.v0.1.txt`
- migration `0008_research_llm.sql` (llm_executions / research tables)

## Out of Scope

- Research QA / Final Judgment (L08)
- PC Web (L09)
- Silent model fallback

## Baseline LLM (from config at PASS)

- llm_profile_version: `llm-profile-v0.1`
- role: `company_research`
- model: `gpt-5.6-terra`
- reasoning_effort: `medium`
- prompt_version: `company-research-prompt-v0.1`
- input schema: `company-analysis-input-v0.1` (`company_analysis_input.v0.1`)
- output schema: `company-analysis-output-v0.1` (`company_analysis_output.v0.1`)
- packet_version: `packet-v0.1`
- research_limits: `research-limits-v0.1`

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | packet snapshot evidence only | yes |
| AC-2 | numeric facts evidence IDs | yes |
| AC-3 | input/output schema PASS | yes |
| AC-4 | requested/executed model+effort 기록 | yes |
| AC-5 | llm_profile_version/prompt/input/output hash 기록 | yes |
| AC-6 | unavailable model silent fallback 0 | yes |
| AC-7 | unsupported_or_missing explicit | yes |

## Expected Files

- `apps/api/app/research/{packet,schema_validate,openai_responses,company_research}.py`
- `config/prompts/company_research.v0.1.txt`
- `config/research_limits.v0.1.yaml`
- `migrations/0008_research_llm.sql`
- `tests/integration/test_research_packet.py`, `tests/unit/test_research_schema.py`
- `audit/mvp/L07_research_packet/**`

## Tests to Write First

- packet schema validate
- evidence-only packet
- ModelUnavailableError fail-closed (no silent fallback)
- hash fields recorded

## Risks

- Live gateway may reject configured model id → Fail Closed (P2 ops, not silent fallback)
- Packet size budgets

## Notes

- LLM profile/model/effort recovered from `config/llm_profiles.v0.1.yaml` @ PASS tree (also present at tag `mvp-v0.1-pass`).
- Per-run live input/output execution hashes: unknown — not retained in original audit; exercised in tests / optional live path.
