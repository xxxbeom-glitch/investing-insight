import json
from pathlib import Path

from app.ops.jobs import finish_job, list_recent_jobs, start_job


class _FakeCur:
    def __init__(self, store: dict):
        self.store = store
        self._rows = []

    def execute(self, sql, params=None):
        sql_l = " ".join(sql.lower().split())
        if sql_l.startswith("insert into ops_jobs"):
            self.store["jobs"][params[0]] = {
                "job_id": params[0],
                "job_type": params[1],
                "stage": params[2],
                "status": "running",
                "retry_count": params[3],
                "error_code": None,
                "started_at": "t0",
                "finished_at": None,
            }
        elif sql_l.startswith("update ops_jobs set"):
            job = self.store["jobs"][params[-1]]
            job["status"] = params[0]
            if params[1] is not None:
                job["stage"] = params[1]
            job["error_code"] = params[2]
            job["finished_at"] = "t1"
        elif "from ops_jobs" in sql_l and "order by" in sql_l:
            jobs = list(self.store["jobs"].values())
            self._rows = [
                (
                    j["job_id"],
                    j["job_type"],
                    j["stage"],
                    j["status"],
                    j["error_code"],
                    j["retry_count"],
                    j["started_at"],
                    j["finished_at"],
                )
                for j in jobs
            ]

    def fetchall(self):
        return self._rows

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _FakeConn:
    def __init__(self):
        self.store = {"jobs": {}}

    def cursor(self):
        return _FakeCur(self.store)

    def commit(self):
        return None


def test_ops_job_lifecycle_persists_fields():
    conn = _FakeConn()
    job_id = start_job(conn, job_type="daily_ingest", stage="init", payload={"limit": 1})
    assert job_id in conn.store["jobs"]
    finish_job(
        conn,
        job_id,
        status="failed",
        stage="market",
        error_code="Boom",
        error_message="x" * 600,
    )
    job = conn.store["jobs"][job_id]
    assert job["status"] == "failed"
    assert job["error_code"] == "Boom"
    rows = list_recent_jobs(conn, limit=5)
    assert rows[0]["job_id"] == job_id


def test_pitr_evidence_is_unavailable_not_fake_confirmed():
    path = (
        Path(__file__).resolve().parents[2]
        / "audit"
        / "post-mvp"
        / "M01_automation_deployment"
        / "evidence"
        / "supabase_pitr_confirmation.md"
    )
    text = path.read_text(encoding="utf-8")
    assert "PITR_UNAVAILABLE" in text
    assert not any(line.strip() == "Status: CONFIRMED" for line in text.splitlines())


def test_backup_free_plan_verify_helper():
    import importlib.util
    import tempfile

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "backup_free_plan",
        root / "scripts" / "backup_free_plan.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.hostname_only("postgresql://u:p@db.example.supabase.co:5432/postgres") == "db.example.supabase.co"
    sample = (
        "-- investing-insight free-plan logical dump\n"
        + ("-- pad\n" * 40)
        + "COPY demo FROM stdin;\n"
        + "1\n"
        + "\\.\n"
    )
    with tempfile.TemporaryDirectory() as td:
        p = Path(td) / "t.sql"
        p.write_text(sample, encoding="utf-8")
        report = mod.verify_dump(p)
        assert report["ok"] is True
        assert report["checks"]["has_copy"] is True


def test_backup_check_reads_readiness_not_pitr():
    import importlib.util

    root = Path(__file__).resolve().parents[2]
    spec = importlib.util.spec_from_file_location(
        "backup_supabase_check",
        root / "scripts" / "backup_supabase_check.py",
    )
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    assert mod.hostname_only("") is None
