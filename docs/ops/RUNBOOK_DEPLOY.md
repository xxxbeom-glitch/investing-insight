# Hosted PC Web + API (M01)

## Scope
Package FastAPI + Next.js for hosted PC Web. Reverse-proxy provides access control.
Do **not** enable cloud schedulers until `supabase_pitr_confirmation.md` contains `CONFIRMED`.

## Local-prod style
```text
# from repo root
docker compose -f deploy/docker-compose.yml build
docker compose -f deploy/docker-compose.yml up api
# web (host machine or separate container):
cd apps/web
$env:API_BASE_URL="http://127.0.0.1:8000"
npm run build
npm run start
```

## Access control
- Bind API to private network / reverse proxy only.
- Require operator auth at proxy (Basic Auth, SSO, or VPN). App has no public anonymous product surface by design.
- Never expose `SUPABASE_SECRET_KEY` / `SUPABASE_DB_URL` / provider keys to the browser.
- Set `WEB_ORIGIN` / CORS to the hosted web origin only.

## Secrets
Inject via host env or secret store into the API container. Do not bake `.env.local` into images.

## Health
- `GET /health`, `/health/db`, `/health/config`
- Ops: `GET /v1/ops/health` and PC Web `/ops`
