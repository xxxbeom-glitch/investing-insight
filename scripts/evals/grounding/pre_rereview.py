#!/usr/bin/env python3
"""One verification pass before M03/rereview. Does not mutate GO/tag/cron or code."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

HERE = Path(__file__).resolve().parent
REPO = HERE.parents[2]


def _python() -> str:
    win = REPO / "apps" / "api" / ".venv" / "Scripts" / "python.exe"
    if win.is_file():
        return str(win)
    return sys.executable


def _npm() -> str:
    for name in ("npm.cmd", "npm.exe", "npm"):
        found = shutil.which(name)
        if found:
            return found
    raise FileNotFoundError("npm not found on PATH")


def steps(*, llm: bool) -> list[tuple[str, list[str], Path]]:
    py = _python()
    out: list[tuple[str, list[str], Path]] = [
        ("pytest", [py, "-m", "pytest", "tests", "-q"], REPO),
        ("secret_scan", [py, str(REPO / "scripts" / "secret_scan.py")], REPO),
        ("web_build", [_npm(), "run", "build"], REPO / "apps" / "web"),
        (
            "grounding_replay",
            [py, str(HERE / "runner.py"), "--replay-only", "--out-dir", str(HERE / "out")],
            REPO,
        ),
    ]
    if llm:
        out.append(
            (
                "grounding_llm",
                [py, str(HERE / "runner.py"), "--llm", "--out-dir", str(HERE / "out")],
                REPO,
            )
        )
    return out


def _clean_web_next() -> None:
    nxt = REPO / "apps" / "web" / ".next"
    if nxt.is_dir():
        shutil.rmtree(nxt, ignore_errors=True)


def run_step(name: str, cmd: list[str], cwd: Path) -> dict[str, Any]:
    if name == "web_build":
        _clean_web_next()
    try:
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=False,
        )
    except FileNotFoundError as exc:
        return {
            "name": name,
            "ok": False,
            "exit_code": 127,
            "cmd": cmd,
            "stdout_tail": "",
            "stderr_tail": str(exc)[:1000],
        }
    return {
        "name": name,
        "ok": proc.returncode == 0,
        "exit_code": proc.returncode,
        "cmd": cmd,
        "stdout_tail": (proc.stdout or "")[-2000:],
        "stderr_tail": (proc.stderr or "")[-1000:],
    }


def run(*, llm: bool = True) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    ok = True
    for name, cmd, cwd in steps(llm=llm):
        row = run_step(name, cmd, cwd)
        results.append(row)
        if not row["ok"]:
            ok = False
            break
    report_json = HERE / "out" / "report.json"
    grounding: dict[str, Any] | None = None
    if report_json.is_file():
        grounding = json.loads(report_json.read_text(encoding="utf-8"))
        if grounding.get("ok") is False:
            ok = False
    summary = {
        "ok": ok,
        "exit_code": 0 if ok else 1,
        "steps": [{"name": r["name"], "ok": r["ok"], "exit_code": r["exit_code"]} for r in results],
        "failed_step": next((r["name"] for r in results if not r["ok"]), None),
        "grounding_report": str(report_json) if report_json.is_file() else None,
        "fp_count": int((((grounding or {}).get("llm") or {}).get("matrix") or {}).get("FP") or 0),
        "fp_fingerprint": ((grounding or {}).get("llm") or {}).get("fp_fingerprint"),
        "scheduler_enable_allowed": False,
        "go_nogo_unchanged": True,
        "results": results,
    }
    out_dir = HERE / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "pre_rereview.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    return summary


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--replay-only", action="store_true", help="Skip LLM red-team (not sufficient for rereview)")
    args = p.parse_args()
    summary = run(llm=not args.replay_only)
    public = {k: v for k, v in summary.items() if k != "results"}
    public["failed_detail"] = None
    if not summary["ok"]:
        failed = next((r for r in summary["results"] if not r["ok"]), None)
        if failed:
            public["failed_detail"] = {
                "name": failed["name"],
                "exit_code": failed["exit_code"],
                "stdout_tail": failed["stdout_tail"][-500:],
            }
    print(json.dumps(public, ensure_ascii=False, indent=2))
    return int(summary["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
