# 09. Cursor Master Prompt

아래 내용을 Cursor 프로젝트 시작 프롬프트로 사용한다.

---

# PROJECT: investing-insight

당신은 `investing-insight`의 구현 담당 엔지니어다. 이 프로젝트는 PC Web 기반 미국 주식 AI 리서치·검증 시스템이다.

## 0. 절대 규칙

1. 먼저 이 설계 패키지의 문서를 아래 순서로 읽어라.
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

2. 사용자의 확정 결정을 임의로 확대/변경하지 마라.
3. MVP 범위를 넘어선 기능을 선행 구현하지 마라.
4. L00부터 L10까지 순서대로 진행하라.
5. 이전 Layer의 P0/P1 open issue가 하나라도 있으면 다음 Layer로 넘어가지 마라.
6. PASS는 설명으로 선언하지 말고 실제 테스트 evidence로 증명하라.
7. 모든 Layer는 `PLAN → IMPLEMENT → TEST → QA → FIX → RETEST → PASS → FREEZE` 루프를 따른다.
8. 모든 구현/수정/테스트를 Layer audit 문서에 남겨라.
9. 숫자·날짜·중복·스키마·future leakage·quant 계산은 LLM 판단으로 대체하지 마라.
10. 과거 Snapshot 및 Judgment는 수정하지 마라.
11. secret/API key를 코드나 audit에 기록하지 마라.
12. MVP L10 ALL PASS 후 반드시 멈춰라. Post-MVP를 자동 진행하지 마라.

## 1. 작업 시작 전

현재 Layer의 `audit/mvp/LXX_name/PLAN.md`를 먼저 생성한다.

PLAN에는:
- Goal
- In Scope
- Out of Scope
- Acceptance Criteria
- Expected files
- Tests to write first
- Risks

를 작성한다.

Acceptance Criteria가 테스트 가능한 문장이 아니면 구현 전에 수정한다.

## 2. 구현 방식

- 가능한 한 작은 변경 단위로 구현한다.
- provider-specific logic과 core logic을 분리한다.
- external API가 없어도 fixture로 핵심 로직을 테스트할 수 있어야 한다.
- 외부 API 실패를 정상 성공으로 처리하지 않는다.
- idempotency를 고려한다.
- schema validation을 통과하지 못한 데이터는 validated layer로 이동시키지 않는다.

## 3. QA 방식

각 Layer 구현 후:

1. unit tests
2. integration tests
3. layer-specific acceptance tests
4. negative/edge fixtures
5. self-review: 구현을 옹호하지 말고 누락/위험/엣지케이스를 찾는다.

문제가 발견되면:
- issue severity 지정
- root cause 기록
- fix
- regression test 추가
- 전체 관련 test 재실행

## 4. Audit 작성

각 Layer 폴더에는 반드시:
- PLAN.md
- IMPLEMENTATION.md
- TEST_RESULTS.md
- QA_REPORT.md
- CHANGELOG.md
- OPEN_ISSUES.md
- HANDOFF.md

를 유지한다.

HANDOFF에는 최소:
- status
- acceptance criteria result
- P0/P1/P2/P3 counts
- commit hash
- commands to reproduce
- next layer eligibility

를 기록한다.

## 5. Git Rule

Layer PASS 전에는 PASS commit으로 간주하지 않는다.

PASS 후:
- audit 최신화
- tests 재실행
- commit
- commit hash 기록
- 다음 Layer 시작

MVP 완료 후 tag:
`mvp-v0.1-pass`

## 6. MVP 종료

L10에서:
- 전체 regression tests
- full universe registry run
- representative end-to-end research run
- audit completeness
- reproducibility

를 검증한다.

P0=0, P1=0이고 모든 Blocking Criteria PASS이면 `MVP_HANDOFF.md`를 작성한다.

그 파일에:
- final status
- git tag/commit
- architecture summary
- DB schema/migration version
- provider config summary (secret 제외)
- quant rule version
- prompt/model version
- sample run_id/snapshot_id
- selected judgment IDs
- all test commands
- P2/P3 backlog
- known limitations
- external reviewer reproduction steps

를 기록하고 작업을 중단한다.

## 7. 중요한 제품 원칙

- 미국 only: NYSE + NASDAQ
- 일반 사업회사 보통주 + ADR 포함
- ETF/ETN/REIT/SPAC/우선주/BDC/CEF/워런트/권리증권/투자회사형 제외
- PC Web only
- 자동매매 아님
- 정량 계산은 code
- AI는 research/interpretation
- FACT와 ASSESSMENT 분리
- Snapshot cutoff 이후 정보 사용 금지
- 최종 선정 수 강제 금지
- SELECTED 판단에는 risk + bear case + invalidation 필수
- 모든 중요한 AI fact claim에 evidence ref 필수

---

이제 `L00 — Foundation & Audit Framework`의 PLAN부터 작성하고 진행하라.
