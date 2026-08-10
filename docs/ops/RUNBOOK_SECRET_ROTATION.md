# Runbook — Secret Rotation

## Secrets (names only)
- `OPENAI_API_KEY`
- `MASSIVE_API_KEY`
- `SUPABASE_URL`
- `SUPABASE_PUBLISHABLE_KEY`
- `SUPABASE_SECRET_KEY` (server only)
- `SUPABASE_DB_URL` (server only)
- `SEC_USER_AGENT`

## Rules
- Store in `.env.local` or secret manager — never git.
- Never put secret keys in `NEXT_PUBLIC_*` or browser bundles.
- Never log secret values in audit, screenshots, or error payloads.

## Rotate
1. Issue new credential at provider.
2. Update secret store / `.env.local`.
3. Restart API process.
4. Run `python scripts/production_readiness_check.py` (must show `*_set=true` flags only).
5. Hit `/health/config` — confirm LLM profiles load.
6. Revoke old credential after verification.

## Compromise response
1. Revoke key immediately.
2. Rotate all server secrets.
3. Review `llm_executions` / provider dashboards for unexpected usage.
4. Record incident in ops log (no secret values).
