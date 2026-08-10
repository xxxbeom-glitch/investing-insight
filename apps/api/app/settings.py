"""Application settings — secrets from env, never hard-coded models."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        # Later file wins: .env.local overrides .env
        env_file=(
            str(REPO_ROOT / ".env"),
            str(REPO_ROOT / ".env.local"),
        ),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    supabase_url: str = Field(default="", alias="SUPABASE_URL")
    supabase_publishable_key: str = Field(default="", alias="SUPABASE_PUBLISHABLE_KEY")
    supabase_secret_key: str = Field(default="", alias="SUPABASE_SECRET_KEY")
    supabase_db_url: str = Field(default="", alias="SUPABASE_DB_URL")
    massive_api_key: str = Field(default="", alias="MASSIVE_API_KEY")
    openai_api_key: str = Field(default="", alias="OPENAI_API_KEY")
    sec_user_agent: str = Field(default="", alias="SEC_USER_AGENT")
    fred_api_key: str = Field(default="", alias="FRED_API_KEY")
    api_host: str = Field(default="127.0.0.1", alias="API_HOST")
    api_port: int = Field(default=8000, alias="API_PORT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    @property
    def has_supabase_api(self) -> bool:
        return bool(self.supabase_url and self.supabase_secret_key)

    @property
    def has_db_url(self) -> bool:
        return bool(self.supabase_db_url)


@lru_cache
def get_settings() -> Settings:
    return Settings()
