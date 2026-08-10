# PLAN

- layer_id: L01
- layer_name: universe
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10
- status: PLAN
- previous_layer_commit: cdf3071

## Goal

NYSE/NASDAQ 투자 대상 registry를 Massive adapter + 분류 규칙 + identity로 정확히 구축한다.

## In Scope

- MarketDataProvider + Massive HTTP adapter (`api.massive.com`)
- companies / securities / universe_memberships / sources 스키마
- inclusion/exclusion 분류 (CS/ADRC 포함, ETF 등 제외)
- company_id / security_id deterministic UUID5
- raw payload hash + source 기록
- fixture 단위 테스트 + sample live ingest 스크립트

## Out of Scope

- 전체 시장 일별 OHLCV (L02)
- SEC facts (L03)
- Quant / LLM

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | Fixture에 XNYS·XNAS CS가 included | yes |
| AC-2 | Fixture ETF/ETN/PFD/WARRANT/REIT-name 등 exclusion leakage 0 | yes |
| AC-3 | Fixture ADRC included + is_adr true | yes |
| AC-4 | 동일 provider payload → duplicate identity 0 | yes |
| AC-5 | excluded 행에 exclusion_reason 존재 | yes |
| AC-6 | source raw_hash 저장·재현 | yes |
| AC-7 | Massive live sample (AAPL) fetch FAIL-closed (키 없으면 실패) | yes |

## Expected Files

- `apps/api/app/providers/**`
- `apps/api/app/universe/**`
- `migrations/0002_universe_identity.sql`
- `tests/unit/test_universe_*.py`
- `tests/fixtures/universe_tickers.json`
- `scripts/ingest_universe_sample.py`
- `audit/mvp/L01_universe/**`

## Tests to Write First

- classify include/exclude matrix
- identity stability / no duplicates
- raw hash
- massive client parse fixture (no network)
- optional live sample if MASSIVE_API_KEY set

## Risks

- REIT/BDC/SPAC이 type=CS로 오는 경우 → name/heuristic 보조 규칙
- Massive pagination 전체 ingest는 시간·쿼터 → sample + fixture로 Blocking, full ingest는 CLI 옵션

## Stop Conditions

- P0/P1 open이면 L02 금지
