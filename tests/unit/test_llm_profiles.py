from pathlib import Path

from app.llm_profiles import load_llm_profiles

REPO = Path(__file__).resolve().parents[2]


def test_llm_profiles_load_and_roles():
    profiles = load_llm_profiles(REPO / "config" / "llm_profiles.v0.1.yaml")
    assert profiles.version.startswith("llm-profile")
    assert profiles.api == "responses"
    assert profiles.company_research.reasoning_effort == "medium"
    assert profiles.research_qa.reasoning_effort == "high"
    assert profiles.final_judgment.model


def test_schema_examples_exist():
    schemas = REPO / "packages" / "schemas"
    required = [
        "company_analysis_input.schema.json",
        "company_analysis_output.schema.json",
        "research_qa_output.schema.json",
        "final_judgment_output.schema.json",
        "snapshot_manifest.schema.json",
    ]
    for name in required:
        assert (schemas / name).is_file()
