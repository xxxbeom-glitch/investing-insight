from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def load_schema(name: str) -> dict[str, Any]:
    path = Path(__file__).resolve().parents[4] / "packages" / "schemas" / name
    return json.loads(path.read_text(encoding="utf-8"))


def validate_against_schema(instance: dict[str, Any], schema: dict[str, Any]) -> None:
    """Minimal fail-closed validator for our draft-2020-12 schemas (no jsonschema dep)."""
    if schema.get("type") == "object" and not isinstance(instance, dict):
        raise ValueError("expected object")
    required = schema.get("required") or []
    missing = [k for k in required if k not in instance]
    if missing:
        raise ValueError(f"missing required keys: {missing}")
    props = schema.get("properties") or {}
    if schema.get("additionalProperties") is False:
        extra = [k for k in instance if k not in props]
        if extra:
            raise ValueError(f"additional properties not allowed: {extra}")
    for key, prop in props.items():
        if key not in instance:
            continue
        val = instance[key]
        if "const" in prop and val != prop["const"]:
            raise ValueError(f"{key} must be const {prop['const']!r}")
        t = prop.get("type")
        if t == "string" and not isinstance(val, str):
            raise ValueError(f"{key} must be string")
        if t == "object" and not isinstance(val, dict):
            raise ValueError(f"{key} must be object")
        if t == "array" and not isinstance(val, list):
            raise ValueError(f"{key} must be array")
        if t == "array" and "items" in prop:
            item_t = (prop["items"] or {}).get("type")
            for i, item in enumerate(val):
                if item_t == "string" and not isinstance(item, str):
                    raise ValueError(f"{key}[{i}] must be string")
                if item_t == "object" and not isinstance(item, dict):
                    raise ValueError(f"{key}[{i}] must be object")
