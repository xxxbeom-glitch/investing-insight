"""Recorded production model capability registry. No substring heuristics."""

from __future__ import annotations

from pathlib import Path
from typing import AbstractSet

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
REGISTRY_REL = Path("config") / "llm_model_capabilities.yaml"


def load_recorded_model_capabilities(repo: Path | None = None) -> set[str]:
    """Load the recorded set generated from the production Responses client."""
    from app.research.openai_responses import ModelUnavailableError

    path = (repo or REPO_ROOT) / REGISTRY_REL
    if not path.is_file():
        raise ModelUnavailableError("model capability registry missing")
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    models = raw.get("models")
    if not isinstance(models, list) or not models:
        raise ModelUnavailableError("model capability registry empty")
    out = {str(m).strip() for m in models if str(m).strip()}
    if not out:
        raise ModelUnavailableError("model capability registry empty")
    return out


def resolve_against_registry(
    model: str,
    *,
    available: AbstractSet[str] | None = None,
    repo: Path | None = None,
) -> str:
    """Fail closed unless the exact requested name is in the recorded/production set."""
    from app.research.openai_responses import ModelUnavailableError

    name = (model or "").strip()
    if not name:
        raise ModelUnavailableError("empty model")
    allowed = set(available) if available is not None else load_recorded_model_capabilities(repo)
    if name not in allowed:
        raise ModelUnavailableError(f"unavailable model: {model}")
    return name
