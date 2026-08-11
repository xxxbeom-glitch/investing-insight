from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml
from pydantic import BaseModel, Field, field_validator

from app.llm_profiles import ALLOWED_EFFORTS, RoleProfile

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PATH = REPO_ROOT / "config" / "llm_profiles.v0.2.yaml"

MULTIAGENT_ROLES = (
    "market_agent",
    "industry_agent",
    "company_agent",
    "event_agent",
    "research_agent",
    "research_qa_agent",
    "adversarial_agent",
    "final_selector_agent",
)


class MultiAgentProfiles(BaseModel):
    version: str
    provider: str = "openai"
    api: str = "responses"
    market_agent: RoleProfile
    industry_agent: RoleProfile
    company_agent: RoleProfile
    event_agent: RoleProfile
    research_agent: RoleProfile
    research_qa_agent: RoleProfile
    adversarial_agent: RoleProfile
    final_selector_agent: RoleProfile


def load_multiagent_profiles(path: Path | None = None) -> MultiAgentProfiles:
    raw = yaml.safe_load((path or DEFAULT_PATH).read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError("multiagent profile root must be a mapping")
    profiles = MultiAgentProfiles.model_validate(raw)
    for role in MULTIAGENT_ROLES:
        if getattr(profiles, role).model.strip() == "":
            raise ValueError(f"{role}.model is empty")
    return profiles
