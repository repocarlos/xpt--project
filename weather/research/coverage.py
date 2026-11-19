"""Coverage aggregation for approved manifests or synthetic summaries only."""

from __future__ import annotations

from collections import defaultdict
from datetime import date
from typing import Any, Iterable, Mapping


def build_coverage_report(records: Iterable[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Aggregate metadata summaries by family and data tier.

    This function accepts counts and manifest metadata, not source observations.
    Rights-unresolved inputs are reported as blocked; no missing value is filled
    with zero unless an explicit denominator and observed count are supplied.
    """
    groups: dict[tuple[str, str], list[Mapping[str, Any]]] = defaultdict(list)
    for row in records:
        family, tier = row.get("family"), row.get("data_tier")
        if not _text(family) or not _text(tier):
            raise ValueError("each summary needs family and data_tier")
        groups[(str(family), str(tier))].append(row)

    report = []
    for (family, tier), rows in sorted(groups.items()):
        expected_values = [_count(row, "expected_count") for row in rows]
        observed_values = [_count(row, "observed_count") for row in rows]
        if any(value is None for value in expected_values + observed_values):
            expected = observed = missing = coverage = None
        else:
            expected = sum(expected_values)  # type: ignore[arg-type]
            observed = sum(observed_values)  # type: ignore[arg-type]
            if observed > expected:
                raise ValueError("observed_count cannot exceed expected_count")
            missing = expected - observed
            coverage = observed / expected if expected else None

        rights_ok = all(
            row.get("source_use_status") == "approved" and _text(row.get("approval_evidence_ref"))
            for row in rows
        )
        starts = [_parse_date(row.get("coverage_start")) for row in rows]
        ends = [_parse_date(row.get("coverage_end")) for row in rows]
        estimates = [_count(row, "estimated_bytes") for row in rows]
        if any(value is None for value in estimates):
            estimated_bytes = None
        else:
            estimated_bytes = sum(estimates)  # type: ignore[arg-type]

        status = "blocked_on_rights" if not rights_ok else "limited"
        if rights_ok and coverage == 1.0:
            status = "ready"
        report.append({
            "family": family,
            "data_tier": tier,
            "summary_count": len(rows),
            "expected_count": expected,
            "observed_count": observed,
            "missing_count": missing,
            "coverage_fraction": coverage,
            "coverage_start": min((d for d in starts if d is not None), default=None),
            "coverage_end": max((d for d in ends if d is not None), default=None),
            "forecast_vintage_count": _sum_optional(rows, "forecast_vintage_count"),
            "outcome_count": _sum_optional(rows, "outcome_count"),
            "quote_count": _sum_optional(rows, "quote_count"),
            "estimated_bytes": estimated_bytes,
            "backfill_summary_count": sum(row.get("capture_mode") == "backfill" for row in rows),
            "prospective_summary_count": sum(row.get("capture_mode") == "prospective" for row in rows),
            "retention_days": min((_count(row, "retention_days") for row in rows if _count(row, "retention_days") is not None), default=None),
            "status": status,
            "evidence_refs": sorted({str(row["evidence_ref"]) for row in rows if _text(row.get("evidence_ref"))}),
            "denominator_definition": "sum of explicit expected_count across summaries in this family and tier",
        })
    return report


def _sum_optional(rows: list[Mapping[str, Any]], field: str) -> int | None:
    values = [_count(row, field) for row in rows]
    if any(value is None for value in values):
        return None
    return sum(values)  # type: ignore[arg-type]


def _count(row: Mapping[str, Any], field: str) -> int | None:
    value = row.get(field)
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValueError(f"{field} must be a non-negative integer")
    return value


def _parse_date(value: Any) -> date | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValueError("coverage dates must be ISO calendar dates")
    try:
        return date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError("coverage dates must be ISO calendar dates") from exc


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
