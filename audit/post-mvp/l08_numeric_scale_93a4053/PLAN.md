# PLAN — L08 numeric unit scale 정합

- layer_id: l08_numeric_scale_93a4053
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-11T14:50:00+00:00
- status: PLAN
- previous_layer_commit: 93a4053
- head_at_start: 93a4053

## Goal

L08 `claim_check.py`가 packet raw 숫자와 claim의 billion/million 표기를 같은 factual value로 판정하게 한다. 틀린 scale/value는 FAIL. M03 schema는 유지. GO/tag/cron 금지.

## Confirmed cause (live AAPL `31835b24`)

| claim | packet `value` (string) |
|-------|-------------------------|
| Assets were $383.266 billion at 2026-06-27 | `383266000000` |
| Stockholders' equity was $107.520 billion at 2026-06-27 | `107520000000` |
| Reported NetIncomeLoss was $101.464 billion at 2026-06-27 | `101464000000` |

`claim_check`는 `_NUM_RE`로 `383.266`만 추출해 bag(`3.83266e+11`)과 비교 → `numeric_not_in_packet_evidence`.

## In Scope

- 재현 fixture + 단위 계약
- 공통 numeric scale 함수 (선택 A)
- L08 `claim_check` 접속
- M03 `claim_support`는 **같은 숫자 계약만** 공유 (schema/operator 계약 불변)
- AAPL biweekly 1회 재실행
- deterministic tests. LLM Red-Team 확장 없음

## Out of Scope

GO / tag / cron / PITR 위조 / hosted / Optional / M03 claim schema / gate 완화 / failed_jobs triage / Docker CI / P2 backlog

## Alignment choice

**A. 공통 numeric normalization 함수만 공유.**  
L08는 bag-of-magnitudes, M03는 field/equals/value. 합치지 않음.

## Unit contract (최소)

Supported claim absolute units: none (raw), `million(s)`/`M`, `billion(s)`/`B`.  
`$` prefix, thousands `,`, `-` sign, decimals.  
`%` ≠ absolute. ISO date ≠ quantity. Glued non-unit letter (`81.32A`) ≠ quantity.  
Unsupported units fail-closed.

Match: `places==0` → exact `evidence == mantissa * scale`.  
`places>=1` → `|evidence - mantissa*scale| <= 0.5 * 10^(-places) * scale`.

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | raw 383266000000 + `$383.266 billion` → L08 no numeric fail | yes |
| AC-2 | `$384.266 billion` / `$383.266 million` / `383.266%` → FAIL | yes |
| AC-3 | 날짜·다른 evidence 숫자 우회 FAIL | yes |
| AC-4 | M03 operator/leftover/81.32A/100.5B fail-closed 유지 | yes |
| AC-5 | pytest / secret scans / web build / grounding self-QA PASS | yes |
| AC-6 | biweekly 1건 Research QA PASS. 아니면 STOP | yes |
| AC-7 | GO/tag/cron/Optional 변경 없음 | yes |

## Expected Files

- `apps/api/app/research/numeric_scale.py`
- `apps/api/app/research/claim_check.py`
- `apps/api/app/agents/claim_support.py` (numeric span only)
- `tests/unit/test_numeric_scale.py`
- `tests/unit/test_claim_check.py`
- `tests/unit/test_l08_m03_numeric_contract.py`
- `audit/post-mvp/l08_numeric_scale_93a4053/`

## Tests to Write First

AAPL 6건 PASS fixture, wrong scale/value/percent FAIL, date/cross-value FAIL, M03 `value was $383.266 billion` SUPPORTED + `close is 100.5B` still FAIL.

## Risks

- B/M 약어가 기존 leftover 공격을 SUPPORTED로 바꾸면 안 됨 (`100.5B` vs close 100.5는 다른 값 → 계속 FAIL)
- 0-decimal `383 billion`을 round로 통과시키면 안 됨 → exact only
- AAPL live가 단위 외 이유로 FAIL이면 범위 확대 금지, STOP
