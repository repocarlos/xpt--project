"""Strict forecast-to-decision alignment checks; never calibrates forecasts."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


def align_forecast(forecast: Mapping[str, Any], contract: Mapping[str, Any]) -> dict[str, Any]:
    """Return one accepted/rejected alignment record with an auditable reason."""
    reasons: list[str] = []
    try:
        issued = _timestamp(forecast.get("issued_at"), "issued_at")
        decision = _timestamp(contract.get("decision_at"), "decision_at")
        fstart = _timestamp(forecast.get("valid_start"), "valid_start")
        fend = _timestamp(forecast.get("valid_end"), "valid_end")
        cstart = _timestamp(contract.get("valid_start"), "valid_start")
        cend = _timestamp(contract.get("valid_end"), "valid_end")
    except ValueError as exc:
        return {"eligible": False, "reasons": [str(exc)], "lead_hours": None}

    if issued > decision:
        reasons.append("forecast_issued_after_decision")
    if fend <= fstart or cend <= cstart:
        reasons.append("invalid_valid_window")
    elif fstart > cstart or fend < cend:
        reasons.append("valid_window_not_covered")
    if forecast.get("variable") != contract.get("variable"):
        reasons.append("variable_mismatch")
    if forecast.get("unit") != contract.get("unit"):
        reasons.append("unit_mismatch")
    if _locations(forecast) != _locations(contract):
        reasons.append("spatial_support_mismatch")
    if forecast.get("timezone") != contract.get("timezone"):
        reasons.append("timezone_mismatch")
    lead = (decision - issued).total_seconds() / 3600
    return {
        "eligible": not reasons,
        "reasons": reasons,
        "forecast_run_id": forecast.get("run_id"),
        "model": forecast.get("model"),
        "issued_at_utc": issued.isoformat().replace("+00:00", "Z"),
        "decision_at_utc": decision.isoformat().replace("+00:00", "Z"),
        "lead_hours": lead,
        "valid_start_utc": fstart.isoformat().replace("+00:00", "Z"),
        "valid_end_utc": fend.isoformat().replace("+00:00", "Z"),
    }


def align_forecasts(forecasts: list[Mapping[str, Any]], contracts: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Align explicit candidate pairs and report accepted/rejected counts."""
    results = [align_forecast(forecast, contract) for forecast, contract in zip(forecasts, contracts)]
    if len(forecasts) != len(contracts):
        raise ValueError("forecasts and contracts must be explicit one-to-one candidate pairs")
    accepted = sum(result["eligible"] for result in results)
    reasons: dict[str, int] = {}
    for result in results:
        for reason in result["reasons"]:
            reasons[reason] = reasons.get(reason, 0) + 1
    return {"pairs": results, "candidate_count": len(results), "accepted_count": accepted,
            "rejected_count": len(results) - accepted, "rejection_counts": reasons}


def _timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str):
        raise ValueError(f"missing_or_invalid_{field}")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"missing_or_invalid_{field}") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"timezone_required_{field}")
    return parsed.astimezone(timezone.utc)


def _locations(row: Mapping[str, Any]) -> tuple[str, ...]:
    locations = row.get("location_refs")
    if locations is None:
        location = row.get("location_ref")
        return (str(location),) if isinstance(location, str) and location else ()
    if not isinstance(locations, (list, tuple, set)) or not all(isinstance(x, str) and x for x in locations):
        return ()
    return tuple(sorted(set(locations)))
