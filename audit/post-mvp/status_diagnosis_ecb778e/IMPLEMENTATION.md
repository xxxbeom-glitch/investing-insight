# IMPLEMENTATION

- status: DONE (diagnosis only; not GO)
- completed_at: 2026-08-11T14:45:00+00:00
- head_diagnosed: ecb778e98d8f168b20594324e5b4bcf1ca819c42

## 1차 진단

Git HEAD/tag, `audit/post-mvp/*` HANDOFF, `_docs/active-track.md`, ops health, 로컬 데모 run을 수집해 `facts.json`에 고정.

## 2차 LLM QA

```text
role: research_qa_agent
requested_model: gpt-5.6-terra
resolved_model: gpt-5.6-terra
reasoning_effort: high
client: OpenAIResponsesClient.create_structured
payload: facts.json only (no secrets)
```

결과: `llm_qa.json` (`response_id` 포함).

## 라이브 재조회

`GET /v1/ops/health` + `GET /v1/companies/{AAPL}?run_id=31835b24-…` → `live_snapshot.json` (packet raw 제외, failed_claims만).

## 켜지 않은 것

tag / GO / cron / 공개 배포 / Long-Term Optional
