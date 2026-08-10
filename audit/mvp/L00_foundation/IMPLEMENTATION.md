# IMPLEMENTATION

- layer_id: L00
- status: BLOCKED (waiting real Supabase)
- commit_hash: (see HANDOFF)

## What Changed

- FastAPI app: `/health`, `/health/db`, `/health/config`
- Next.js PC health dashboard calling API
- LLM profile loader + config registry
- SQL migration `0001_app_bootstrap.sql` + `scripts/migrate.py`
- audit generator / secret scan / client secret ref check
- pytest unit + integration

## Files Changed

- `apps/api/**`
- `apps/web/**`
- `migrations/0001_app_bootstrap.sql`
- `scripts/*.py`
- `tests/**`
- `pytest.ini`, `.env.example`, `README.md`
- `audit/mvp/L00_foundation/**`

## Commands Run

```text
pip install -r apps/api/requirements.txt
pytest tests -q
python scripts/secret_scan.py
python scripts/check_client_secrets.py
python scripts/migrate.py --check
npm run build (apps/web)
```

## Deviations from PLAN

- `SUPABASE_DB_URL` 미설정 → SQL apply는 재현 스크립트만 검증 (`--check`), 실 apply는 사용자 DB URI 필요
- `.env`의 `SUPABASE_URL`이 placeholder(`xxxxx.supabase.co`)라 `/health/db`는 Fail Closed 503

## Notes

- `.env` → `.env.local` 복사해 두었음 (로컬만, gitignore)
