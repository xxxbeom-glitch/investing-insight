import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
_SPEC = importlib.util.spec_from_file_location(
    "production_readiness_check",
    ROOT / "scripts" / "production_readiness_check.py",
)
assert _SPEC and _SPEC.loader
_mod = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(_mod)


def test_build_report_has_no_secret_needles_in_json():
    report = _mod.build_report()
    blob = json.dumps(report)
    for needle in ("OPENAI_API_KEY=", "postgresql://", "Bearer "):
        assert needle not in blob
    assert any(c["check"] == "openai_key_set" for c in report["checks"])
    assert "checks" in report


def test_secret_blob_detector():
    assert _mod._looks_like_secret_blob("postgresql://user:pass@db.supabase.co/postgres")
    assert not _mod._looks_like_secret_blob("openai_key_set=true")
    assert isinstance(_mod.SECRET_NEEDLES, tuple)
