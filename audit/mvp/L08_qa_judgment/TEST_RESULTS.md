# TEST_RESULTS

- layer_id: L08
- executed_at: 2026-08-10T21:10:20+09:00
- commit_hash: 765c5f0
- spec_version: investing-insight-spec-v1.6

## Commands

```text
pytest tests/unit/test_claim_check.py tests/integration/test_qa_judgment.py -q
pytest tests -q
```

## Results Summary (historical)

| Suite | Pass | Fail | Skip | Source |
|-------|------|------|------|--------|
| claim_check + qa_judgment | 3 | 0 | 0 | original TEST_RESULTS |
| pytest full suite after L08 | 44 | 0 | 0 | original TEST_RESULTS |

## LLM / Config Versions Under Test

- llm-profile-v0.1
- research_qa: gpt-5.6-terra / high / research-qa-prompt-v0.1 / research-qa-output-v0.1
- final_judgment: gpt-5.6-terra / high / final-judgment-prompt-v0.1 / final-judgment-output-v0.1

## Live execution hashes / judgment_ids

- Historical live OpenAI execution hashes / judgment_ids for a production SELECTED path: unknown — revalidated during L10 remediation
- `MVP_HANDOFF.md`: “judgment_ids: (sample path exercised in tests; live judgment optional per model availability)”
- Evidence: `audit/mvp/L10_mvp_freeze/evidence/pytest_revalidation_erp104.txt`
- Config snapshot: `audit/mvp/L10_mvp_freeze/evidence/llm_config_versions_erp104.md`
