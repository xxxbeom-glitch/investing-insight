# 05. QA Loop & Audit Protocol

## 1. Core Rule

Cursor의 "완료" 문구는 PASS 증거가 아니다.

PASS는 사전에 정한 Acceptance Criteria와 실제 테스트 결과가 일치할 때만 부여한다.

## 2. Loop Engineering

모든 Layer는 동일한 루프를 사용한다.

```text
PLAN
↓
IMPLEMENT
↓
TEST
↓
QA
↓
FAIL? ─ YES → ROOT CAUSE → FIX → RETEST
↓ NO
PASS
↓
FREEZE
↓
NEXT LAYER
```

## 3. Issue Severity

### P0 — Integrity/Critical
예:
- future leakage
- wrong company mapped to data
- corrupted snapshot
- quant formula fundamentally wrong
- judgment cannot be traced to snapshot

처리: 다음 Layer 금지.

### P1 — Reliability/Blocking
예:
- required data silently missing
- exclusion rule leakage
- non-deterministic score
- unsupported LLM factual claims accepted

처리: 다음 Layer 금지.

### P2 — Important Improvement
예:
- 일부 ADR metadata quality 낮음
- classification ambiguity
- performance issue but system correct

처리: backlog 기록 후 진행 가능.

### P3 — UX/Minor
예:
- spacing
- non-critical label
- cosmetic issue

처리: backlog 가능.

## 4. ALL PASS Definition

`ALL PASS`는 warning이 0개라는 뜻이 아니다.

다음을 의미한다.
- P0 open = 0
- P1 open = 0
- 모든 Blocking Acceptance Criteria PASS
- P2/P3는 owner / impact / follow-up plan 기록
- test evidence 존재

## 5. QA Layers

### Mechanical QA — Code
- schema validation
- type
- null
- duplicates
- date ordering
- unit
- numeric bounds
- hash
- deterministic calculation
- uniqueness constraints

### Data QA — Code + Provider Cross-check when required
- source traceability
- known fixtures
- SEC facts consistency
- unavailable reason
- raw/normalized linkage

### Snapshot QA
- cutoff 이후 source 0건
- eligible record only
- content hash stable
- same input → same snapshot
- restatement/version handling

### Quant QA
- unit tests for formulas
- deterministic
- missing handling
- outlier handling
- rank monotonicity tests where applicable

### Research QA — LLM + Code
- evidence grounding
- numeric claim match
- FACT/inference separation
- bear case
- unsupported claim rejection

### End-to-End QA
- one research run completes from ingest to UI
- run state recoverable after failure
- audit trail complete

## 6. Audit Directory Contract

각 Layer는 아래 구조를 가진다.

```text
audit/mvp/LXX_layer_name/
├─ PLAN.md
├─ IMPLEMENTATION.md
├─ TEST_RESULTS.md
├─ QA_REPORT.md
├─ CHANGELOG.md
├─ OPEN_ISSUES.md
└─ HANDOFF.md
```

## 7. Required Layer Metadata

각 문서에는 최소:
- layer_id
- spec_version
- started_at
- completed_at
- status
- commit_hash
- previous_layer_commit
- files_changed
- commands_run
- acceptance_criteria
- test evidence
- P0/P1/P2/P3 issues

를 기록한다.

## 8. Freeze Rule

Layer PASS 후:
1. tests 재실행
2. audit 문서 업데이트
3. git commit
4. commit hash를 HANDOFF에 기록
5. 다음 Layer 시작

PASS Layer를 수정해야 한다면:
- 이전 audit를 수정하지 않는다.
- CHANGELOG에 regression reason 기록
- 영향받는 Layer QA를 다시 실행

## 9. MVP Freeze Rule

MVP ALL PASS 후:
- 전체 test suite 실행
- DB migration checksum 기록
- config version 기록
- quant rule version 기록
- prompt version 기록
- code commit hash 기록
- Git tag 생성 예: `mvp-v0.1-pass`
- `MVP_HANDOFF.md` 생성

그 후 Post-MVP 개발 중단.

## 10. External Review Package

외부 검증자가 받아야 할 핵심:
- 전체 설계 버전
- 최종 git commit/tag
- migration 목록
- `.env.example` (secret 제외)
- test 실행 방법
- audit 폴더 전체
- known issues
- sample research run id
- snapshot id
- selected judgment ids
- 재현 방법
