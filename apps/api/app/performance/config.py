from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
DEFAULT_PATH = REPO_ROOT / "config" / "performance_rules.v0.2.yaml"


def load_performance_rules(path: Path | None = None) -> dict[str, Any]:
    raw = yaml.safe_load((path or DEFAULT_PATH).read_text(encoding="utf-8")) or {}
    if not raw.get("horizons"):
        raise ValueError("performance rules missing horizons")
    return raw
