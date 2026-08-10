import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parents[1] / "apps" / "api"
if str(API_ROOT) not in sys.path:
    sys.path.insert(0, str(API_ROOT))


def priced_security_ids(conn, limit: int = 20) -> list[str]:
    """Scope snapshot tests after full-registry ingest (ER-P1-01)."""
    with conn.cursor() as cur:
        cur.execute(
            """
            select distinct security_id::text
            from daily_prices
            order by security_id
            limit %s
            """,
            (limit,),
        )
        return [r[0] for r in cur.fetchall()]
