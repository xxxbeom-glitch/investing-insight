#!/usr/bin/env python3
"""Grounding eval harness. Standalone. Does not change GO/NO-GO/tags."""

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

from app.agents.claim_support import claim_is_supported, factual_payload  # noqa: E402

import compare  # noqa: E402
import judge as judge_mod  # noqa: E402
import redteam  # noqa: E402
from client import create_client  # noqa: E402

FIXTURES = HERE / "fixtures"
EVIDENCE_DIR = FIXTURES / "evidence"
SEED_PATH = FIXTURES / "attacks" / "seed.json"
RULES_PATH = FIXTURES / "rules" / "grounding_spec.short.md"
CONFIG_PATH = REPO / "config" / "evals" / "grounding.yaml"
LLM_EVIDENCE_IDS = ("regime", "daily_price", "assessment")


def load_config(path: Path = CONFIG_PATH) -> dict[str, Any]:
    raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    if not isinstance(raw, dict):
        raise ValueError("grounding.yaml must be a mapping")
    return raw


def load_evidence() -> dict[str, dict[str, Any]]:
    out: dict[str, dict[str, Any]] = {}
    for path in sorted(EVIDENCE_DIR.glob("*.json")):
        blob = json.loads(path.read_text(encoding="utf-8"))
        eid = str(blob.get("id") or path.stem)
        item = blob.get("item")
        if not isinstance(item, dict):
            raise ValueError(f"evidence {path.name} missing item")
        out[eid] = item
    return out


def load_seed(evidence: dict[str, dict[str, Any]]) -> list[dict[str, Any]]:
    rows = json.loads(SEED_PATH.read_text(encoding="utf-8"))
    resolved: list[dict[str, Any]] = []
    for row in rows:
        ref = str(row.get("evidence_ref") or "")
        item = evidence.get(ref)
        if item is None:
            raise ValueError(f"seed {row.get('id')}: unknown evidence_ref {ref}")
        resolved.append({**row, "evidence_item": item})
    return resolved


def load_rules() -> str:
    return RULES_PATH.read_text(encoding="utf-8")


def replay_seed(seed: list[dict[str, Any]]) -> dict[str, Any]:
    mismatches: list[dict[str, Any]] = []
    rows: list[dict[str, Any]] = []
    for item in seed:
        text = str(item["claim"])
        eid = str(item["evidence_id"])
        evidence = [item["evidence_item"]]
        actual = compare.gate_label(claim_is_supported(text, eid, evidence))
        expected = str(item["expected_gate"]).upper()
        ok = actual == expected
        row = {
            "id": item.get("id"),
            "claim": text,
            "evidence_id": eid,
            "expected_gate": expected,
            "gate_actual": actual,
            "ok": ok,
            "attack_class": item.get("attack_class"),
            "source": item.get("source"),
        }
        rows.append(row)
        if not ok:
            mismatches.append(row)
    return {
        "passed": len(rows) - len(mismatches),
        "failed": len(mismatches),
        "total": len(rows),
        "mismatches": mismatches,
        "rows": rows,
    }


def _quotas(max_attacks: int, n_evidence: int) -> list[int]:
    if n_evidence <= 0 or max_attacks <= 0:
        return [0] * max(n_evidence, 0)
    base, rem = divmod(max_attacks, n_evidence)
    return [base + (1 if i < rem else 0) for i in range(n_evidence)]


