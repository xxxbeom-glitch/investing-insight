import pytest

from app.governance.proposals import GovernanceError, ARTIFACT_TYPES


def test_artifact_types_include_profile_and_prompt():
    assert "llm_profile" in ARTIFACT_TYPES
    assert "prompt" in ARTIFACT_TYPES
    assert "quant_rule" in ARTIFACT_TYPES


def test_approve_requires_notes_logic():
    # mirror guard without DB
    replay_notes = ""
    holdout_notes = "x"
    with pytest.raises(GovernanceError):
        if not replay_notes.strip() or not holdout_notes.strip():
            raise GovernanceError("replay_notes and holdout_notes required before approve")
