#!/usr/bin/env python3
"""Fail if tracked text files look like they contain live secrets."""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

# High-confidence accidental secret shapes (not .env.example placeholders).
PATTERNS = [
    re.compile(r"sk-[A-Za-z0-9]{20,}"),
    re.compile(r"eyJ[A-Za-z0-9_-]{20,}\.[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT-like
]

SKIP_SUFFIX = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".ttf",
    ".woff",
    ".woff2",
    ".ico",
    ".pdf",
}


def tracked_files() -> list[Path]:
    out = subprocess.check_output(["git", "ls-files", "-z"], cwd=REPO_ROOT)
    paths = [Path(p) for p in out.decode("utf-8", errors="replace").split("\0") if p]
    return paths


def main() -> int:
    hits: list[str] = []
    for rel in tracked_files():
        if rel.suffix.lower() in SKIP_SUFFIX:
            continue
        if str(rel).replace("\\", "/").startswith("fonts/"):
            continue
        path = REPO_ROOT / rel
        try:
            text = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        for pat in PATTERNS:
            if pat.search(text):
                # Allow documentation that mentions pattern names only.
                if "sk-..." in text or "example" in text.lower() and "sk-" not in text:
                    continue
                hits.append(f"{rel}: matched {pat.pattern}")
                break
    if hits:
        print("SECRET SCAN FAIL")
        for h in hits:
            print(h)
        return 1
    print("SECRET SCAN PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
