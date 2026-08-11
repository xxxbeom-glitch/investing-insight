# QA_REPORT — status_diagnosis_ecb778e

- status: PASS (진단 산출물 기준)
- P0: 0
- P1 (audit 결함): 0
- P1 (2차 readiness 라벨): 4 — 제품 GO 금지 근거. 코드 회귀 아님

## AC

| ID | Result | Evidence |
|----|--------|----------|
| AC-1 | PASS | `facts.json` |
| AC-2 | PASS | `llm_qa.json` resolved=`gpt-5.6-terra` |
| AC-3 | PASS | `REPORT.md` |
| AC-4 | PASS | cron/tag/GO 변경 없음 |

## Commands

- OpenAIResponsesClient structured call (research_qa_agent)
- `GET /v1/ops/health`
- `GET /v1/companies/2c3f9b93-…?run_id=31835b24-…`
