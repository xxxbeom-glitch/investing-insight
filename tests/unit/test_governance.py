import pytest

from app.agents.evidence import validate_research_evidence_ids
from app.governance.proposals import GovernanceError, ARTIFACT_TYPES, _require_eval_pass


def test_artifact_types_include_profile_and_prompt():
    assert "llm_profile" in ARTIFACT_TYPES
    assert "prompt" in ARTIFACT_TYPES
    assert "quant_rule" in ARTIFACT_TYPES


def test_notes_alone_cannot_pass_governance():
    with pytest.raises(GovernanceError, match="eval artifact required"):
        _require_eval_pass("replay", None)
    with pytest.raises(GovernanceError, match="must be PASS"):
        _require_eval_pass("replay", {"status": "NOTES_ONLY", "dataset_id": "d1", "metrics": {}})
    with pytest.raises(GovernanceError, match="dataset_id or snapshot_id"):
        _require_eval_pass("holdout", {"status": "PASS", "metrics": {}})
    # valid
    _require_eval_pass(
        "replay",
        {"status": "PASS", "snapshot_id": "s1", "metrics": {"n": 1}},
    )


def test_unknown_evidence_ids_fail_deterministic_qa():
    status, reasons = validate_research_evidence_ids(
        {
            "claims": [{"claim": "x", "evidence_id": "missing"}],
            "evidence_refs": ["also-missing"],
        },
        {"regime", "assessment:semis"},
    )
    assert status == "FAIL"
    assert any("unknown_evidence" in r for r in reasons)


def test_known_evidence_ids_pass_deterministic_qa():
    status, reasons = validate_research_evidence_ids(
        {
            "claims": [{"claim": "x", "evidence_id": "regime"}],
            "evidence_refs": ["regime", "assessment:semis"],
        },
        {"regime", "assessment:semis"},
    )
    assert status == "PASS"
    assert reasons == []
