"""Supabase client helpers — secret key stays server-side."""

from __future__ import annotations

from typing import Any

from supabase import Client, create_client

from app.logging_setup import get_logger
from app.settings import Settings

log = get_logger("db")


def create_supabase_client(settings: Settings) -> Client:
    if not settings.has_supabase_api:
        raise RuntimeError("SUPABASE_URL and SUPABASE_SECRET_KEY are required")
    return create_client(settings.supabase_url, settings.supabase_secret_key)


def check_supabase_connection(settings: Settings) -> dict[str, Any]:
    """Prove API credentials reach Supabase PostgREST (fail closed)."""
    from urllib.parse import urlparse

    host = (urlparse(settings.supabase_url).hostname or "").lower()
    if not host or host.startswith("xxxxx.") or "example" in host:
        raise RuntimeError("SUPABASE_URL looks like a placeholder; set a real project URL")

    client = create_supabase_client(settings)
    try:
        # Prefer bootstrap table after migrations; fall back to probing PostgREST.
        result = client.table("app_bootstrap").select("id,key,value").limit(1).execute()
        return {
            "ok": True,
            "mode": "table",
            "rows": len(result.data or []),
        }
    except Exception as table_exc:  # noqa: BLE001 — surface provider errors
        msg = str(table_exc)
        # Relation missing still proves auth+network to PostgREST.
        if "Could not find the table" in msg or "PGRST" in msg or "42P01" in msg:
            return {
                "ok": True,
                "mode": "postgrest",
                "note": "connected; app_bootstrap missing until migrate",
                "detail": msg[:200],
            }
        log.error("supabase_health_failed", error=msg[:300])
        raise
