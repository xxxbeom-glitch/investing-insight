from __future__ import annotations

from typing import Any, Iterable


def build_ticker_cik_map(payload: dict[str, Any]) -> dict[str, str]:
    """Map ticker -> zero-padded CIK from SEC company_tickers.json."""
    out: dict[str, str] = {}
    for _, row in payload.items():
        if not isinstance(row, dict):
            continue
        ticker = str(row.get("ticker") or "").strip().upper()
        cik = row.get("cik_str")
        if not ticker or cik is None:
            continue
        out[ticker] = str(cik).zfill(10)
    return out


def extract_fact_points(
    company_facts: dict[str, Any],
    *,
    taxonomy: str = "us-gaap",
    metrics: Iterable[str] | None = None,
) -> list[dict[str, Any]]:
    """Flatten selected us-gaap facts into rows with period/published separation."""
    wanted = set(metrics or ["Assets", "Revenues", "NetIncomeLoss", "StockholdersEquity"])
    facts_root = (company_facts.get("facts") or {}).get(taxonomy) or {}
    rows: list[dict[str, Any]] = []
    entity_name = company_facts.get("entityName")
    cik = str(company_facts.get("cik") or "").zfill(10)
    for metric in wanted:
        node = facts_root.get(metric)
        if not isinstance(node, dict):
            continue
        units = node.get("units") or {}
        for unit, points in units.items():
            if not isinstance(points, list):
                continue
            for p in points:
                if not isinstance(p, dict):
                    continue
                rows.append(
                    {
                        "sec_cik": cik,
                        "entity_name": entity_name,
                        "metric_key": metric,
                        "value": p.get("val"),
                        "unit": unit,
                        "fiscal_year": p.get("fy"),
                        "fiscal_quarter": p.get("fp"),
                        "period_end": p.get("end"),
                        "filed_at": p.get("filed"),
                        "published_at": p.get("filed"),
                        "form_type": p.get("form"),
                        "frame": p.get("frame"),
                        "accn": p.get("accn"),
                    }
                )
    return rows
