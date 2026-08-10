import json

from app.research.schema_validate import load_schema, validate_against_schema


def test_company_analysis_schemas_load():
    inp = load_schema("company_analysis_input.schema.json")
    out = load_schema("company_analysis_output.schema.json")
    sample_in = {
        "schema_version": "company-analysis-input-v0.1",
        "run_id": "r",
        "snapshot_id": "s",
        "security_id": "x",
        "identity": {},
        "quant": {},
        "evidence": [{"evidence_id": "e1"}],
    }
    validate_against_schema(sample_in, inp)
    sample_out = {
        "summary": "s",
        "business_model": "b",
        "growth_drivers": ["g"],
        "moat_assessment": "m",
        "financial_interpretation": "f",
        "valuation_interpretation": "v",
        "bull_case": ["a"],
        "bear_case": ["b"],
        "key_risks": ["r"],
        "invalidation_conditions": ["i"],
        "uncertainties": ["u"],
        "claim_evidence_map": [{"claim": "c", "evidence_id": "e1"}],
        "unsupported_or_missing": ["m"],
    }
    validate_against_schema(sample_out, out)
    assert json.dumps(sample_out)


def test_schema_rejects_extra_keys():
    inp = load_schema("company_analysis_input.schema.json")
    bad = {
        "schema_version": "company-analysis-input-v0.1",
        "run_id": "r",
        "snapshot_id": "s",
        "security_id": "x",
        "identity": {},
        "quant": {},
        "evidence": [],
        "extra": 1,
    }
    try:
        validate_against_schema(bad, inp)
        assert False, "expected ValueError"
    except ValueError as e:
        assert "additional" in str(e).lower()
