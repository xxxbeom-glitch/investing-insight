from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml

_CONFIG_PATH = Path(__file__).resolve().parents[4] / "config" / "quant_rules.v0.1.yaml"


@dataclass(frozen=True)
class QuantRules:
    version: str
    weights: dict[str, float]
    shortlist_size: int
    neutral_score: float


def load_quant_rules(path: Path | None = None) -> QuantRules:
    raw: dict[str, Any] = yaml.safe_load((path or _CONFIG_PATH).read_text(encoding="utf-8")) or {}
    weights = {k: float(v) for k, v in (raw.get("weights") or {}).items()}
    required = {"growth", "quality", "cashflow", "health", "valuation", "momentum"}
    if set(weights) != required:
        raise ValueError(f"quant weights must be exactly {sorted(required)}, got {sorted(weights)}")
    total_w = sum(weights.values())
    if abs(total_w - 100.0) > 1e-6:
        raise ValueError(f"quant weights must sum to 100, got {total_w}")
    return QuantRules(
        version=str(raw.get("version") or "quant-rules-v0.1"),
        weights=weights,
        shortlist_size=int(raw.get("shortlist_size") or 20),
        neutral_score=float(raw.get("neutral_score") or 50),
    )
