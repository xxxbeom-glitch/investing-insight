# 05. QA Loop & Audit Protocol

## 1. Core Rule

Cursor의 "완료"는 PASS 증거가 아니다.

PASS는 Acceptance Criteria + 실제 test/audit evidence로만 부여한다.

## 2. Loop Engineering

```text
PLAN
↓
IMPLEMENT
↓
TEST
↓
QA
↓
FAIL? → ROOT CAUSE → FIX → REGRESSION TEST → RETEST
↓ PASS
FREEZE
↓
NEXT LAYER
```

## 3. Issue Severity

### P0 — Integrity/Critical
- future leakage
- wrong company/data mapping
- corrupted snapshot
- secret exposure
- fundamentally wrong quant formula
- immutable judgment 변경

다음 Layer 금지.

### P1 — Reliability/Blocking
- required data silently missing
- excluded securities leakage
- non-deterministic score
- unsupported LLM factual claim accepted
- wrong LLM profile silently used
- model failure silently fallback

다음 Layer 금지.

### P2 — Important Improvement
- 일부 ADR metadata ambiguity
- non-critical classification ambiguity
- 성능/비용 최적화 여지

Backlog 후 진행 가능.

### P3 — UX/Minor
- cosmetic / non-critical labels

## 4. ALL PASS Definition

- P0 open = 0
- P1 open = 0
- 모든 Blocking Criteria PASS
- P2/P3 owner/impact/follow-up 기록
- test evidence 존재

Warning 0을 뜻하지 않는다.

## 5. QA Layers

### Mechanical QA — Code
- schema/type/null/duplicate
- date ordering
- unit/numeric bounds
- hash/uniqueness
- deterministic calculation

### Secret/Config QA
- `.env.local` Git 제외
- `.env.example`에 secret value 0
- Supabase secret server-only
- OpenAI/Massive key browser bundle 0
- LLM model/effort config hard-code 금지
- config version present

### Provider QA
- API failure silent success 금지
- retry/backoff
- SEC User-Agent present
- SEC rate limiter compliant
- raw response traceable

### Data QA
- source traceability
- known fixtures
- raw/normalized linkage
- unavailable reason

### Snapshot QA
- cutoff 이후 source 0
- eligible only
- same input/cutoff → stable content hash
- later restatement가 old snapshot 변경 0

### Quant QA
- formula unit tests
- deterministic
- missing/outlier handling
- rank tests

### Research Packet QA
- snapshot-eligible evidence only
- schema valid
- numeric fact evidence mapping
- input hash stable

### LLM Execution QA
- requested profile == executed profile
- model/reasoning/prompt/profile version recorded
- no silent fallback
- schema validation
- failure/retry traceable

### Research QA
- evidence grounding
- numeric claim match
- FACT/inference separation
- bear case
- unsupported claim rejection

### Final Judgment QA
- QA FAIL source research → SELECTED 금지
- no new unsupported fact
- risk/bear/invalidation required
- immutable insert only

### End-to-End QA
- ingest→snapshot→quant→research→QA→judgment→UI 완료
- failure recovery
- audit trail complete

## 6. Audit Directory Contract

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

- layer_id
- spec_version
- started_at/completed_at
- status
- commit_hash/previous commit
- files_changed
- commands_run
- config versions
- acceptance criteria/evidence
- P0/P1/P2/P3 issues

LLM layer는 추가:
- llm_profile_version
- role/model/reasoning
- prompt/schema version
- input/output hashes

## 8. Freeze Rule

PASS 후:
1. 관련 tests 재실행
2. audit 문서 최신화
3. git commit
4. hash 기록
5. 다음 Layer

이미 PASS한 Layer를 수정하면 regression reason과 영향 Layer 재QA가 필요하다.

## 9. MVP Freeze Rule

MVP ALL PASS 후:
- full suite
- DB migration checksum
- provider policy version
- quant rule version
- prompt bundle version
- llm profile version
- schema versions
- commit hash
- Git tag `mvp-v0.1-pass`
- `MVP_HANDOFF.md`

그 후 중단.

## 10. External Review Package

- spec version
- git tag/commit
- migrations
- `.env.example` only
- versioned configs
- schema contracts
- test commands/results
- audit folders
- known issues
- representative run/snapshot/judgment IDs
- reproduction steps

실제 secret은 절대 포함하지 않는다.
