#!/usr/bin/env python3
"""Rights-gated normalization and timestamp alignment for synthetic option inputs."""
from __future__ import annotations

import argparse
import json
import math
from datetime import datetime
from pathlib import Path
from typing import Any


REQUIRED_USES = ("collection", "raw_storage", "derivation", "team_sharing", "dashboard_display")


def _timestamp(value: str, field: str) -> datetime:
    if not isinstance(value, str) or not value:
        raise ValueError(f"{field} must be an ISO timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed


def _rights_clear(document: dict[str, Any]) -> bool:
    uses = document.get("source_use_status", {})
    return all(uses.get(use) == "approved" for use in REQUIRED_USES)


def _finite(value: Any, field: str, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{field} must be numeric")
    numeric = float(value)
    if not math.isfinite(numeric):
        raise ValueError(f"{field} must be finite")
    if numeric < 0 if allow_zero else numeric <= 0:
        raise ValueError(f"{field} must be {'nonnegative' if allow_zero else 'positive'}")
    return numeric


def _same_snapshot_terms(pm: dict[str, Any], option: dict[str, Any]) -> bool:
    return (
        pm.get("underlying") == option.get("underlying")
        and pm.get("expiry") == option.get("expiry")
        and pm.get("settlement_reference") == option.get("settlement_reference")
        and str(option.get("option_style", "")).lower() == "european"
        and str(option.get("option_type", "")).lower() == "call"
    )


def _option_quality(option: dict[str, Any], snapshot: datetime,
                    max_age_seconds: float, max_relative_spread: float) -> list[str]:
    flags = []
    timestamp = _timestamp(option.get("quote_timestamp"), "option quote_timestamp")
    if abs((snapshot - timestamp).total_seconds()) > max_age_seconds:
        flags.append("stale_listed_quote")
    bid = _finite(option.get("bid"), "listed bid", allow_zero=True)
    ask = _finite(option.get("ask"), "listed ask", allow_zero=True)
    if bid > ask:
        flags.append("crossed_listed_book")
    else:
        mid = (bid + ask) / 2.0
        if mid == 0 or (ask - bid) / mid > max_relative_spread:
            flags.append("wide_listed_spread")
    for side in ("bid_size", "ask_size"):
        if option.get(side) is None or float(option[side]) <= 0:
            flags.append("missing_or_zero_listed_depth")
    return sorted(set(flags))


def align_inputs(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "options.alignment_input.v1":
        raise ValueError("schema_version must be 'options.alignment_input.v1'")
    fixture_status = document.get("fixture_status")
    if fixture_status not in {"synthetic", "real"}:
        raise ValueError("fixture_status must be 'synthetic' or 'real'")
    if fixture_status == "real" and not _rights_clear(document):
        return {
            "schema_version": "options.aligned_inputs.v1",
            "fixture_status": "real",
            "status": "blocked_source_rights",
            "real_data_enabled": False,
            "source_use_status": document.get("source_use_status", {}),
            "reason": "required collection/storage/derivation/sharing/display permissions are not all approved",
            "rows": [],
        }

    tolerance = _finite(document.get("quote_tolerance_seconds", 60), "quote_tolerance_seconds", allow_zero=True)
    max_pm_spread = _finite(document.get("max_pm_spread_fraction", 1.0), "max_pm_spread_fraction", allow_zero=True)
    max_option_spread = _finite(document.get("max_listed_relative_spread", 1.0), "max_listed_relative_spread", allow_zero=True)
    snapshot = _timestamp(document.get("snapshot_time"), "snapshot_time")
    pm_contracts = document.get("pm_contracts", [])
    listed_quotes = document.get("listed_quotes", [])
    results = []
    unique_usable_option_ids: set[str] = set()

    for pm in pm_contracts:
        pm_time = _timestamp(pm.get("quote_timestamp"), "PM quote_timestamp")
        pm_threshold = _finite(pm.get("threshold"), "PM threshold")
        payout = _finite(pm.get("payout"), "PM payout")
        identity_matches = [option for option in listed_quotes if _same_snapshot_terms(pm, option)]
        options = []
        for option in identity_matches:
            option_time = _timestamp(option.get("quote_timestamp"), "option quote_timestamp")
            delta = (option_time - pm_time).total_seconds()
            if abs(delta) <= tolerance:
                options.append((option_time, delta, option))
        if not options:
            status = "timestamp_mismatch" if identity_matches else "unmatched_terms"
            results.append({
                "contract_id": pm.get("contract_id"),
                "threshold": pm_threshold,
                "alignment_status": status,
                "pm_quality_flags": [],
                "quality_flags": ["no_synchronized_listed_chain"],
                "usable_for_curve": False,
                "pm": dict(pm),
                "listed_option_chain": [],
            })
            continue

        pm_flags = []
        if abs((snapshot - pm_time).total_seconds()) > tolerance:
            pm_flags.append("stale_pm_quote")
        yes_bid = _finite(pm.get("yes_bid"), "yes_bid", allow_zero=True)
        yes_ask = _finite(pm.get("yes_ask"), "yes_ask", allow_zero=True)
        no_bid = _finite(pm.get("no_bid"), "no_bid", allow_zero=True)
        no_ask = _finite(pm.get("no_ask"), "no_ask", allow_zero=True)
        if yes_bid > yes_ask or no_bid > no_ask or yes_ask > payout or no_ask > payout:
            pm_flags.append("invalid_or_crossed_pm_book")
        elif (yes_ask - yes_bid) / payout > max_pm_spread:
            pm_flags.append("wide_pm_spread")

        chain = []
        for option_time, delta, option in sorted(options, key=lambda row: (float(row[2]["strike"]), row[0])):
            option_flags = _option_quality(option, snapshot, tolerance, max_option_spread)
            option_row = dict(option)
            option_row["quote_time_delta_seconds"] = delta
            option_row["quality_flags"] = option_flags
            option_row["usable"] = not option_flags
            chain.append(option_row)
            if option_row["usable"] and option.get("option_id") is not None:
                unique_usable_option_ids.add(str(option["option_id"]))

        all_flags = sorted(set(pm_flags + [flag for option in chain for flag in option["quality_flags"]]))
        results.append({
            "contract_id": pm.get("contract_id"),
            "threshold": pm_threshold,
            "alignment_status": "matched",
            "pm_quality_flags": sorted(set(pm_flags)),
            "listed_chain_quality_flags": sorted(set(flag for option in chain for flag in option["quality_flags"])),
            "quality_flags": all_flags,
            "usable_for_curve": not pm_flags,
            "pm": dict(pm),
            "listed_option_chain": chain,
        })

    results.sort(key=lambda row: (row["threshold"], row["contract_id"] or ""))
    return {
        "schema_version": "options.aligned_inputs.v1",
        "fixture_status": fixture_status,
        "status": "synthetic_only" if fixture_status == "synthetic" else "authorized_alignment",
        "real_data_enabled": fixture_status == "real" and _rights_clear(document),
        "source_use_status": document.get("source_use_status", {}),
        "snapshot_time": document.get("snapshot_time"),
        "quote_tolerance_seconds": tolerance,
        "max_pm_spread_fraction": max_pm_spread,
        "max_listed_relative_spread": max_option_spread,
        "rows": results,
        "counts": {
            "pm_contracts": len(pm_contracts),
            "matched": sum(row["alignment_status"] == "matched" for row in results),
            "usable_for_curve": sum(row.get("usable_for_curve", False) for row in results),
            "unmatched": sum(row["alignment_status"] != "matched" for row in results),
            "unique_usable_listed_quotes": len(unique_usable_option_ids),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = align_inputs(json.loads(args.input.read_text(encoding="utf-8")))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
