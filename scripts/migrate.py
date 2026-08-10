#!/usr/bin/env python3
"""Apply SQL migrations with psycopg when SUPABASE_DB_URL is set."""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

from dotenv import load_dotenv

REPO_ROOT = Path(__file__).resolve().parents[1]
MIGRATIONS = REPO_ROOT / "migrations"


def load_env() -> None:
    load_dotenv(REPO_ROOT / ".env.local")
    load_dotenv(REPO_ROOT / ".env")


def list_migrations() -> list[Path]:
    return sorted(MIGRATIONS.glob("*.sql"))


def ensure_table(conn) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            create table if not exists public.schema_migrations (
              id text primary key,
              applied_at timestamptz not null default now()
            );
            """
        )
    conn.commit()


def applied_ids(conn) -> set[str]:
    with conn.cursor() as cur:
        cur.execute("select id from public.schema_migrations")
        return {row[0] for row in cur.fetchall()}


def apply(conn, path: Path) -> None:
    sql = path.read_text(encoding="utf-8")
    with conn.cursor() as cur:
        cur.execute(sql)
        cur.execute(
            "insert into public.schema_migrations (id) values (%s) on conflict (id) do nothing",
            (path.name,),
        )
    conn.commit()
    print(f"applied {path.name}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="List migrations only")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    load_env()
    files = list_migrations()
    if not files:
        print("No migrations found", file=sys.stderr)
        return 1
    if args.check or args.dry_run:
        for f in files:
            print(f.name)
        return 0

    db_url = os.getenv("SUPABASE_DB_URL", "").strip()
    if not db_url:
        print(
            "SUPABASE_DB_URL missing — cannot apply SQL. "
            "Use Supabase Dashboard SQL or set connection string.",
            file=sys.stderr,
        )
        return 2

    import psycopg

    with psycopg.connect(db_url) as conn:
        ensure_table(conn)
        done = applied_ids(conn)
        for path in files:
            if path.name in done:
                print(f"skip {path.name}")
                continue
            apply(conn, path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
