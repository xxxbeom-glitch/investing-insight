# 06. PC Web UI Specification

## 1. Scope

- PC Web only
- primary viewport: 1440px class desktop
- minimum supported width target: 1280px
- mobile/tablet responsive QA는 MVP 범위 밖

UI의 목적은 화려함보다 **연구 흐름과 근거·QA 상태를 한눈에 확인하는 것**이다.

## 2. Global Layout

```text
┌──────── Sidebar ────────┬──────────────── Main Content ───────────────┐
│ investing-insight      │ Top Bar / Run Context                       │
│                        │                                              │
│ Dashboard              │                                              │
│ Research Runs          │                                              │
│ Candidates             │                                              │
│ Companies              │                                              │
│ Audit & QA              │                                              │
│ Settings               │                                              │
└────────────────────────┴──────────────────────────────────────────────┘
```

추천:
- sidebar 240~280px
- dense data table support
- cards보다 tables와 evidence panel 우선
- status color는 PASS/WARN/FAIL 의미가 명확해야 함

## 3. Dashboard

목표: 현재 시스템 상태와 최근 research run을 한 화면에서 파악.

필수:
- Latest Research Run
- Universe count
- Eligible count
- Quant shortlist count
- Selected / Watch / Reject count
- Data QA status
- Snapshot QA status
- Research QA status
- 최근 run 바로가기
- 최근 오류/P1 존재 시 상단 경고

## 4. Research Runs

table:
- run_id
- cutoff_at
- status
- snapshot QA
- quant version
- prompt version
- model
- candidates
- selected
- commit hash

상세 화면:
- pipeline step timeline
- each step PASS/WARN/FAIL
- snapshot metadata
- run config

## 5. Candidates

대형 desktop table을 기본으로 한다.

columns 예:
- Rank
- Ticker
- Company
- Sector
- Quant Score
- Growth
- Quality
- Valuation
- Momentum
- Data Quality
- Research Status
- Final Status

filter:
- sector
- status
- score range
- exchange
- ADR

## 6. Company Detail

한 화면에서 "왜 선택/탈락했는가"를 이해할 수 있어야 한다.

sections:
1. Header: ticker/company/status/selection price
2. Quant score breakdown
3. Financial trend
4. Price trend
5. AI Research Summary
6. Bull Case / Bear Case
7. Risks
8. Invalidation Conditions
9. Evidence list
10. Research QA result
11. Historical judgments

FACT와 AI ASSESSMENT 시각 구분 필수.

## 7. Audit & QA

이 화면은 사용자용이자 외부 검증용이다.

필수:
- Layer status matrix
- P0/P1/P2/P3 counts
- latest test run
- failed test drill-down
- data quarantine count
- snapshot future leak check
- audit document links/paths
- current git commit/tag display

## 8. Settings

MVP에서는 최소:
- provider connection status
- research run config
- shortlist size
- final max selections
- LLM provider/model display
- quant rule version display

Secret/API key raw value를 UI에 표시하지 않는다.

## 9. UX Principle

- 하나의 숫자에 hover만 해야 근거가 보이는 구조를 피한다.
- 중요한 QA 경고는 숨기지 않는다.
- AI 문장 옆에 source/evidence로 이동할 수 있어야 한다.
- 과거 judgment와 최신 judgment를 섞지 않는다.
- run context가 항상 명확해야 한다.

## 10. MVP UI Acceptance

- 1280px 이상에서 horizontal overflow 없이 핵심 화면 사용 가능
- Candidates table은 많은 열을 위해 내부 horizontal scroll 허용 가능
- 모든 Final Judgment에서 snapshot 및 evidence 화면으로 이동 가능
- FAIL 상태가 PASS처럼 보이지 않음
- Run detail에서 pipeline history 확인 가능
