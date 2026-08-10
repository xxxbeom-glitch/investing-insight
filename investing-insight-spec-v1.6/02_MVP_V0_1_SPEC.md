# 02. MVP v0.1 Specification

## 1. MVP Definition

MVP는 미국 상장사 registry에서 시작해 `수집 → 검증 → Snapshot → Quant → 동적 Research Packet → AI Research → Research QA → Final Judgment → PC Web`까지 한 번 끝까지 통과하는 최소 완성품이다.

MVP의 목적은 투자 성과가 아니라 **데이터 무결성, 재현성, AI 근거 추적성, 개발 감사 가능성**을 증명하는 것이다.

## 2. MVP Runtime

- Web/API는 개발 PC에서 실행
- DB는 Supabase PostgreSQL
- ingest/research run은 수동 command로 실행 가능
- 운영 자동화/배포는 하지 않음

## 3. MVP In Scope

### Universe Registry
- NYSE + NASDAQ
- 일반 사업회사 보통주 + ADR
- 지정 제외상품 제거
- company_id/security_id
- historical membership

### Data
- 일별 OHLCV
- security metadata
- SEC company facts 핵심 재무
- SEC filings metadata
- raw payload hash/source metadata

### Data QA
- schema / required / duplicate
- unit / date / impossible value
- source traceability
- future leak eligibility
- quarantine

### Snapshot
- exact cutoff timestamp
- eligible universe membership
- price/financial/filing availability
- source hashes/versions
- content hash

### Quant
공통 요소:
- Growth
- Quality
- Cash Flow
- Financial Health
- Valuation
- Momentum

Industry-specific score는 Post-MVP.

### Candidate Shortlist
- hard exclusion 최소화
- Quant rank 기반
- Research 대상 기본 10~20개
- 최종 선정 최대 5개, 0개 허용

### AI Research — MVP Roles
1. Company Research
   - `gpt-5.6-terra`
   - `reasoning.effort=medium`
2. Research QA
   - `gpt-5.6-terra`
   - `reasoning.effort=high`
3. Final Judgment
   - `gpt-5.6-terra`
   - `reasoning.effort=high`

OpenAI Responses API + Structured Output/Schema Validation을 사용한다.

### JSON Contract
- 기업별 영구 JSON 파일 생성 금지
- Research Packet은 snapshot에서 동적 생성
- Input/Output/QA contracts는 versioned schema
- schema fail → next step 금지

### Judgment
저장:
- SELECTED / WATCH / REJECT
- selection price
- quant score
- thesis / why_now
- evidence refs
- bear case / risks
- invalidation conditions
- uncertainty
- evidence quality
- data completeness
- snapshot_id
- prompt_version
- model_id
- reasoning_effort
- llm_profile_version
- input/output hash

### PC Web
최소 화면:
1. Dashboard
2. Research Runs
3. Candidates
4. Company Detail
5. Audit & QA
6. Settings/Config read-only summary

## 4. MVP Explicitly Out of Scope

- FRED/Macro Agent
- full Top-down industry attractiveness/value-chain engine
- industry-specific score templates
- separate model vendor cross-check
- GPT-5.6 Sol independent QA
- event-triggered research
- performance grading automation
- rejected-stock long-term control group
- self-learning rule optimization
- cloud scheduler/public deployment
- trading execution

## 5. Run Modes

### Smoke Mode
- deterministic fixtures
- 대표 종목 20~30개
- 외부 API 없이 core tests 가능

### Integration Mode
- 실제 Supabase/Massive/SEC/OpenAI 연결
- API 비용/호출 상한 설정

### Full Registry Mode
- NYSE/NASDAQ 전체 registry
- Universe classification 검증

### Research Mode
- 제한된 shortlist만 LLM 호출
- token/cost budget 필수

## 6. MVP Success Criteria

모두 충족:
- L00~L10 Blocking QA PASS
- P0 open = 0
- P1 open = 0
- Snapshot future leakage fixture PASS
- Snapshot reproducibility PASS
- Quant deterministic PASS
- Research packet schema PASS
- unsupported factual claim 차단/flag PASS
- role별 LLM profile이 config대로 호출·기록됨
- model/profile silent fallback 0
- judgment → snapshot → evidence 역추적 가능
- PC Web core flow 사용 가능
- audit package 완성
- Git tag 생성

## 7. MVP Stop Rule

MVP ALL PASS 후 Cursor는 Post-MVP를 구현하지 않는다.

반드시 `MVP_HANDOFF.md`에:
- final git tag/commit
- DB schema/migration version
- provider config summary(secret 제외)
- quant rule version
- prompt version
- llm_profile_version + role별 model/reasoning
- representative run/snapshot/judgment IDs
- test commands
- P2/P3 backlog
- reproduction steps

을 기록하고 중단한다.
