#!/usr/bin/env python3
"""Ensure client/web source does not reference server-only secret env names."""

from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
WEB = REPO_ROOT / "apps" / "web"
FORBIDDEN = [
    "SUPABASE_SECRET_KEY",
    "OPENAI_API_KEY",
    "MASSIVE_API_KEY",
    "SUPABASE_DB_URL",
]


def main() -> int:
    if not WEB.exists():
        print("web dir missing — skip")
        return 0
    hits: list[str] = []
    for path in WEB.rglob("*"):
        if path.is_dir():
            continue
        if "node_modules" in path.parts or ".next" in path.parts:
            continue
        if path.suffix.lower() not in {".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs", ".json", ".md"}:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        for token in FORBIDDEN:
            if token in text:
                hits.append(f"{path.relative_to(REPO_ROOT)}: {token}")
    if hits:
        print("CLIENT SECRET REF FAIL")
        for h in hits:
            print(h)
        return 1
    print("CLIENT SECRET REF PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
