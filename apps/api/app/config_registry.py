"""Config version registry — non-secret versioned files under /config."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

REPO_ROOT = Path(__file__).resolve().parents[3]
CONFIG_DIR = REPO_ROOT / "config"


def list_config_versions(config_dir: Path | None = None) -> dict[str, Any]:
    root = config_dir or CONFIG_DIR
    items: list[dict[str, str]] = []
    for path in sorted(root.glob("*.yaml")):
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
        version = str(raw.get("version", "unknown"))
        items.append({"file": path.name, "version": version})
    return {"config_dir": str(root), "items": items}
