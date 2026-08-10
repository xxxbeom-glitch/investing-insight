# TEST_RESULTS

- layer_id: L07
- executed_at: 2026-08-10T21:03:40+09:00
- commit_hash: 960457c
- spec_version: investing-insight-spec-v1.6

## Commands

```text
pytest tests/unit/test_research_schema.py tests/integration/test_research_packet.py -q
pytest tests -q
```

## Results Summary (historical)

| Suite | Pass | Fail | Skip | Source |
|-------|------|------|------|--------|
| research schema/packet/company_research | 4 | 0 | 0 | original TEST_RESULTS |
| pytest full suite after L07 | 41 | 0 | 0 | original TEST_RESULTS |

## LLM / Config Versions Under Test

- llm-profile-v0.1 / company_research / gpt-5.6-terra / medium
- company-research-prompt-v0.1
- company-analysis-input-v0.1 / company-analysis-output-v0.1

## Live execution hashes

- Historical per-run `input_hash` / `output_hash` for a production live OpenAI call: unknown — revalidated during L10 remediation (suite path; live model optional)
- Representative snapshot content_hash (downstream of packet inputs) recorded in `MVP_HANDOFF.md`: `5fb7a83b…`
- Revalidation: `audit/mvp/L10_mvp_freeze/evidence/pytest_revalidation_erp104.txt`
- Config snapshot pointer: `audit/mvp/L10_mvp_freeze/evidence/llm_config_versions_erp104.md`
