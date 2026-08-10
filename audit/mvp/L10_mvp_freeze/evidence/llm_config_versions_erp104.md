# LLM / Config / Schema versions (ER-P1-04 revalidation snapshot)

Recovered from versioned files at remediation time (same content as MVP freeze configs; do not invent).

## Source files

- `config/llm_profiles.v0.1.yaml`
- `config/research_limits.v0.1.yaml`
- `config/quant_rules.v0.1.yaml`
- `config/prompts/company_research.v0.1.txt`
- `config/prompts/research_qa.v0.1.txt`
- `config/prompts/final_judgment.v0.1.txt`
- `packages/schemas/*.schema.json`
- Code constants in `apps/api/app/research/{company_research,qa,judgment,packet}.py`

## LLM profile — llm-profile-v0.1

| Role | Model | reasoning_effort |
|------|-------|------------------|
| company_research | gpt-5.6-terra | medium |
| research_qa | gpt-5.6-terra | high |
| final_judgment | gpt-5.6-terra | high |

Provider/API: openai / responses

## Prompts

| Version id | File |
|------------|------|
| company-research-prompt-v0.1 | config/prompts/company_research.v0.1.txt |
| research-qa-prompt-v0.1 | config/prompts/research_qa.v0.1.txt |
| final-judgment-prompt-v0.1 | config/prompts/final_judgment.v0.1.txt |

## Schemas

| Version / $id | File |
|---------------|------|
| company-analysis-input-v0.1 / company_analysis_input.v0.1 | company_analysis_input.schema.json |
| company-analysis-output-v0.1 / company_analysis_output.v0.1 | company_analysis_output.schema.json |
| research-qa-output-v0.1 / research_qa_output.v0.1 | research_qa_output.schema.json |
| final-judgment-output-v0.1 / final_judgment_output.v0.1 | final_judgment_output.schema.json |
| snapshot_manifest.v0.1 | snapshot_manifest.schema.json |

## Other

- research-limits-v0.1
- quant-rules-v0.1
- packet-v0.1
- migrations 0001–0009

## Unknown (not inventable)

- Historical live OpenAI `input_hash` / `output_hash` / `judgment_id` for a production SELECTED call at freeze time were not retained in original L07/L08 audit stubs.
- Suite path revalidation: see `pytest_revalidation_erp104.txt` (unit 28 passed; full suite hung during remediation).
- Representative snapshot content_hash remains as recorded in `MVP_HANDOFF.md`.
