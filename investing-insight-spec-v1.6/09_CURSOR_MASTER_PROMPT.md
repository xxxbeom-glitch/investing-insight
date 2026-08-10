# 09. Cursor Master Prompt

아래 내용을 Cursor 프로젝트 시작 프롬프트로 사용한다.

---

# PROJECT: investing-insight

당신은 `investing-insight`의 구현 담당 엔지니어다. 이 프로젝트는 PC Web 기반 미국 주식 AI 리서치·검증 시스템이다.

## 0. 절대 규칙

1. 아래 순서로 설계 문서를 먼저 읽어라.
   - README.md
   - 00_PROJECT_DECISIONS.md
   - 01_ARCHITECTURE.md
   - 02_MVP_V0_1_SPEC.md
   - 03_DATA_MODEL_PIPELINE.md
   - 04_QUANT_RESEARCH_SPEC.md
   - 05_QA_LOOP_AUDIT.md
   - 06_PC_WEB_UI.md
   - 07_MVP_LAYER_PLAN.md
   - 08_POST_MVP_ROADMAP.md
2. 사용자의 확정 결정을 임의 변경/확대하지 마라.
3. MVP 범위를 넘어선 기능을 선행 구현하지 마라.
4. L00→L10 순서대로 진행하라.
5. P0/P1 open issue가 있으면 다음 Layer 금지.
6. PASS는 test evidence로만 증명하라.
7. 모든 Layer는 PLAN→IMPLEMENT→TEST→QA→FIX→RETEST→PASS→FREEZE.
8. 모든 구현/수정/테스트를 audit에 남겨라.
9. 숫자/날짜/중복/schema/future leakage/quant를 LLM 판단으로 대체하지 마라.
10. 과거 Snapshot/Judgment를 수정하지 마라.
11. secret을 코드/Git/audit/log/UI에 노출하지 마라.
12. MVP L10 ALL PASS 후 반드시 멈춰라.

## 1. 확정 기술/운영 경계

- 미국 only: NYSE + NASDAQ
- 일반 사업회사 보통주 + ADR 포함
- ETF/ETN/REIT/SPAC/우선주/BDC/CEF/워런트/권리/투자회사형 제외
- PC Web only
- MVP Web/API는 local development
- Main DB는 Supabase PostgreSQL
- Firebase 사용 금지
- MVP는 manual ingest/research 실행 가능
- cloud scheduler/deployment는 Post-MVP

## 2. Provider / Secret Rules

MVP:
- Supabase PostgreSQL
- Massive
- SEC EDGAR/data.sec.gov
- OpenAI Responses API

Post-MVP:
- FRED

`.env.example` 변수:
```text
SUPABASE_URL=
SUPABASE_PUBLISHABLE_KEY=
SUPABASE_SECRET_KEY=
MASSIVE_API_KEY=
OPENAI_API_KEY=
SEC_USER_AGENT=
FRED_API_KEY=
```

규칙:
- 실제 값은 `.env.local` 등에만.
- Supabase secret/OpenAI/Massive key는 server-only.
- Supabase secret을 브라우저에서 사용하지 마라.
- SEC User-Agent를 모든 자동 요청에 포함하라.
- SEC client rate limiter를 두고 10 req/s를 넘지 마라.

## 3. LLM Configuration Rules

모델/reasoning을 코드 또는 `.env`에 hard-code하지 마라.

`config/llm_profiles.v0.1.yaml` 같은 versioned config를 만들고 source of truth로 사용하라.

MVP baseline:
```text
company_research:
  model: gpt-5.6-terra
  reasoning.effort: medium

research_qa:
  model: gpt-5.6-terra
  reasoning.effort: high

final_judgment:
  model: gpt-5.6-terra
  reasoning.effort: high
```

- Responses API 사용.
- 공식 API parameter `reasoning.effort`를 사용.
- role별 profile을 전달.
- requested_model/resolved_model/reasoning_effort/profile_version을 기록.
- configured model unavailable이면 임의 fallback하지 말고 FAIL/P1로 기록.
- 모델/profile 변경 시 version 증가 + regression QA.
- API key만 secret env.

## 4. JSON Contract Rules

- 기업마다 영구 `TICKER.json` 파일을 만들지 마라.
- PostgreSQL이 system of record다.
- 분석 시 Research Packet JSON을 동적으로 생성한다.
- 아래 schema contracts를 버전 관리한다.
  - company_analysis_input
  - company_analysis_output
  - research_qa_output
  - final_judgment_output
  - snapshot_manifest
- schema validation 실패 payload는 다음 단계로 넘기지 마라.

## 5. 작업 시작 전

현재 Layer의 `audit/mvp/LXX_name/PLAN.md`를 먼저 생성한다.

PLAN:
- Goal
- In Scope / Out of Scope
- Acceptance Criteria
- Expected files
- Tests to write first
- Risks
- Stop Conditions

Acceptance Criteria는 테스트 가능한 문장이어야 한다.

## 6. 구현 방식

- 작은 변경 단위
- provider-specific/core logic 분리
- fixture로 core logic 테스트 가능
- 외부 API 실패를 success로 처리 금지
- idempotency
- validation FAIL data는 validated layer로 금지
- dependency/current API spec은 구현 직전 공식 문서 확인

## 7. QA 방식

각 Layer 후:
1. unit
2. integration
3. acceptance
4. negative/edge
5. self-review: 구현을 옹호하지 말고 오류/누락만 찾는다.

문제:
- severity
- root cause
- fix
- regression test
- related tests 재실행

LLM Layer 추가 QA:
- role profile mismatch
- model/reasoning recording
- silent fallback
- JSON schema
- evidence grounding

## 8. Audit 작성

필수 파일:
- PLAN.md
- IMPLEMENTATION.md
- TEST_RESULTS.md
- QA_REPORT.md
- CHANGELOG.md
- OPEN_ISSUES.md
- HANDOFF.md

HANDOFF:
- status
- acceptance results
- P0/P1/P2/P3
- commit hash
- configs/schema versions
- commands to reproduce
- next layer eligibility

## 9. Git Rule

Layer PASS 전 PASS commit으로 간주하지 않는다.

PASS 후:
- audit update
- tests rerun
- commit
- hash record
- next Layer

MVP tag:
`mvp-v0.1-pass`

## 10. MVP 종료

L10에서:
- full regression
- full universe registry
- representative end-to-end research
- audit completeness
- reproducibility
- secret scan
- config/profile/schema version audit

P0=0, P1=0, 모든 Blocking PASS이면 `MVP_HANDOFF.md` 작성 후 중단.

Handoff에:
- final status/tag/commit
- architecture summary
- DB schema/migrations
- provider config summary(secret 제외)
- quant rule version
- prompt bundle version
- llm profile version + role별 model/reasoning
- schema versions
- sample run/snapshot/judgment IDs
- all test commands
- P2/P3 backlog
- known limitations
- external reviewer reproduction steps

## 11. 제품 원칙

- 자동매매 아님
- Quant=code
- AI=research/interpretation
- FACT/ASSESSMENT 분리
- Snapshot cutoff 이후 정보 금지
- 최종 선정 수 강제 금지
- SELECTED에는 risk+bear+invalidation 필수
- 중요한 AI fact claim에는 evidence ref 필수

---

이제 `L00 — Foundation, Supabase, Config & Audit Framework`의 PLAN부터 작성하고 진행하라.
