from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

import psycopg

from app.agents.binding import bind_multi_agent_run, verify_frozen_context
from app.agents.evidence import load_evidence_bundle
from app.agents.final_gate import (
    approved_claim_catalog,
    evaluate_final_selector_gate,
    materialize_final_selector,
)
from app.agents.judgment_project import project_final_selector_to_judgment
from app.agents.profiles import load_multiagent_profiles
from app.agents.runner import (
    GateBlockedError,
    build_role_packet,
    evaluate_adversarial_gate,
    evaluate_research_qa_gate,
    record_gate,
    run_agent_role,
)
from app.settings import Settings, get_settings

PRE_GATE_ROLES = (
    "market_agent",
    "industry_agent",
    "company_agent",
    "event_agent",
    "research_agent",
)


def run_multi_agent_pipeline(
    conn: psycopg.Connection,
    *,
    client: Any,
    settings: Settings | None = None,
    security_limit: int = 1,
    code_commit_hash: str = "m03-multi-agent",
) -> dict[str, Any]:
    """Ordered multi-agent run on one shared Snapshot. Gates block progression."""
    settings = settings or get_settings()
    profiles = load_multiagent_profiles()
    binding = bind_multi_agent_run(
        conn,
        code_commit_hash=code_commit_hash,
        llm_profile_version=profiles.version,
        security_limit=security_limit,
    )
    multi_id = binding["multi_agent_run_id"]
    run_id = binding["run_id"]
    snapshot_id = binding["snapshot_id"]
    frozen = verify_frozen_context(conn, multi_id)
    security_id = binding["security_ids"][0]

    ticker = None
    with conn.cursor() as cur:
        cur.execute("select ticker from securities where security_id=%s::uuid limit 1", (security_id,))
        row = cur.fetchone()
        ticker = row[0] if row else None

    evidence_bundle = load_evidence_bundle(
        conn,
        snapshot_id=snapshot_id,
        security_id=security_id,
        frozen_context=frozen,
    )

    prior: dict[str, Any] = {}
    outputs_meta: list[dict[str, Any]] = []
    snapshot_ids: set[str] = set()

    try:
        for role in PRE_GATE_ROLES:
            packet = build_role_packet(
                agent_role=role,
                run_id=run_id,
                snapshot_id=snapshot_id,
                frozen_context=frozen,
                security_id=security_id,
                ticker=ticker,
                prior_outputs=prior,
                evidence_bundle=evidence_bundle,
            )
            if role in {"market_agent", "industry_agent"}:
                packet["security_id"] = None
            result = run_agent_role(
                conn,
                multi_agent_run_id=multi_id,
                agent_role=role,
                packet=packet,
                client=client,
                settings=settings,
                profiles=profiles,
            )
            prior[role] = result["output"]
            outputs_meta.append(
                {"agent_role": role, "output_id": result["output_id"], "snapshot_id": result["snapshot_id"]}
            )
            snapshot_ids.add(result["snapshot_id"])

        # Research QA gate
        qa_packet = build_role_packet(
            agent_role="research_qa_agent",
            run_id=run_id,
            snapshot_id=snapshot_id,
            frozen_context=frozen,
            security_id=security_id,
            ticker=ticker,
            prior_outputs=prior,
            evidence_bundle=evidence_bundle,
        )
        qa_result = run_agent_role(
            conn,
            multi_agent_run_id=multi_id,
            agent_role="research_qa_agent",
            packet=qa_packet,
            client=client,
            settings=settings,
            profiles=profiles,
        )
        prior["research_qa_agent"] = qa_result["output"]
        outputs_meta.append(
            {
                "agent_role": "research_qa_agent",
                "output_id": qa_result["output_id"],
                "snapshot_id": qa_result["snapshot_id"],
            }
        )
        snapshot_ids.add(qa_result["snapshot_id"])
        qa_status, qa_reasons = evaluate_research_qa_gate(
            qa_result["output"],
            research_output=prior.get("research_agent"),
            allowed_evidence_ids=evidence_bundle.get("allowed_evidence_ids") or [],
            evidence_bundle=evidence_bundle,
        )
        record_gate(
            conn,
            multi_agent_run_id=multi_id,
            gate_type="research_qa",
            status=qa_status,
            reasons=qa_reasons,
            source_output_id=qa_result["output_id"],
        )
        if qa_status == "FAIL":
            raise GateBlockedError(f"research_qa gate FAIL: {qa_reasons}")

        # Adversarial + gate
        adv_packet = build_role_packet(
            agent_role="adversarial_agent",
            run_id=run_id,
            snapshot_id=snapshot_id,
            frozen_context=frozen,
            security_id=security_id,
            ticker=ticker,
            prior_outputs=prior,
            evidence_bundle=evidence_bundle,
        )
        adv_result = run_agent_role(
            conn,
            multi_agent_run_id=multi_id,
            agent_role="adversarial_agent",
            packet=adv_packet,
            client=client,
            settings=settings,
            profiles=profiles,
        )
        prior["adversarial_agent"] = adv_result["output"]
        outputs_meta.append(
            {
                "agent_role": "adversarial_agent",
                "output_id": adv_result["output_id"],
                "snapshot_id": adv_result["snapshot_id"],
            }
        )
        snapshot_ids.add(adv_result["snapshot_id"])
        adv_status, adv_reasons = evaluate_adversarial_gate(adv_result["output"])
        record_gate(
            conn,
            multi_agent_run_id=multi_id,
            gate_type="adversarial",
            status=adv_status,
            reasons=adv_reasons,
            source_output_id=adv_result["output_id"],
        )
        if adv_status == "FAIL":
            raise GateBlockedError(f"adversarial gate FAIL: {adv_reasons}")

        # Final selector
        final_packet = build_role_packet(
            agent_role="final_selector_agent",
            run_id=run_id,
            snapshot_id=snapshot_id,
            frozen_context=frozen,
            security_id=security_id,
            ticker=ticker,
            prior_outputs=prior,
            evidence_bundle=evidence_bundle,
        )
        final_result = run_agent_role(
            conn,
            multi_agent_run_id=multi_id,
            agent_role="final_selector_agent",
            packet=final_packet,
            client=client,
            settings=settings,
            profiles=profiles,
        )
        outputs_meta.append(
            {
                "agent_role": "final_selector_agent",
                "output_id": final_result["output_id"],
                "snapshot_id": final_result["snapshot_id"],
            }
        )
        snapshot_ids.add(final_result["snapshot_id"])

        catalog = approved_claim_catalog(
            prior.get("research_agent"),
            prior.get("adversarial_agent"),
            allowed_evidence_ids=evidence_bundle.get("allowed_evidence_ids") or [],
            evidence_bundle=evidence_bundle,
            qa_output=prior.get("research_qa_agent"),
        )
        final_status, final_reasons = evaluate_final_selector_gate(
            final_result["output"],
            allowed_evidence_ids=evidence_bundle.get("allowed_evidence_ids") or [],
            evidence_bundle=evidence_bundle,
            research_output=prior.get("research_agent"),
            adversarial_output=prior.get("adversarial_agent"),
            qa_output=prior.get("research_qa_agent"),
        )
        record_gate(
            conn,
            multi_agent_run_id=multi_id,
            gate_type="final_selector",
            status=final_status,
            reasons=final_reasons,
            source_output_id=final_result["output_id"],
        )
        if final_status == "FAIL":
            raise GateBlockedError(f"final_selector gate FAIL: {final_reasons}")

        materialized = materialize_final_selector(final_result["output"], catalog)
        judgment = project_final_selector_to_judgment(
            conn,
            multi_agent_run_id=multi_id,
            run_id=run_id,
            security_id=security_id,
            final_output=materialized,
            source_agent_output_id=final_result["output_id"],
        )

        with conn.cursor() as cur:
            cur.execute(
                """
                update multi_agent_runs
                set status='completed', completed_at=%s
                where multi_agent_run_id=%s::uuid
                """,
                (datetime.now(timezone.utc), multi_id),
            )
        conn.commit()

        if len(snapshot_ids) != 1 or snapshot_id not in snapshot_ids:
            raise RuntimeError("snapshot_id divergence across agents")

        return {
            "ok": True,
            "multi_agent_run_id": multi_id,
            "run_id": run_id,
            "snapshot_id": snapshot_id,
            "security_id": security_id,
            "ticker": ticker,
            "outputs": outputs_meta,
            "final": materialized,
            "judgment_id": judgment["judgment_id"],
            "allowed_evidence_ids": evidence_bundle.get("allowed_evidence_ids"),
            "scheduler_enable_allowed": False,
        }
    except GateBlockedError as exc:
        return {
            "ok": False,
            "blocked": True,
            "error_code": "GateBlockedError",
            "error": str(exc)[:300],
            "multi_agent_run_id": multi_id,
            "run_id": run_id,
            "snapshot_id": snapshot_id,
            "outputs": outputs_meta,
            "scheduler_enable_allowed": False,
        }
    except Exception as exc:  # noqa: BLE001
        with conn.cursor() as cur:
            cur.execute(
                """
                update multi_agent_runs
                set status='failed', block_reason=%s, completed_at=%s
                where multi_agent_run_id=%s::uuid
                """,
                (type(exc).__name__, datetime.now(timezone.utc), multi_id),
            )
        conn.commit()
        return {
            "ok": False,
            "blocked": False,
            "error_code": type(exc).__name__,
            "error": str(exc)[:300],
            "multi_agent_run_id": multi_id,
            "run_id": run_id,
            "snapshot_id": snapshot_id,
            "outputs": outputs_meta,
            "scheduler_enable_allowed": False,
        }
