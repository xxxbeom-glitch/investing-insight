from app.agents.evidence import validate_research_evidence_ids
from app.governance.proposals import ARTIFACT_TYPES, GovernanceError, _require_recorded_eval


def test_artifact_types_include_profile_and_prompt():
    assert "llm_profile" in ARTIFACT_TYPES
    assert "prompt" in ARTIFACT_TYPES
    assert "quant_rule" in ARTIFACT_TYPES


def test_notes_and_hand_json_cannot_pass_governance():
    class _Conn:
        pass

    try:
        _require_recorded_eval(_Conn(), "replay", "replay", None, None)
        assert False
    except GovernanceError as exc:
        assert "evaluation_id" in str(exc)
    try:
        _require_recorded_eval(
            _Conn(),
            "replay",
            "replay",
            None,
            {"status": "PASS", "dataset_id": "d1", "metrics": {"n": 1}},
        )
        assert False
    except GovernanceError as exc:
        assert "evaluation_id" in str(exc)


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
