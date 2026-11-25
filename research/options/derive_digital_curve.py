#!/usr/bin/env python3
"""Derive a quote-bounded PM event-price curve from aligned synthetic snapshots."""
from __future__ import annotations

import argparse
import json
import math
import statistics
from pathlib import Path
from typing import Any


def _quote_interval(pm: dict[str, Any], target_relation: str) -> tuple[float, float, str, list[str], dict[str, Any]]:
    payout = float(pm["payout"])
    yes_bid, yes_ask = float(pm["yes_bid"]), float(pm["yes_ask"])
    no_bid, no_ask = float(pm["no_bid"]), float(pm["no_ask"])
    relation = pm.get("event_relation")
    flags: list[str] = []

    if relation == ">":
        low, high, side = yes_bid / payout, yes_ask / payout, "YES"
    elif relation == "<=":
        low, high, side = no_bid / payout, no_ask / payout, "NO"
    elif relation == ">=":
        low, high, side = yes_bid / payout, yes_ask / payout, "YES"
        flags.append("equality_mass_ambiguity")
    elif relation == "<":
        low, high, side = no_bid / payout, no_ask / payout, "NO"
        flags.append("equality_mass_ambiguity")
    else:
        return 0.0, 0.0, "unavailable", ["unsupported_event_relation"]

    if target_relation != ">":
        flags.append("unsupported_target_relation")
    for value in (low, high):
        if not math.isfinite(value) or value < 0 or value > 1:
            flags.append("quote_outside_unit_payout_bounds")
    if low > high:
        flags.append("crossed_target_quote")
    opposite_interval = (
        (1.0 - no_ask / payout, 1.0 - no_bid / payout)
        if side == "YES" else
        (1.0 - yes_ask / payout, 1.0 - yes_bid / payout)
    )
    complement_overlap = max(low, opposite_interval[0]) <= min(high, opposite_interval[1])
    if not complement_overlap:
        flags.append("yes_no_complement_nonoverlap")
    complement_check = {
        "target_interval": [low, high],
        "complement_from_opposite_book": list(opposite_interval),
        "intervals_overlap": complement_overlap,
    }
    return low, high, side, sorted(set(flags)), complement_check


def derive_digital_curve(document: dict[str, Any], target_relation: str = ">") -> dict[str, Any]:
    if document.get("schema_version") != "options.aligned_inputs.v1":
        raise ValueError("schema_version must be 'options.aligned_inputs.v1'")
    if document.get("fixture_status") not in {"synthetic", "real"}:
        raise ValueError("fixture_status must be 'synthetic' or 'real'")
    if document.get("status") == "blocked_source_rights" or (
        document.get("fixture_status") == "real" and not document.get("real_data_enabled")
    ):
        return {
            "schema_version": "options.digital_curve.v1",
            "fixture_status": document.get("fixture_status"),
            "status": "blocked_source_rights",
            "points": [],
            "reason": "source-use approvals are unresolved; no digital curve was derived",
        }
    if target_relation != ">":
        raise ValueError("this v1 implementation defines the target as strict underlying > threshold")

    aligned_rows = document.get("rows", [])
    groups = {(row.get("pm", {}).get("underlying"), row.get("pm", {}).get("expiry"),
               row.get("pm", {}).get("settlement_reference"), row.get("pm", {}).get("observation_time"),
               row.get("pm", {}).get("quote_timestamp")) for row in aligned_rows
              if row.get("alignment_status") == "matched"}
    if len({group[:4] for group in groups}) > 1:
        raise ValueError("one digital curve may contain only one underlying/expiry/settlement/observation group")

    points = []
    for aligned in aligned_rows:
        pm = aligned.get("pm") or {}
        low, high, side, orientation_flags, complement_check = _quote_interval(pm, target_relation)
        flags = list(aligned.get("pm_quality_flags", [])) + orientation_flags
        if aligned.get("alignment_status") != "matched":
            flags.append(aligned.get("alignment_status", "unmatched_input"))
        if "equality_mass_ambiguity" in flags:
            flags.append("terminal_rule_not_equivalent_to_strict_greater")
        payout = float(pm.get("payout", 1.0))
        point = {
            "contract_id": pm.get("contract_id", aligned.get("contract_id")),
            "threshold": float(pm.get("threshold", aligned.get("threshold"))),
            "bid": low,
            "ask": high,
            "quote_status": "usable" if not flags else "excluded",
            "quality_flags": sorted(set(flags)),
            "yes_event_relation": pm.get("event_relation"),
            "target_relation": target_relation,
            "side_used": side,
            "payout_original": payout,
            "quote_timestamp": pm.get("quote_timestamp"),
            "contract_rule_version": pm.get("contract_rule_version"),
            "raw_yes_bid": pm.get("yes_bid"),
            "raw_yes_ask": pm.get("yes_ask"),
            "raw_no_bid": pm.get("no_bid"),
            "raw_no_ask": pm.get("no_ask"),
            "listed_chain_quality_flags": aligned.get("listed_chain_quality_flags", []),
            "complement_check": complement_check,
        }
        points.append(point)

    points.sort(key=lambda row: (row["threshold"], row["contract_id"] or ""))
    usable = [point for point in points if point["quote_status"] == "usable"]
    bid_violations, ask_violations = [], []
    for left, right in zip(usable, usable[1:]):
        if right["bid"] > left["bid"] + 1e-12:
            bid_violations.append({"from_threshold": left["threshold"], "to_threshold": right["threshold"]})
        if right["ask"] > left["ask"] + 1e-12:
            ask_violations.append({"from_threshold": left["threshold"], "to_threshold": right["threshold"]})
    gaps = [right["threshold"] - left["threshold"] for left, right in zip(usable, usable[1:])]
    sparse = len(usable) < 3 or bool(gaps and max(gaps) > 2.0 * statistics.median(gaps))
    first = usable[0]["threshold"] if usable else None
    last = usable[-1]["threshold"] if usable else None
    matched_pm = [row["pm"] for row in aligned_rows if row.get("alignment_status") == "matched"]
    first_pm = matched_pm[0] if matched_pm else {}
    monotone = not bid_violations and not ask_violations

    return {
        "schema_version": "options.digital_curve.v1",
        "fixture_status": document["fixture_status"],
        "status": "synthetic_only" if document["fixture_status"] == "synthetic" else "authorized_market_inputs",
        "underlying": first_pm.get("underlying"),
        "expiry": first_pm.get("expiry"),
        "snapshot_time": document.get("snapshot_time"),
        "event_relation": target_relation,
        "price_basis": "undiscounted_event_price",
        "price_convention": "PM event price per unit cash payout; no discounting or risk-neutral interpretation is applied.",
        "payout": 1.0,
        "points": points,
        "curve_diagnostics": {
            "usable_points": len(usable),
            "excluded_points": len(points) - len(usable),
            "usable_strike_coverage": [first, last] if usable else None,
            "usable_strike_gaps": gaps,
            "sparse_coverage_warning": sparse,
            "bid_curve_nonincreasing": not bid_violations,
            "ask_curve_nonincreasing": not ask_violations,
            "monotonicity_violations": {"bid": bid_violations, "ask": ask_violations},
            "curve_suitable_for_option_transformation": bool(usable) and monotone and not sparse,
        },
        "interpretation_warning": "These are PM event-price conventions, not unbiased forecasts or options risk-neutral probabilities.",
        "source_use_status": document.get("source_use_status", {}),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    aligned = json.loads(args.input.read_text(encoding="utf-8"))
    curve = derive_digital_curve(aligned)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(curve, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
