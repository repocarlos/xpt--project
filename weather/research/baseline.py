"""Quote-context-preserving probability comparisons for the weather study."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping


def compare_models(
    market: Mapping[str, Any],
    forecasts: list[Mapping[str, Any]],
    *,
    decision_at: str,
    max_quote_age_seconds: int,
    transaction_cost: float = 0.0,
    candidate_gap_threshold: float = 0.05,
) -> list[dict[str, Any]]:
    """Compare each aligned forecast separately; outputs are research candidates only."""
    _require_approved(market)
    for forecast in forecasts:
        _require_approved(forecast)
    decision = _timestamp(decision_at, "decision_at")
    quote_at = _timestamp(market.get("quote_at"), "quote_at", optional=True)
    age = (decision - quote_at).total_seconds() if quote_at else None
    if max_quote_age_seconds < 0 or transaction_cost < 0 or candidate_gap_threshold < 0:
        raise ValueError("age limit, costs, and candidate threshold must be non-negative")

    bid = _probability(market.get("yes_bid"), "yes_bid", optional=True)
    ask = _probability(market.get("yes_ask"), "yes_ask", optional=True)
    no_bid = _probability(market.get("no_bid"), "no_bid", optional=True)
    no_ask = _probability(market.get("no_ask"), "no_ask", optional=True)
    quote_coherent = bid is not None and ask is not None and bid <= ask
    stale = age is None or age < 0 or age > max_quote_age_seconds
    top_of_book = market.get("quote_type") == "top_of_book"
    mapping_ok = market.get("mapping_status") == "verified"
    ladder_complete = market.get("bucket_ladder_complete") is True
    midpoint = (bid + ask) / 2 if quote_coherent else None
    rows = []
    for forecast in forecasts:
        model_probability = _probability(forecast.get("probability"), "probability")
        aligned = forecast.get("alignment_eligible") is True
        executable_context = top_of_book and quote_coherent and not stale and mapping_ok and aligned
        gap = model_probability - midpoint if midpoint is not None else None
        buy_yes = model_probability - ask if ask is not None and executable_context else None
        sell_yes = bid - model_probability if bid is not None and executable_context else None
        rows.append({
            "family": market.get("family"),
            "cohort_id": market.get("cohort_id"),
            "decision_at": decision.isoformat().replace("+00:00", "Z"),
            "model": forecast.get("model"),
            "run_id": forecast.get("run_id"),
            "model_probability": model_probability,
            "yes_bid": bid,
            "yes_ask": ask,
            "no_bid": no_bid,
            "no_ask": no_ask,
            "midpoint": midpoint,
            "spread": ask - bid if quote_coherent else None,
            "quote_age_seconds": age,
            "quote_type": market.get("quote_type"),
            "probability_gap_vs_midpoint": gap,
            "buy_yes_gross_edge": buy_yes,
            "sell_yes_gross_edge": sell_yes,
            "buy_yes_net_edge": buy_yes - transaction_cost if buy_yes is not None else None,
            "sell_yes_net_edge": sell_yes - transaction_cost if sell_yes is not None else None,
            "executable_quote_context": executable_context,
            "mapping_status": market.get("mapping_status"),
            "alignment_eligible": aligned,
            "quote_coherent": quote_coherent,
            "incomplete_bucket_ladder": not ladder_complete,
            "stale_quote": stale,
            "candidate_gap": (gap is not None and abs(gap) >= candidate_gap_threshold
                              and aligned and not stale and mapping_ok),
            "interpretation": "candidate_gap_for_validation_only",
        })
    return rows


def _timestamp(value: Any, field: str, optional: bool = False) -> datetime | None:
    if value is None and optional:
        return None
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc)


def _probability(value: Any, field: str, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{field} must be a finite probability in [0, 1]")
    return float(value)


def _require_approved(row: Mapping[str, Any]) -> None:
    if row.get("source_use_status") != "approved" or not isinstance(row.get("source_use_evidence_ref"), str) or not row["source_use_evidence_ref"].strip():
        raise PermissionError("comparison requires approved source use and evidence")
