#!/usr/bin/env python3
"""Record grounding self-remediation attempts. Does not edit production code or GO/tag."""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "apps" / "api"))

from dotenv import load_dotenv

load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import yaml  # noqa: E402

import pre_rereview  # noqa: E402

STATE_PATH = HERE / "out" / "loop_state.json"
CONFIG_PATH = REPO / "config" / "evals" / "grounding.yaml"

# exit 0 = pass (FP=0, all steps ok) — Cursor may run M03 only if user asked
# exit 1 = FP/step fail, attempt < max, fingerprint changed — Cursor may fix grounding only
# exit 2 = stop (max attempts or same FP fingerprint) — report to human
PASS = 0
CONTINUE = 1
STOP = 2


def _max_attempts(path: Path = CONFIG_PATH) -> int:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    loop = raw.get("loop") or {}
    return int(loop.get("max_attempts") or 3)


def load_state() -> dict[str, Any]:
    if not STATE_PATH.is_file():
        return {"attempts": 0, "last_fp_fingerprint": None, "history": []}
    return json.loads(STATE_PATH.read_text(encoding="utf-8"))


def save_state(state: dict[str, Any]) -> None:
    STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    STATE_PATH.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def decide(*, attempts: int, max_attempts: int, prev_fp: str | None, new_fp: str | None, ok: bool) -> str:
    if ok:
        return "pass"
    if attempts >= max_attempts:
        return "stop_max"
    if new_fp and prev_fp and new_fp == prev_fp:
        return "stop_repeat"
    return "continue"


def run(*, llm: bool = True, verify_fn=None) -> dict[str, Any]:
    max_attempts = _max_attempts()
    state = load_state()
    attempts_before = int(state.get("attempts") or 0)
    if attempts_before >= max_attempts:
        result = {
            "ok": False,
            "action": "stop_max",
            "exit_code": STOP,
            "attempts": attempts_before,
            "max_attempts": max_attempts,
            "reason": "max_attempts already reached; not re-running",
            "read_report": str(HERE / "out" / "report.json"),
            "scheduler_enable_allowed": False,
            "go_nogo_unchanged": True,
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return result

    verify = verify_fn or pre_rereview.run
    summary = verify(llm=llm)
    attempts = attempts_before + 1
    new_fp = summary.get("fp_fingerprint") or None
    if int(summary.get("fp_count") or 0) == 0:
        new_fp = None
    prev_fp = state.get("last_fp_fingerprint")
    action = decide(
        attempts=attempts,
        max_attempts=max_attempts,
        prev_fp=prev_fp,
        new_fp=new_fp,
        ok=bool(summary.get("ok")),
    )
    state["attempts"] = attempts
    state["last_fp_fingerprint"] = new_fp
    state["last_action"] = action
    state["updated_at"] = datetime.now(timezone.utc).isoformat()
    hist = list(state.get("history") or [])
    hist.append(
        {
            "attempt": attempts,
            "ok": summary.get("ok"),
            "fp_count": summary.get("fp_count"),
            "fp_fingerprint": new_fp,
            "failed_step": summary.get("failed_step"),
            "action": action,
        }
    )
    state["history"] = hist
    if action == "pass":
        state["attempts"] = 0
        state["last_fp_fingerprint"] = None
    save_state(state)

    exit_code = PASS if action == "pass" else STOP if action.startswith("stop") else CONTINUE
    result = {
        "ok": action == "pass",
        "action": action,
        "exit_code": exit_code,
        "attempts": attempts,
        "max_attempts": max_attempts,
        "fp_count": summary.get("fp_count"),
        "fp_fingerprint": new_fp,
        "failed_step": summary.get("failed_step"),
        "read_report": str(HERE / "out" / "report.json"),
        "read_pre_rereview": str(HERE / "out" / "pre_rereview.json"),
        "fix_scope": ["apps/api/app/agents/claim_support.py", "tests/unit/test_er*.py", "scripts/evals/grounding/fixtures/"],
        "do_not": ["M03-M06 until pass", "GO/NO-GO", "tag", "cron", "schema change"],
        "scheduler_enable_allowed": False,
        "go_nogo_unchanged": True,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return result


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--reset", action="store_true", help="Clear loop_state.json")
    p.add_argument("--replay-only", action="store_true")
    args = p.parse_args()
    if args.reset:
        if STATE_PATH.is_file():
            STATE_PATH.unlink()
        print(json.dumps({"ok": True, "reset": True}))
        return 0
    result = run(llm=not args.replay_only)
    return int(result["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
