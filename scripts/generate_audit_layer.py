#!/usr/bin/env python3
"""Generate audit/mvp/<layer_id>/ from templates."""

from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = REPO_ROOT / "audit" / "mvp" / "_templates"
REQUIRED = [
    "PLAN.md",
    "IMPLEMENTATION.md",
    "TEST_RESULTS.md",
    "QA_REPORT.md",
    "CHANGELOG.md",
    "OPEN_ISSUES.md",
    "HANDOFF.md",
]


def generate(layer_id: str, force: bool = False) -> Path:
    if not layer_id or "/" in layer_id or "\\" in layer_id:
        raise ValueError("invalid layer_id")
    dest = REPO_ROOT / "audit" / "mvp" / layer_id
    if dest.exists() and any(dest.iterdir()) and not force:
        raise FileExistsError(f"{dest} already exists (use --force)")
    dest.mkdir(parents=True, exist_ok=True)
    for name in REQUIRED:
        src = TEMPLATES / name
        if not src.exists():
            raise FileNotFoundError(src)
        target = dest / name
        if target.exists() and not force:
            continue
        shutil.copyfile(src, target)
    return dest


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("layer_id", help="e.g. L00_foundation")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    try:
        path = generate(args.layer_id, force=args.force)
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    print(path)
    for name in REQUIRED:
        print(name)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
