import json

from app.agents.mock_client import MockStructuredClient
from app.agents.profiles import load_multiagent_profiles
from app.agents.runner import (
    build_role_packet,
    evaluate_adversarial_gate,
    evaluate_research_qa_gate,
)
from app.research.schema_validate import load_schema, validate_against_schema


def test_multiagent_profiles_load():
    p = load_multiagent_profiles()
    assert p.version == "llm-profile-v0.2"
    assert p.market_agent.model
    assert p.adversarial_agent.reasoning_effort == "high"


def test_role_schemas_validate_defaults():
    client = MockStructuredClient()
    for role in (
        "market_agent",
        "industry_agent",
        "company_agent",
        "event_agent",
        "research_agent",
        "research_qa_agent",
        "adversarial_agent",
        "final_selector_agent",
    ):
        packet = build_role_packet(
            agent_role=role,
            run_id="r",
            snapshot_id="s",
            frozen_context={"regime": {"regime": "expansion"}, "union": {"members": []}, "assessments": []},
            security_id="sec",
            ticker="AAA",
            prior_outputs={
                "research_agent": {
                    "synthesis": "x",
                    "claims": [],
                    "bear_case": [],
                    "evidence_refs": ["e1"],
                    "unsupported_or_missing": [],
                }
            },
        )
        result = client.create_structured(
            model="gpt-5.6-terra",
            reasoning_effort="medium",
            system_prompt="x",
            user_payload=packet,
            output_schema={},
            schema_name=role,
        )
        output = json.loads(result.output_text)
        schema_name = {
            "market_agent": "agent_market_output.schema.json",
            "industry_agent": "agent_industry_output.schema.json",
            "company_agent": "agent_company_output.schema.json",
            "event_agent": "agent_event_output.schema.json",
            "research_agent": "agent_research_output.schema.json",
            "research_qa_agent": "agent_research_qa_output.schema.json",
            "adversarial_agent": "agent_adversarial_output.schema.json",
            "final_selector_agent": "agent_final_selector_output.schema.json",
        }[role]
        validate_against_schema(output, load_schema(schema_name))


def test_research_qa_gate_blocks():
    status, reasons = evaluate_research_qa_gate({"status": "FAIL", "failed_claims": ["c1"], "warnings": []})
    assert status == "FAIL"
    assert "c1" in reasons
    status, _ = evaluate_research_qa_gate({"status": "PASS", "failed_claims": [], "warnings": []})
    assert status == "PASS"


def test_adversarial_gate_blocks_on_blockers():
    status, reasons = evaluate_adversarial_gate(
        {"status": "PASS", "counter_thesis": "x", "broken_assumptions": [], "gate_blockers": ["b1"]}
    )
    assert status == "FAIL"
    assert reasons == ["b1"]


def test_packets_share_snapshot_id():
    snap = "snap-fixed"
    for role in ("market_agent", "company_agent", "research_agent"):
        pkt = build_role_packet(
            agent_role=role,
            run_id="run1",
            snapshot_id=snap,
            frozen_context={"regime": {}, "union": {"members": []}, "assessments": []},
            security_id="s1",
            ticker="AAA",
        )
        assert pkt["snapshot_id"] == snap
        assert pkt["run_id"] == "run1"


def test_mock_client_is_structured_only():
    client = MockStructuredClient()
    assert hasattr(client, "create_structured")
    assert not hasattr(client, "chat")
