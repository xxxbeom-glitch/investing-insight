from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_PROFILE_PATH = REPO_ROOT / "config" / "llm_profiles.v0.1.yaml"
REQUIRED_ROLES = ("company_research", "research_qa", "final_judgment")
ALLOWED_EFFORTS = {"none", "minimal", "low", "medium", "high", "xhigh"}


class RoleProfile(BaseModel):
    model: str = Field(min_length=1)
    reasoning_effort: str = Field(min_length=1)

    @field_validator("reasoning_effort")
    @classmethod
    def effort_ok(cls, v: str) -> str:
        if v not in ALLOWED_EFFORTS:
            raise ValueError(f"reasoning_effort must be one of {sorted(ALLOWED_EFFORTS)}")
        return v


class LlmProfiles(BaseModel):
    version: str
    provider: str = "openai"
    api: str = "responses"
    company_research: RoleProfile
    research_qa: RoleProfile
    final_judgment: RoleProfile


def load_llm_profiles(path: Path | None = None) -> LlmProfiles:
    profile_path = path or DEFAULT_PROFILE_PATH
    raw = yaml.safe_load(profile_path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("llm profile root must be a mapping")
    profiles = LlmProfiles.model_validate(raw)
    for role in REQUIRED_ROLES:
        if getattr(profiles, role).model.strip() == "":
            raise ValueError(f"{role}.model is empty")
    return profiles


def profiles_as_dict(profiles: LlmProfiles) -> dict[str, Any]:
    return profiles.model_dump()
