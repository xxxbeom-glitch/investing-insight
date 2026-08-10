from __future__ import annotations

import json
import uuid
from datetime import date
from pathlib import Path
from typing import Any

import psycopg
import yaml

REPO_ROOT = Path(__file__).resolve().parents[4]
RULES_PATH = REPO_ROOT / "config" / "industry_rules.v0.1.yaml"


def load_industry_rules(path: Path | None = None) -> dict[str, Any]:
    return yaml.safe_load((path or RULES_PATH).read_text(encoding="utf-8")) or {}


def classify_regime(latest: dict[str, dict[str, Any]], rules: dict[str, Any] | None = None) -> dict[str, Any]:
    rules = rules or load_industry_rules()
    rr = rules.get("regime") or {}
    unrate = (latest.get("labor") or {}).get("value")
    curve = (latest.get("yield_curve") or {}).get("value")
    if unrate is None:
        raise RuntimeError("regime requires labor (UNRATE) observation")

    expansion = rr.get("expansion") or {}
    late = rr.get("late_cycle") or {}
    contraction = rr.get("contraction") or {}

    if unrate >= float(contraction.get("unrate_min", 5.5)):
        regime = "contraction"
    elif curve is not None and curve < float(late.get("yield_curve_max", 0.0)) and unrate <= float(
        late.get("unrate_max", 5.5)
    ):
        regime = "late_cycle"
    elif unrate <= float(expansion.get("unrate_max", 5.5)) and (
        curve is None or curve >= float(expansion.get("yield_curve_min", 0.0))
    ):
        regime = "expansion"
    else:
        regime = "transition"

    as_of = max(
        (v["date"] for v in latest.values() if v.get("date")),
        default=date.today().isoformat(),
    )
    return {
        "regime": regime,
        "as_of": as_of,
        "inputs": latest,
        "rule_version": str(rules.get("regime_rules_version") or "market-regime-v0.1"),
    }


def persist_regime(conn: psycopg.Connection, classified: dict[str, Any]) -> str:
    regime_id = str(uuid.uuid4())
    with conn.cursor() as cur:
        cur.execute(
            """
            insert into market_regimes (regime_id, as_of, regime, inputs, rule_version)
            values (%s,%s,%s,%s::jsonb,%s)
            """,
            (
                regime_id,
                classified["as_of"],
                classified["regime"],
                json.dumps(classified["inputs"]),
                classified["rule_version"],
            ),
        )
    conn.commit()
    return regime_id
