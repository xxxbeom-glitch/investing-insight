# 06. PC Web UI Specification

## 1. Scope

- PC Web only
- primary viewport: 1440px class
- minimum target: 1280px
- mobile/tablet QA는 MVP 밖
- MVP에서는 개발 PC에서 로컬 접속

UI 목적은 화려함이 아니라 **연구 흐름·근거·QA·버전을 즉시 확인**하는 것이다.

## 2. Global Layout

```text
┌──────── Sidebar ────────┬──────────────── Main Content ───────────────┐
│ investing-insight      │ Top Bar / Run Context                       │
│ Dashboard              │                                              │
│ Research Runs          │                                              │
│ Candidates             │                                              │
│ Companies              │                                              │
│ Audit & QA             │                                              │
│ Settings               │                                              │
└────────────────────────┴──────────────────────────────────────────────┘
```

## 3. Dashboard

필수:
- Latest Research Run
- Universe/Eligible/Shortlist counts
- Selected/Watch/Reject counts
- Data/Snapshot/Research/Final QA status
- provider connection status
- P0/P1 경고
- latest config versions

## 4. Research Runs

Table:
- run_id
- cutoff_at
- status
- snapshot QA
- quant version
- prompt bundle version
- llm profile version
- candidates/selected
- commit hash

Detail:
- pipeline timeline
- step PASS/WARN/FAIL
- snapshot metadata
- role별 실제 model/reasoning 기록
- input/output hashes

## 5. Candidates

Columns 예:
- Rank
- Ticker / Company
- Sector
- Quant Score/components
- Data Quality
- Research Status
- Research QA
- Final Status

Filters:
- sector/status/score/exchange/ADR

## 6. Company Detail

Sections:
1. Header: ticker/company/status/selection price
2. Quant breakdown
3. Financial trend
4. Price trend
5. AI Research
6. Bull/Bear
7. Risks
8. Invalidation
9. Evidence
10. QA result
11. LLM execution metadata
12. Historical judgments

FACT와 ASSESSMENT를 시각적으로 명확히 구분한다.

## 7. Audit & QA

필수:
- Layer status matrix
- P0/P1/P2/P3
- latest test run
- failed tests
- quarantine count
- future leak check
- config/profile versions
- git commit/tag
- audit path/document references

## 8. Settings

MVP에서는 **표시/검증 중심**이다.

표시:
- Supabase connected 여부
- Massive connected 여부
- SEC client/User-Agent configured 여부(실제 이메일 raw 노출은 피할 수 있음)
- OpenAI connected 여부
- current LLM profiles
- quant rule version
- shortlist/final max settings

금지:
- API secret raw value 표시
- secret 브라우저 전송
- UI에서 모델/profile 무기록 즉시 변경

모델/profile 변경 UI는 Post-MVP 또는 개발자 설정으로 제한한다.

## 9. UX Principles

- 중요한 QA 경고 숨기지 않음
- AI claim에서 evidence로 이동 가능
- 최신/과거 judgment 구분
- 항상 run/snapshot context 표시
- PASS/WARN/FAIL 상태가 텍스트와 함께 명확

## 10. MVP UI Acceptance

- 1280px+ core flow 사용 가능
- Candidates는 내부 horizontal scroll 허용
- Final Judgment → Snapshot/Evidence/LLM execution 이동 가능
- QA FAIL가 PASS처럼 보이지 않음
- role별 model/reasoning/profile version 확인 가능
- secret value DOM/network에 노출되지 않음
