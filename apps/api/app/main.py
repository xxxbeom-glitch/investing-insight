from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.config_registry import list_config_versions
from app.db import check_supabase_connection
from app.llm_profiles import load_llm_profiles, profiles_as_dict
from app.logging_setup import configure_logging, get_logger
from app.settings import get_settings

settings = get_settings()
configure_logging(settings.log_level)
log = get_logger("api")

from app.reads import router as reads_router

app = FastAPI(title="investing-insight-api", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(reads_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "service": "investing-insight-api"}


@app.get("/health/db")
def health_db() -> dict:
    if not settings.has_supabase_api:
        raise HTTPException(status_code=503, detail="Supabase API credentials missing")
    try:
        result = check_supabase_connection(settings)
        return {"status": "ok", "supabase": result}
    except Exception as exc:  # noqa: BLE001
        log.error("health_db_failed", error=str(exc)[:300])
        raise HTTPException(status_code=503, detail="supabase connection failed") from exc


@app.get("/health/config")
def health_config() -> dict:
    try:
        profiles = load_llm_profiles()
        registry = list_config_versions()
        return {
            "status": "ok",
            "llm_profile_version": profiles.version,
            "llm_profiles": profiles_as_dict(profiles),
            "registry": registry,
        }
    except Exception as exc:  # noqa: BLE001
        raise HTTPException(status_code=500, detail=f"config invalid: {exc}") from exc