def _known_attacks(seed: list[dict[str, Any]], evidence_id: str) -> list[str]:
    seen: set[str] = set()
    out: list[str] = []
    for row in seed:
        if str(row.get("evidence_id")) != evidence_id:
            continue
        if str(row.get("expected_gate")).upper() != compare.UNSUPPORTED:
            continue
        key = compare.normalize_claim(str(row.get("claim") or ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(str(row["claim"]))
    return out


def run_llm(
    *,
    cfg: dict[str, Any],
    seed: list[dict[str, Any]],
    evidence: dict[str, dict[str, Any]],
    rules: str,
    client: Any,
    max_attacks: int,
) -> dict[str, Any]:
    red_cfg = cfg.get("redteam") or {}
    judge_cfg = cfg.get("judge") or {}
    known_keys = {compare.claim_key(str(r["claim"]), str(r["evidence_id"])) for r in seed}
    generated = 0
    discarded = 0
    novel: list[dict[str, Any]] = []
    refs = [rid for rid in LLM_EVIDENCE_IDS if rid in evidence]
    for ref, quota in zip(refs, _quotas(max_attacks, len(refs))):
        item = evidence[ref]
        eid = str(item.get("evidence_id") or "")
        payload = factual_payload(item)
        attacks = redteam.generate_attacks(
            client,
            evidence_id=eid,
            factual_payload=payload,
            known_attacks=_known_attacks(seed, eid),
            max_new=quota,
            rules=rules,
            model=str(red_cfg.get("model") or ""),
            reasoning_effort=str(red_cfg.get("reasoning_effort") or "low"),
            max_output_tokens=int(red_cfg.get("max_output_tokens") or 800),
        )
        generated += len(attacks)
        for atk in attacks:
            key = compare.claim_key(atk["claim"], eid)
            if key in known_keys:
                discarded += 1
                continue
            known_keys.add(key)
            novel.append(
                {
                    "claim": atk["claim"],
                    "evidence_id": eid,
                    "evidence_ref": ref,
                    "attack_class": atk.get("attack_class"),
                    "factual_payload": payload,
                    "evidence_item": item,
                }
            )

    judged_rows: list[dict[str, Any]] = []
    false_positives: list[dict[str, Any]] = []
    gate_supported = 0
    judge_calls = 0
    for atk in novel:
        supported = claim_is_supported(atk["claim"], atk["evidence_id"], [atk["evidence_item"]])
        actual = compare.gate_label(supported)
        judge_expected = None
        judge_meta: dict[str, str] | None = None
        if actual == compare.SUPPORTED:
            gate_supported += 1
            judge_meta = judge_mod.judge_claim(
                client,
                evidence_id=atk["evidence_id"],
                factual_payload=atk["factual_payload"],
                claim=atk["claim"],
                rules=rules,
                model=str(judge_cfg.get("model") or ""),
                reasoning_effort=str(judge_cfg.get("reasoning_effort") or "low"),
                max_output_tokens=int(judge_cfg.get("max_output_tokens") or 220),
            )
            judge_calls += 1
            judge_expected = judge_meta["expected"]
        matrix = compare.classify(judge_expected=judge_expected, gate_actual=actual)
        row = {
            "claim": atk["claim"],
            "evidence_id": atk["evidence_id"],
            "attack_class": atk.get("attack_class"),
            "gate_actual": actual,
            "judge_expected": judge_expected,
            "judge_reason_code": (judge_meta or {}).get("reason_code"),
            "judge_reason": (judge_meta or {}).get("reason"),
            "matrix": matrix,
            "severity": compare.severity(matrix),
        }
        judged_rows.append(row)
        if matrix == "FP":
            false_positives.append(row)

    totals = compare.tally(judged_rows)
    return {
        "redteam_generated": generated,
        "redteam_discarded_duplicate": discarded,
        "redteam_kept_new": len(novel),
        "gate_supported": gate_supported,
        "judge_calls": judge_calls,
        "matrix": totals,
        "false_positives": false_positives,
        "fp_fingerprint": compare.fp_fingerprint(false_positives),
        "rows": judged_rows,
    }


def render_markdown(report: dict[str, Any]) -> str:
    replay = report.get("replay") or {}
    llm = report.get("llm")
    matrix = (llm or {}).get("matrix") or {}
    fps = (llm or {}).get("false_positives") or []
    lines = [
        "# Grounding eval",
        "",
        f"- status: {'FAIL' if not report.get('ok') else 'PASS'}",
        f"- mode: {report.get('mode')}",
        f"- replay passed/failed/total: {replay.get('passed')}/{replay.get('failed')}/{replay.get('total')}",
    ]
    if llm is None:
        lines.append("- llm: skipped")
    else:
        lines.extend(
            [
                f"- redteam generated/kept: {llm.get('redteam_generated')}/{llm.get('redteam_kept_new')}",
                f"- gate SUPPORTED: {llm.get('gate_supported')}",
                f"- judge calls: {llm.get('judge_calls')}",
                f"- FP/FN/TP/TN: {matrix.get('FP', 0)}/{matrix.get('FN', 0)}/{matrix.get('TP', 0)}/{matrix.get('TN', 0)}",
                f"- token usage: {json.dumps(report.get('token_usage') or {}, sort_keys=True)}",
            ]
        )
        if fps:
            lines.append("")
            lines.append("## False positives (FP / CRITICAL)")
            for row in fps:
                lines.append(
                    f"- FP / CRITICAL `{row.get('claim')}` ({row.get('evidence_id')}): "
                    f"gate={row.get('gate_actual')} judge={row.get('judge_expected')} — {row.get('judge_reason')}"
                )
    lines.append("")
    lines.append("Does not change GO/NO-GO, tags, cron, or candidate disposition.")
    lines.append("")
    return "\n".join(lines)


def write_reports(out_dir: Path, report: dict[str, Any]) -> tuple[Path, Path]:
    out_dir.mkdir(parents=True, exist_ok=True)
    json_path = out_dir / "report.json"
    md_path = out_dir / "report.md"
    json_path.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    md_path.write_text(render_markdown(report), encoding="utf-8")
    return json_path, md_path


def run(
    *,
    llm: bool = False,
    max_attacks: int | None = None,
    out_dir: Path | None = None,
    client: Any | None = None,
    config_path: Path = CONFIG_PATH,
) -> dict[str, Any]:
    cfg = load_config(config_path)
    evidence = load_evidence()
    seed = load_seed(evidence)
    replay = replay_seed(seed)
    ok = replay["failed"] == 0
    report: dict[str, Any] = {
        "ok": ok,
        "mode": "llm" if llm else "replay-only",
        "started_at": datetime.now(timezone.utc).isoformat(),
        "replay": {
            "passed": replay["passed"],
            "failed": replay["failed"],
            "total": replay["total"],
            "mismatches": replay["mismatches"],
        },
        "llm": None,
        "token_usage": None,
        "exit_code": 0 if ok else 1,
        "scheduler_enable_allowed": False,
        "go_nogo_unchanged": True,
    }
    if llm and ok:
        rules = load_rules()
        active = client or create_client(str(cfg.get("provider") or "openai"))
        cap = int(max_attacks if max_attacks is not None else cfg.get("max_attacks") or 20)
        llm_out = run_llm(
            cfg=cfg,
            seed=seed,
            evidence=evidence,
            rules=rules,
            client=active,
            max_attacks=cap,
        )
        report["llm"] = {
            k: v
            for k, v in llm_out.items()
            if k != "rows"
        }
        report["llm"]["rows"] = llm_out["rows"]
        usage = getattr(active, "usage_totals", None)
        if isinstance(usage, dict):
            report["token_usage"] = {
                "input_tokens": usage.get("input_tokens"),
                "output_tokens": usage.get("output_tokens"),
                "requests": usage.get("requests"),
            }
        fp = int((llm_out.get("matrix") or {}).get("FP") or 0)
        if fp >= 1:
            ok = False
        report["ok"] = ok
        report["exit_code"] = 0 if ok else 1
    dest = out_dir or (HERE / "out")
    json_path, md_path = write_reports(dest, report)
    report["report_json"] = str(json_path)
    report["report_md"] = str(md_path)
    return report


def main() -> int:
    p = argparse.ArgumentParser(description="Grounding eval (standalone). Default is replay-only.")
    p.add_argument("--llm", action="store_true", help="Run Red-Team + Judge after replay PASS")
    p.add_argument("--replay-only", action="store_true", help="Deterministic fixtures only (default)")
    p.add_argument("--max-attacks", type=int, default=None)
    p.add_argument("--out-dir", default="")
    args = p.parse_args()
    llm = bool(args.llm) and not args.replay_only
    out = Path(args.out_dir) if args.out_dir else HERE / "out"
    try:
        report = run(llm=llm, max_attacks=args.max_attacks, out_dir=out)
    except Exception as exc:  # noqa: BLE001
        print(json.dumps({"ok": False, "error": type(exc).__name__, "detail": str(exc)[:300]}))
        return 2
    summary = {
        "ok": report["ok"],
        "mode": report["mode"],
        "exit_code": report["exit_code"],
        "replay": report["replay"],
        "llm": None
        if report["llm"] is None
        else {
            "redteam_generated": report["llm"]["redteam_generated"],
            "redteam_kept_new": report["llm"]["redteam_kept_new"],
            "gate_supported": report["llm"]["gate_supported"],
            "judge_calls": report["llm"]["judge_calls"],
            "matrix": report["llm"]["matrix"],
            "false_positive_count": len(report["llm"]["false_positives"]),
        },
        "token_usage": report.get("token_usage"),
        "report_json": report.get("report_json"),
        "report_md": report.get("report_md"),
    }
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return int(report["exit_code"])


if __name__ == "__main__":
    raise SystemExit(main())
