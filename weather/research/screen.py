"""Evidence-gated paper screens; no live execution or order-submission path."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping


def screen_candidate(candidate: Mapping[str, Any], policy: Mapping[str, Any]) -> dict[str, Any]:
    """Assess a single synthetic/approved candidate under explicit paper assumptions."""
    reasons: list[str] = []
    if candidate.get("source_use_status") != "approved" or not _text(candidate.get("source_use_evidence_ref")):
        reasons.append("source_use_unapproved")
    if candidate.get("mapping_status") != "verified":
        reasons.append("settlement_mapping_unverified")
    if candidate.get("alignment_eligible") is not True:
        reasons.append("forecast_alignment_missing")
    if candidate.get("calibration_status") != "validated" or candidate.get("chronological_holdout") is not True:
        reasons.append("held_out_calibration_not_validated")
    if not _text(candidate.get("calibration_evidence_ref")):
        reasons.append("calibration_evidence_missing")

    minimum_events = _positive_int(policy.get("minimum_calibration_events"), "minimum_calibration_events")
    calibration_events = _optional_nonnegative_int(candidate.get("calibration_event_count"))
    if calibration_events is None or calibration_events < minimum_events:
        reasons.append("insufficient_calibration_events")
    max_log_loss = _nonnegative_number(policy.get("maximum_log_loss"), "maximum_log_loss")
    log_loss = _nonnegative_number(candidate.get("holdout_log_loss"), "holdout_log_loss", optional=True)
    if log_loss is None or log_loss > max_log_loss:
        reasons.append("holdout_log_loss_outside_policy")

    side = candidate.get("side")
    if side not in {"buy_yes", "buy_no"}:
        reasons.append("unsupported_quote_side")
        side = None
    model_p = _probability(candidate.get("model_yes_probability"), "model_yes_probability", optional=True)
    price_field = "yes_ask" if side == "buy_yes" else "no_ask"
    size_field = "yes_ask_size" if side == "buy_yes" else "no_ask_size"
    price = _probability(candidate.get(price_field), price_field, optional=True)
    size = _positive_number(candidate.get(size_field))
    if candidate.get("quote_type") != "top_of_book":
        reasons.append("quote_not_top_of_book")
    if price is None:
        reasons.append("executable_ask_missing")
    if size is None:
        reasons.append("displayed_ask_size_missing")
    fill_rule = policy.get("fill_assumption")
    if not _text(fill_rule):
        raise ValueError("policy requires an explicit fill_assumption")
    if not _text(candidate.get("settlement_rule_ref")):
        reasons.append("settlement_rule_reference_missing")
    fee = _probability(candidate.get("fee_per_unit"), "fee_per_unit", optional=True)
    if fee is None:
        reasons.append("fee_missing")
    spread = _probability(candidate.get("spread"), "spread", optional=True)
    max_spread = _probability(policy.get("maximum_spread"), "maximum_spread")
    if spread is None or spread > max_spread:
        reasons.append("spread_outside_policy")
    decision = _timestamp(candidate.get("decision_at"), "decision_at", reasons)
    quote_at = _timestamp(candidate.get("quote_at"), "quote_at", reasons)
    quote_age = (decision - quote_at).total_seconds() if decision and quote_at else None
    max_age = _positive_int(policy.get("maximum_quote_age_seconds"), "maximum_quote_age_seconds", allow_zero=True)
    if quote_age is None or quote_age < 0 or quote_age > max_age:
        reasons.append("quote_stale_or_time_invalid")

    model_side_probability = None if model_p is None or side is None else model_p if side == "buy_yes" else 1 - model_p
    edge = model_side_probability - price - fee if model_side_probability is not None and price is not None and fee is not None else None
    minimum_edge = _probability(policy.get("minimum_net_edge"), "minimum_net_edge")
    if edge is None or edge < minimum_edge:
        reasons.append("net_edge_below_policy")

    outcome = candidate.get("held_out_outcome")
    simulated_pnl = None
    if outcome is not None:
        if outcome not in (0, 1) or isinstance(outcome, bool):
            raise ValueError("held_out_outcome must be binary 0 or 1")
        if price is not None and fee is not None and side is not None:
            payout = outcome if side == "buy_yes" else 1 - outcome
            simulated_pnl = payout - price - fee
    return {
        "event_id": candidate.get("event_id"),
        "family": candidate.get("family"),
        "settlement_rule_ref": candidate.get("settlement_rule_ref"),
        "forecast_model": candidate.get("model"),
        "forecast_run_id": candidate.get("run_id"),
        "decision_at": candidate.get("decision_at"),
        "quote_at": candidate.get("quote_at"),
        "calibration_evidence_ref": candidate.get("calibration_evidence_ref"),
        "side": side,
        "quote_type": candidate.get("quote_type"),
        "quote_age_seconds": quote_age,
        "spread": spread,
        "fee_per_unit": fee,
        "fill_assumption": fill_rule,
        "displayed_size": size,
        "net_edge_per_unit": edge,
        "held_out_outcome": outcome,
        "simulated_pnl_per_unit": simulated_pnl,
        "eligible_for_paper_review": not reasons,
        "classification": "paper_candidate" if not reasons else "exploratory_or_rejected",
        "reasons": reasons,
        "live_execution": False,
    }


def summarize_screen(results: list[Mapping[str, Any]]) -> dict[str, Any]:
    """Return sample counts only; deliberately does not infer performance claims."""
    eligible = [row for row in results if row.get("eligible_for_paper_review") is True]
    events = {row.get("event_id") for row in eligible if row.get("event_id") is not None}
    outcomes = [row["simulated_pnl_per_unit"] for row in eligible if row.get("simulated_pnl_per_unit") is not None]
    return {
        "candidate_count": len(results),
        "eligible_candidate_count": len(eligible),
        "eligible_event_count": len(events),
        "simulated_outcome_count": len(outcomes),
        "mean_simulated_pnl_per_unit": sum(outcomes) / len(outcomes) if outcomes else None,
        "interpretation": "paper_research_only_no_live_execution",
    }


def _timestamp(value: Any, field: str, reasons: list[str]) -> datetime | None:
    if not isinstance(value, str):
        reasons.append(f"{field}_missing")
        return None
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        reasons.append(f"{field}_invalid")
        return None
    if parsed.tzinfo is None:
        reasons.append(f"{field}_timezone_missing")
        return None
    return parsed.astimezone(timezone.utc)


def _probability(value: Any, field: str, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or not 0 <= value <= 1:
        raise ValueError(f"{field} must be finite and in [0, 1]")
    return float(value)


def _positive_number(value: Any) -> float | None:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
        return None
    return float(value)


def _positive_int(value: Any, field: str, allow_zero: bool = False) -> int:
    minimum = 0 if allow_zero else 1
    if isinstance(value, bool) or not isinstance(value, int) or value < minimum:
        raise ValueError(f"{field} must be an integer >= {minimum}")
    return value


def _optional_nonnegative_int(value: Any) -> int | None:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        return None
    return value


def _nonnegative_number(value: Any, field: str, optional: bool = False) -> float | None:
    if value is None and optional:
        return None
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value < 0:
        raise ValueError(f"{field} must be finite and non-negative")
    return float(value)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
