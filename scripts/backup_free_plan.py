#!/usr/bin/env python3
"""
Free-plan backup readiness (M01 AC-5).

Supabase Free: Automatic Backup/PITR unavailable — do NOT fake PITR CONFIRMED.

Flow:
  dump → verify → restore-drill → readiness evidence

Dump format: logical SQL with COPY blocks (pg_dump-style data) under storage/backups/.
Restore drill: disposable schema, CREATE TABLE AS … WITH NO DATA, load COPY from dump,
compare row counts to public, DROP SCHEMA CASCADE.

Production schedulers remain DISABLED even when backup_ready=true.
Never prints connection secrets.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse

from dotenv import load_dotenv

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "apps" / "api"))
load_dotenv(REPO / ".env.local")
load_dotenv(REPO / ".env")

import psycopg  # noqa: E402
from psycopg import sql  # noqa: E402

from app.settings import get_settings  # noqa: E402

BACKUP_DIR = REPO / "storage" / "backups"
EVIDENCE_DIR = REPO / "audit" / "post-mvp" / "M01_automation_deployment" / "evidence"
DRILL_PREFIX = "m01_restore_drill_"


def hostname_only(db_url: str) -> str | None:
    if not db_url:
        return None
    try:
        return urlparse(db_url).hostname
    except Exception:  # noqa: BLE001
        return None


def _looks_secret(text: str) -> bool:
    lower = text.lower()
    return "postgresql://" in lower or "pgpassword=" in lower


def list_public_tables(conn: psycopg.Connection) -> list[str]:
    with conn.cursor() as cur:
        cur.execute(
            """
            select tablename
            from pg_tables
            where schemaname = 'public'
            order by tablename
            """
        )
        return [r[0] for r in cur.fetchall()]


def dump_public(conn: psycopg.Connection, out_path: Path) -> dict:
    tables = list_public_tables(conn)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    started = datetime.now(timezone.utc).isoformat()
    row_counts: dict[str, int] = {}

    with out_path.open("w", encoding="utf-8", newline="\n") as fh:
        fh.write("-- investing-insight free-plan logical dump\n")
        fh.write(f"-- generated_at: {started}\n")
        fh.write("-- note: structure restored via CREATE TABLE AS … WITH NO DATA; data from COPY\n")
        fh.write("SET client_encoding = 'UTF8';\n\n")

        with conn.cursor() as cur:
            for table in tables:
                cur.execute(sql.SQL("select count(*) from {}").format(sql.Identifier(table)))
                row_counts[table] = int(cur.fetchone()[0])
                fh.write(f"-- TABLE {table} rows={row_counts[table]}\n")
                fh.write(f"COPY {table} FROM stdin;\n")
                with cur.copy(sql.SQL("COPY {} TO STDOUT").format(sql.Identifier(table))) as copy:
                    for chunk in copy:
                        if isinstance(chunk, memoryview):
                            fh.write(chunk.tobytes().decode("utf-8"))
                        elif isinstance(chunk, bytes):
                            fh.write(chunk.decode("utf-8"))
                        else:
                            fh.write(str(chunk))
                fh.write("\\.\n\n")

    digest = hashlib.sha256(out_path.read_bytes()).hexdigest()
    return {
        "path": str(out_path.relative_to(REPO)).replace("\\", "/"),
        "bytes": out_path.stat().st_size,
        "sha256": digest,
        "table_count": len(row_counts),
        "row_counts": row_counts,
        "generated_at": started,
        "method": "psycopg_copy_logical_dump",
    }


def verify_dump(path: Path, expected_sha256: str | None = None) -> dict:
    if not path.is_file():
        return {"ok": False, "error_code": "MISSING_FILE"}
    raw = path.read_bytes()
    head = raw[:8000].decode("utf-8", errors="replace")
    digest = hashlib.sha256(raw).hexdigest()
    checks = {
        "exists": True,
        "min_bytes": len(raw) >= 200,
        "has_marker": "investing-insight free-plan logical dump" in head,
        "has_copy": "COPY " in head and "FROM stdin;" in head,
        "no_uri_secret": not _looks_secret(head),
        "sha256_match": expected_sha256 is None or digest == expected_sha256,
    }
    return {
        "ok": all(checks.values()),
        "bytes": len(raw),
        "sha256": digest,
        "checks": checks,
        "path": str(path.relative_to(REPO)).replace("\\", "/") if path.is_relative_to(REPO) else path.name,
    }


_COPY_RE = re.compile(
    r"^COPY\s+([a-zA-Z0-9_]+)\s+FROM\s+stdin;\n(.*?)^\\\.\s*$",
    re.MULTILINE | re.DOTALL,
)


def restore_drill(conn: psycopg.Connection, dump_path: Path) -> dict:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S")
    schema = f"{DRILL_PREFIX}{stamp}"
    text = dump_path.read_text(encoding="utf-8")
    if _looks_secret(text[:8000]):
        raise RuntimeError("dump_head_looks_like_secret")

    blocks = list(_COPY_RE.finditer(text))
    if not blocks:
        return {"ok": False, "error_code": "NO_COPY_BLOCKS", "drill_schema": schema}

    restored: dict[str, int] = {}
    source: dict[str, int] = {}
    with conn.cursor() as cur:
        cur.execute(sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema)))
        conn.commit()
        try:
            for m in blocks:
                table = m.group(1)
                data = m.group(2)
                # Structure clone from live public (Free-plan substitute when pg_dump binary absent)
                cur.execute(
                    sql.SQL(
                        "CREATE TABLE {}.{} AS TABLE public.{} WITH NO DATA"
                    ).format(
                        sql.Identifier(schema),
                        sql.Identifier(table),
                        sql.Identifier(table),
                    )
                )
                conn.commit()
                with cur.copy(
                    sql.SQL("COPY {}.{} FROM STDIN").format(
                        sql.Identifier(schema),
                        sql.Identifier(table),
                    )
                ) as copy:
                    copy.write(data.encode("utf-8"))
                conn.commit()
                cur.execute(
                    sql.SQL("select count(*) from {}.{}").format(
                        sql.Identifier(schema),
                        sql.Identifier(table),
                    )
                )
                restored[table] = int(cur.fetchone()[0])
                cur.execute(sql.SQL("select count(*) from public.{}").format(sql.Identifier(table)))
                source[table] = int(cur.fetchone()[0])
        finally:
            cur.execute(sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(sql.Identifier(schema)))
            conn.commit()

    mismatches = {
        t: {"source": source[t], "restored": restored[t]}
        for t in restored
        if source.get(t) != restored.get(t)
    }
    ok = len(restored) > 0 and not mismatches
    return {
        "ok": ok,
        "drill_schema": schema,
        "tables_restored": len(restored),
        "mismatches": mismatches,
        "sample_restored": dict(list(restored.items())[:10]),
        "dropped": True,
        "structure_method": "CREATE TABLE AS TABLE public.* WITH NO DATA",
        "data_method": "COPY FROM dump file",
    }


def write_evidence(report: dict) -> None:
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    text = json.dumps(report, indent=2)
    if _looks_secret(text):
        raise RuntimeError("refusing_to_write_secret_evidence")
    (EVIDENCE_DIR / "backup_readiness.json").write_text(text, encoding="utf-8")
    status = "PASS" if report.get("ok") else "FAIL"
    (EVIDENCE_DIR / "backup_readiness.md").write_text(
        "\n".join(
            [
                "# Backup Readiness (Supabase Free / dump+restore)",
                "",
                f"Status: {status}",
                "",
                "- Automatic Backup/PITR: unavailable on Free (not faked)",
                "- Method: logical COPY dump → verify → restore drill → DROP",
                "- Production schedulers: DISABLED",
                "",
                f"- generated_at: {report.get('generated_at')}",
                f"- db_hostname: {report.get('db_hostname')}",
                f"- dump_sha256: {(report.get('dump') or {}).get('sha256')}",
                f"- dump_bytes: {(report.get('dump') or {}).get('bytes')}",
                f"- verify_ok: {(report.get('verify') or {}).get('ok')}",
                f"- restore_ok: {(report.get('restore_drill') or {}).get('ok')}",
                f"- scheduler_enable_allowed: false",
                "",
                "Dump files: `storage/backups/` (gitignored). Never commit dumps or DB URLs.",
                "",
            ]
        ),
        encoding="utf-8",
    )
    legacy = {
        "generated_at": report.get("generated_at"),
        "db_hostname_set": bool(report.get("db_hostname")),
        "db_hostname": report.get("db_hostname"),
        "backup_method": "free_plan_logical_dump_restore",
        "pitr_confirmed": False,
        "pitr_available": False,
        "backup_ready": bool(report.get("ok")),
        "scheduler_enable_allowed": False,
        "ok": bool(report.get("ok")),
        "evidence": "audit/post-mvp/M01_automation_deployment/evidence/backup_readiness.json",
    }
    (EVIDENCE_DIR / "backup_check.json").write_text(json.dumps(legacy, indent=2), encoding="utf-8")


def cmd_readiness(_: argparse.Namespace) -> int:
    get_settings.cache_clear()
    s = get_settings()
    host = hostname_only(s.supabase_db_url or "")
    report: dict = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "plan": "supabase_free",
        "pitr_available": False,
        "method": "logical_dump_restore_drill",
        "db_hostname": host,
        "scheduler_enable_allowed": False,
        "ok": False,
    }
    if not s.supabase_db_url or not host:
        report["error_code"] = "MISSING_DB_URL"
        write_evidence(report)
        print(json.dumps(report, indent=2))
        return 2

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    dump_path = BACKUP_DIR / f"public_{stamp}.sql"
    try:
        with psycopg.connect(s.supabase_db_url) as conn:
            dump_meta = dump_public(conn, dump_path)
            report["dump"] = {
                k: dump_meta[k]
                for k in ("path", "bytes", "sha256", "table_count", "generated_at", "method")
            }
            report["dump"]["row_count_total"] = sum(dump_meta["row_counts"].values())
            verify = verify_dump(dump_path, expected_sha256=dump_meta["sha256"])
            report["verify"] = verify
            if not verify["ok"]:
                report["error_code"] = "VERIFY_FAILED"
                write_evidence(report)
                print(json.dumps(report, indent=2))
                return 1
            restore = restore_drill(conn, dump_path)
            report["restore_drill"] = restore
            report["ok"] = bool(restore.get("ok"))
            if not report["ok"]:
                report["error_code"] = "RESTORE_DRILL_FAILED"
    except Exception as exc:  # noqa: BLE001
        report["error_code"] = type(exc).__name__
        report["error"] = str(exc)[:300]
        write_evidence(report)
        print(json.dumps(report, indent=2))
        return 1

    write_evidence(report)
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


def cmd_dump(args: argparse.Namespace) -> int:
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out = Path(args.out) if args.out else BACKUP_DIR / f"public_{stamp}.sql"
    with psycopg.connect(s.supabase_db_url) as conn:
        meta = dump_public(conn, out)
    meta["ok"] = True
    meta["db_hostname"] = hostname_only(s.supabase_db_url)
    # omit full row_counts from stdout if huge — keep totals
    out_meta = {k: meta[k] for k in meta if k != "row_counts"}
    out_meta["row_count_total"] = sum(meta["row_counts"].values())
    print(json.dumps(out_meta, indent=2))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "last_dump_meta.json").write_text(json.dumps(out_meta, indent=2), encoding="utf-8")
    return 0


def cmd_verify(args: argparse.Namespace) -> int:
    report = verify_dump(Path(args.file))
    print(json.dumps(report, indent=2))
    return 0 if report["ok"] else 1


def cmd_restore_drill(args: argparse.Namespace) -> int:
    get_settings.cache_clear()
    s = get_settings()
    if not s.supabase_db_url:
        print(json.dumps({"ok": False, "error_code": "MISSING_DB_URL"}))
        return 2
    path = Path(args.file)
    v = verify_dump(path)
    if not v["ok"]:
        print(json.dumps({"ok": False, "error_code": "VERIFY_FAILED", "verify": v}, indent=2))
        return 1
    with psycopg.connect(s.supabase_db_url) as conn:
        result = restore_drill(conn, path)
    print(json.dumps(result, indent=2))
    EVIDENCE_DIR.mkdir(parents=True, exist_ok=True)
    (EVIDENCE_DIR / "last_restore_drill.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    return 0 if result["ok"] else 1


def main() -> int:
    p = argparse.ArgumentParser()
    sub = p.add_subparsers(dest="cmd", required=True)
    d = sub.add_parser("dump")
    d.add_argument("--out", default="")
    d.set_defaults(func=cmd_dump)
    v = sub.add_parser("verify")
    v.add_argument("--file", required=True)
    v.set_defaults(func=cmd_verify)
    r = sub.add_parser("restore-drill")
    r.add_argument("--file", required=True)
    r.set_defaults(func=cmd_restore_drill)
    c = sub.add_parser("readiness")
    c.set_defaults(func=cmd_readiness)
    args = p.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
