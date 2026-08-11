# PLAN — L08 English month-day dates are not quantities

- layer_id: l08_english_date_9e94983
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-11T21:25:00+00:00
- status: PLAN
- previous_layer_commit: 9e94983

## Goal

Live AAPL `bac5e73f` FAIL 20건은 billion이 아니라 `June 27, 2026` / `July 9, 2026` 조각(`27`,`9`,`2026`)이었다. 이 표현을 ISO date와 같이 non-quantity로 제외한다. 게이트 완화 금지. GO/tag/cron 금지.

## In Scope

- `numeric_scale.iter_quantities` date spans에 month-name dates 추가
- live 문장 fixture + 회귀 (month 없는 `2026`/`27`은 계속 FAIL)
- AAPL biweekly 1회
- deterministic tests only (LLM Red-Team 확장 없음)

## Out of Scope

GO / tag / cron / hosted / Optional / M03 schema / 모든 세계 날짜 형식

## Contract (최소, live가 쓴 것)

```
MonthName D, YYYY
MonthName DD, YYYY
```
Full names + 흔한 약어(Jan, Sept). 서수 `1st` optional. ISO `YYYY-MM-DD` 유지.

## Acceptance

| ID | Criterion |
|----|-----------|
| AC-1 | `383,266,000,000 at June 27, 2026` → L08 numeric fail 없음 |
| AC-2 | `316.22 on July 9, 2026` → 316.22만 quantity |
| AC-3 | `Assets were 2026` / `Assets were 27` 계속 FAIL |
| AC-4 | billion/raw·%·100.5B 회귀 유지 |
| AC-5 | pytest / scans / build / grounding FP=0 |
| AC-6 | biweekly 1건 Research QA PASS. 아니면 새 원인 보고 후 같은 L08 경로만 최소 수정 |
| AC-7 | GO/tag/cron 불변 |
