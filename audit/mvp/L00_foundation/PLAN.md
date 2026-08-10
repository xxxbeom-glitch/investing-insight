# PLAN

- layer_id: L00
- layer_name: foundation
- spec_version: investing-insight-spec-v1.6
- started_at: 2026-08-10
- status: PLAN
- previous_layer_commit: n/a (first layer)

## Goal

프로젝트 실행·Supabase DB 연결·secret/config 경계·test/audit 기반을 구축한다.

## In Scope

- `apps/web` (Next.js) health UI → API health 호출
- `apps/api` (FastAPI) `/health`, `/health/db`
- Supabase 클라이언트 연결 검증 (server-only secret)
- SQL migration 프레임워크 + 재현 스크립트
- `.env.example` / `.env.local` secret 경계
- `config/llm_profiles.v0.1.yaml` 로드·검증
- config version registry 헬퍼
- structured logging
- pytest 기반 unit/integration
- audit layer 디렉터리 generator 스크립트
- `packages/schemas` JSON Schema 존재 검증

## Out of Scope

- Massive/SEC/OpenAI 실호출 ingest
- Universe/Quant/Research
- 공개 배포·스케줄러·Firebase
- 모바일 UI

## Acceptance Criteria

| ID | Criterion | Testable? |
|----|-----------|-----------|
| AC-1 | `apps/api` clean install 후 `/health` → 200 `{status:ok}` | yes |
| AC-2 | `apps/web`가 API health를 호출해 성공 상태를 표시/반환 | yes |
| AC-3 | API `/health/db`가 Supabase 연결에 성공 (또는 명확한 FAIL) | yes |
| AC-4 | `scripts/migrate.py`로 migration up이 재현 가능 (DB URL 있을 때) | yes |
| AC-5 | `scripts/secret_scan.py`가 트래킹 파일에서 secret 패턴 0건 | yes |
| AC-6 | web 번들/클라이언트 코드에 `SUPABASE_SECRET`/`OPENAI`/`MASSIVE` 키 참조 0 | yes |
| AC-7 | LLM profile YAML 로드·필수 role/model/effort 검증 PASS | yes |
| AC-8 | `scripts/generate_audit_layer.py L00_foundation`이 7파일 생성 가능 | yes |

## Expected Files

- `apps/api/**`
- `apps/web/**`
- `migrations/*.sql`
- `scripts/migrate.py`, `generate_audit_layer.py`, `secret_scan.py`
- `tests/unit/**`, `tests/integration/**`
- `audit/mvp/L00_foundation/**`
- root `README` runbook 갱신

## Tests to Write First

- unit: llm profile load/validate
- unit: audit generator
- unit: secret scan on fixtures
- integration: health endpoints (api; db if credentials)

## Risks

- `.env`만 있고 DB connection string 없으면 SQL migrate 불가 → REST health로 연결 증명 + `SUPABASE_DB_URL` optional
- Supabase 프로젝트에 테이블 없으면 migrate 필수
- Next/FastAPI 버전 pin 필요

## Stop Conditions

- P0/P1 blocking으로 L00 PASS 불가 시 HANDOFF에 기록하고 사용자 개입 대기 (야간 자율 시 우회 가능한 P2만 backlog)
- secret이 커밋되면 즉시 중단·히스토리 정리 보고
