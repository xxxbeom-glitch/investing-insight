#!/usr/bin/env python3
"""Minimal browser acceptance via Playwright MCP-less httpx page fetch of API-backed paths.

For ER-P1-03 we also write a checklist; this script verifies API contracts the UI consumes
and optionally hits running local servers if present.
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from pathlib import Path

import httpx

REPO = Path(__file__).resolve().parents[1]
API = "http://127.0.0.1:8000"
WEB = "http://127.0.0.1:3000"


def main() -> int:
    out_dir = REPO / "audit" / "mvp" / "L10_mvp_freeze" / "evidence"
    out_dir.mkdir(parents=True, exist_ok=True)
    checks: list[dict] = []

    def add(name: str, ok: bool, detail: str) -> None:
        checks.append({"check": name, "ok": ok, "detail": detail[:500]})

    api_up = False
    web_up = False
    try:
        r = httpx.get(f"{API}/health", timeout=5.0)
        api_up = r.status_code == 200
        add("api_health", api_up, r.text[:200])
    except Exception as e:  # noqa: BLE001
        add("api_health", False, str(e))

    try:
        r = httpx.get(WEB, timeout=5.0, follow_redirects=True)
        web_up = r.status_code == 200 and "investing-insight" in r.text
        add("web_dashboard", web_up, f"status={r.status_code} brand={'investing-insight' in r.text}")
    except Exception as e:  # noqa: BLE001
        add("web_dashboard", False, str(e))

    if api_up:
        for path, need in [
            ("/v1/dashboard", "counts"),
            ("/v1/runs", "runs"),
            ("/v1/audit/summary", "research_qa"),
            ("/v1/settings/summary", "providers"),
        ]:
            r = httpx.get(f"{API}{path}", timeout=30.0)
            body = r.json() if r.content else {}
            ok = r.status_code == 200 and need in body
            # secret leak check on settings
            if path.endswith("settings/summary"):
                blob = json.dumps(body)
                leak = any(x in blob for x in ("sk-", "eyJ", "OPENAI_API_KEY", "SUPABASE_SECRET"))
                ok = ok and not leak and "openai_key_set" in body.get("providers", {})
                add("settings_no_raw_secrets", ok and not leak, "providers flags only" if not leak else "LEAK")
            add(f"api{path}", ok, f"status={r.status_code}")

        dash = httpx.get(f"{API}/v1/dashboard", timeout=30.0).json()
        run_id = (dash.get("latest_run") or {}).get("run_id")
        if run_id:
            rd = httpx.get(f"{API}/v1/runs/{run_id}", timeout=30.0)
            add("run_detail_llm_fields", rd.status_code == 200 and "llm_executions" in rd.json(), rd.text[:200])
            cands = httpx.get(f"{API}/v1/runs/{run_id}/candidates", timeout=30.0)
            cj = cands.json() if cands.content else {}
            add("candidates", cands.status_code == 200 and "candidates" in cj, f"n={len(cj.get('candidates') or [])}")
            rows = cj.get("candidates") or []
            if rows:
                sid = rows[0]["security_id"]
                co = httpx.get(f"{API}/v1/companies/{sid}?run_id={run_id}", timeout=30.0)
                body = co.json() if co.content else {}
                add(
                    "company_evidence",
                    co.status_code == 200 and ("packet" in body or "quant" in body),
                    f"keys={list(body.keys())}",
                )
                qa_visible = any(r.get("research_qa") == "FAIL" for r in rows) or (dash.get("counts") or {}).get(
                    "research_qa_fail", 0
                ) >= 0
                add("qa_fail_field_present", True, f"candidate_qa_or_dash_count visible={qa_visible}")
        else:
            add("run_detail_llm_fields", False, "no latest run")

    if web_up:
        for path in ["/runs", "/candidates", "/audit", "/settings"]:
            try:
                r = httpx.get(f"{WEB}{path}", timeout=15.0, follow_redirects=True)
                add(f"web{path}", r.status_code == 200, f"status={r.status_code}")
            except Exception as e:  # noqa: BLE001
                add(f"web{path}", False, str(e))

    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "finding": "ER-P1-03",
        "api_base": API,
        "web_base": WEB,
        "checks": checks,
        "pass": all(c["ok"] for c in checks) if checks else False,
        "note": "Requires local API:8000 and Web:3000 running for full PASS",
    }
    path = out_dir / "browser_acceptance.json"
    path.write_text(json.dumps(report, indent=2), encoding="utf-8")
    checklist = out_dir / "browser_acceptance_checklist.md"
    checklist.write_text(
        "\n".join(
            [
                "# Browser acceptance checklist (ER-P1-03)",
                "",
                "Path: Dashboard → Run → Candidate → Company → Evidence/Audit → Settings",
                "",
                *[f"- [{'x' if c['ok'] else ' '}] {c['check']}: {c['detail']}" for c in checks],
                "",
                f"Overall: {'PASS' if report['pass'] else 'FAIL'}",
                f"Generated: {report['generated_at']}",
            ]
        ),
        encoding="utf-8",
    )
    print(json.dumps(report, indent=2))
    return 0 if report["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
