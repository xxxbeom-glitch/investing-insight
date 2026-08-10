# IMPLEMENTATION

- layer_id: L07
- status: PASS
- completed_at: 2026-08-10T21:03:40+09:00
- commit_hash: 960457c
- previous_layer_commit: 7f78093
- spec_version: investing-insight-spec-v1.6

## What Changed

- Research packet builder + schema validate
- OpenAI Responses client (`openai_responses.py`) with reasoning.effort
- Company research runner recording llm_profile/prompt/model/effort/hashes
- `config/prompts/company_research.v0.1.txt`
- `config/research_limits.v0.1.yaml` (`company_research_prompt_version: company-research-prompt-v0.1`)
- migration `0008_research_llm.sql`

## LLM Execution Contract (recorded by code)

| Field | Value (config/code SoT) |
|-------|-------------------------|
| llm_profile_version | llm-profile-v0.1 |
| role | company_research |
| requested model | gpt-5.6-terra |
| reasoning_effort | medium |
| prompt file | config/prompts/company_research.v0.1.txt |
| prompt_version | company-research-prompt-v0.1 |
| packet_schema_version | company-analysis-input-v0.1 |
| packet_version | packet-v0.1 |
| output schema_version | company-analysis-output-v0.1 |
| research_limits version | research-limits-v0.1 |
| silent fallback | forbidden (`ModelUnavailableError` if resolved ≠ requested) |

## Files Changed (from `git show --stat 960457c`)

- `apps/api/app/research/{__init__,packet,schema_validate,openai_responses,company_research}.py`
- `config/prompts/company_research.v0.1.txt`, `config/research_limits.v0.1.yaml`
- `migrations/0008_research_llm.sql`
- `tests/integration/test_research_packet.py`, `tests/unit/test_research_schema.py`
- audit + TASK_CONTRACT + active-track
- Totals: 19 files, +822 / −8

## Commands Run

```text
# historical (original TEST_RESULTS)
# research schema/packet/company_research tests — 4 passed
pytest tests -q   # 41 passed
```

## Deviations from PLAN

- none recorded
