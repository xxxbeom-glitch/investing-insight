# OPEN_ISSUES — M01

## P0
(none)

## P1
(none)

## P2
- M01-P2-01: Docker image build not yet evidenced in CI (local docker optional).
- M01-P2-02: Full-universe daily ingest cost/time not load-tested (default `--limit` sample).
- M01-P2-03: Production scheduler enable is a separate ops decision (intentionally blocked on Free lab).

## P3
- M01-P3-01: External pager/Slack alerting still deferred beyond `/ops` UI.
- M01-P3-02: Prefer native `pg_dump`/`supabase db dump` binaries when installed; current path uses psycopg COPY logical dump.
