import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]


def test_generate_audit_layer(tmp_path, monkeypatch):
    # Run against repo templates into a temp layer under audit/mvp
    layer_id = "L99_test_generator"
    dest = REPO / "audit" / "mvp" / layer_id
    if dest.exists():
        for p in dest.iterdir():
            p.unlink()
        dest.rmdir()
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "generate_audit_layer.py"), layer_id],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    for name in [
        "PLAN.md",
        "IMPLEMENTATION.md",
        "TEST_RESULTS.md",
        "QA_REPORT.md",
        "CHANGELOG.md",
        "OPEN_ISSUES.md",
        "HANDOFF.md",
    ]:
        assert (dest / name).is_file()
    # cleanup
    for p in dest.iterdir():
        p.unlink()
    dest.rmdir()


def test_migrate_check_lists_sql():
    proc = subprocess.run(
        [sys.executable, str(REPO / "scripts" / "migrate.py"), "--check"],
        cwd=REPO,
        capture_output=True,
        text=True,
        check=False,
    )
    assert proc.returncode == 0, proc.stderr
    assert "0001_app_bootstrap.sql" in proc.stdout
