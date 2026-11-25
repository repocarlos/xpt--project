#!/usr/bin/env python3
"""Synthetic call-equivalent reconstruction from a terminal digital curve.

This module does not collect venue data. It integrates unit-payout digital
prices only when a caller supplies a curve; outputs preserve the input price
basis and expose strike-tail assumptions instead of hiding them.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


ALLOWED_BASES = {"present_value_per_unit_payout", "undiscounted_event_price"}


def _finite_number(value: Any, field: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    return float(value)


def _interpolate(points: list[tuple[float, float]], strike: float) -> float:
    if strike <= points[0][0]:
        return points[0][1]
    for (x0, y0), (x1, y1) in zip(points, points[1:]):
        if x0 <= strike <= x1:
            weight = (strike - x0) / (x1 - x0)
            return y0 + weight * (y1 - y0)
    return points[-1][1]


def _integrate(points: list[tuple[float, float]], start: float, end: float,
               method: str = "piecewise_linear") -> float:
    """Integrate one explicit interpolation scenario over [start, end]."""
    if end < start:
        raise ValueError("integration end must be at or above start")
    if end == start:
        return 0.0
    if method in {"left_step", "right_step"}:
        cuts = [start, *[x for x, _ in points if start < x < end], end]
        total = 0.0
        for left, right in zip(cuts, cuts[1:]):
            midpoint = (left + right) / 2.0
            segment = next(i for i in range(len(points) - 1)
                           if points[i][0] <= midpoint < points[i + 1][0])
            value_index = segment if method == "left_step" else segment + 1
            total += (right - left) * points[value_index][1]
        return total
    if method != "piecewise_linear":
        raise ValueError("interpolation_method must be piecewise_linear, left_step, or right_step")
    interior = [(x, y) for x, y in points if start < x < end]
    curve = [(start, _interpolate(points, start)), *interior, (end, _interpolate(points, end))]
    return sum((x1 - x0) * (y0 + y1) / 2.0 for (x0, y0), (x1, y1) in zip(curve, curve[1:]))


def _is_nonincreasing(values: list[float], tol: float = 1e-12) -> bool:
    return all(right <= left + tol for left, right in zip(values, values[1:]))


def reconstruct_calls(document: dict[str, Any]) -> dict[str, Any]:
    """Return synthetic call-equivalent ranges and explicit quality/tail flags."""
    if document.get("schema_version") != "options.digital_curve.v1":
        raise ValueError("schema_version must be 'options.digital_curve.v1'")
    if document.get("fixture_status") != "synthetic":
        raise ValueError("only explicitly synthetic inputs are accepted by this research fixture")
    price_basis = document.get("price_basis")
    if price_basis not in ALLOWED_BASES:
        raise ValueError(f"price_basis must be one of {sorted(ALLOWED_BASES)}")

    payout = _finite_number(document.get("payout"), "payout")
    if payout <= 0:
        raise ValueError("payout must be positive")
    discount_factor = document.get("discount_factor")
    if discount_factor is not None:
        discount_factor = _finite_number(discount_factor, "discount_factor")
        if not 0 < discount_factor <= 1:
            raise ValueError("discount_factor must be in (0, 1]")
        if price_basis == "present_value_per_unit_payout":
            raise ValueError("discount_factor must be omitted for already-present-value quotes")

    raw_points = document.get("points")
    if not isinstance(raw_points, list) or len(raw_points) < 2:
        raise ValueError("points must contain at least two rows")
    points: list[dict[str, Any]] = []
    for index, row in enumerate(raw_points):
        if not isinstance(row, dict):
            raise ValueError(f"points[{index}] must be an object")
        threshold = _finite_number(row.get("threshold"), f"points[{index}].threshold")
        bid = _finite_number(row.get("bid"), f"points[{index}].bid")
        ask = _finite_number(row.get("ask"), f"points[{index}].ask")
        if bid < 0 or ask > payout or bid > ask:
            raise ValueError(f"points[{index}] must satisfy 0 <= bid <= ask <= payout")
        points.append({
            "threshold": threshold,
            "bid": bid / payout,
            "ask": ask / payout,
            "quote_status": row.get("quote_status", "usable"),
            "contract_id": row.get("contract_id"),
        })
    points.sort(key=lambda row: row["threshold"])
    strikes = [row["threshold"] for row in points]
    if len(set(strikes)) != len(strikes):
        raise ValueError("thresholds must be unique")
    usable = [row for row in points if row["quote_status"] == "usable"]
    excluded_ids = [row["contract_id"] for row in points if row["quote_status"] != "usable"]
    if len(usable) < 2:
        raise ValueError("at least two usable quote rows are required")

    bid_curve = [(row["threshold"], row["bid"]) for row in usable]
    ask_curve = [(row["threshold"], row["ask"]) for row in usable]
    bid_monotone = _is_nonincreasing([y for _, y in bid_curve])
    ask_monotone = _is_nonincreasing([y for _, y in ask_curve])
    curve_monotone = bid_monotone and ask_monotone
    low_strike, high_strike = usable[0]["threshold"], usable[-1]["threshold"]
    interpolation_method = document.get("interpolation_method", "piecewise_linear")
    if interpolation_method not in {"piecewise_linear", "left_step", "right_step"}:
        raise ValueError("interpolation_method must be piecewise_linear, left_step, or right_step")

    basis_factor = discount_factor if price_basis == "undiscounted_event_price" and discount_factor is not None else 1.0
    value_kind = (
        "synthetic_call_present_value_equivalent"
        if price_basis == "present_value_per_unit_payout" or discount_factor is not None
        else "undiscounted_event_price_integral"
    )

    requested = document.get("requested_strikes", strikes)
    if not isinstance(requested, list):
        raise ValueError("requested_strikes must be a list")
    tail_config = document.get("tail")
    tail_cap = None
    scenarios: list[dict[str, Any]] = []
    if tail_config is not None:
        tail_cap = _finite_number(tail_config.get("cap"), "tail.cap")
        if tail_cap <= high_strike:
            raise ValueError("tail.cap must be above the highest usable threshold")
        scenarios = tail_config.get("scenarios", [])
        if not isinstance(scenarios, list):
            raise ValueError("tail.scenarios must be a list")
        for index, scenario in enumerate(scenarios):
            if not isinstance(scenario, dict) or not isinstance(scenario.get("name"), str):
                raise ValueError(f"tail.scenarios[{index}] must have a string name")
            fraction = _finite_number(scenario.get("remaining_fraction"), f"tail.scenarios[{index}].remaining_fraction")
            if not 0 <= fraction <= 1:
                raise ValueError("remaining_fraction must be in [0, 1]")

    outputs = []
    for requested_value in requested:
        strike = _finite_number(requested_value, "requested strike")
        outside = strike < low_strike or strike > high_strike
        result: dict[str, Any] = {
            "strike": strike,
            "observed_coverage": [low_strike, high_strike],
            "outside_observed_coverage": outside,
            "quote_status_warning": bool(excluded_ids),
            "excluded_contract_ids": excluded_ids,
            "bid_curve_nonincreasing": bid_monotone,
            "ask_curve_nonincreasing": ask_monotone,
            "curve_monotone": curve_monotone,
            "eligible_for_model_use": (
                not outside and curve_monotone and not excluded_ids
                and tail_cap is not None and bool(scenarios)
            ),
            "observed_range_call": None,
            "tail_scenarios": [],
            "tail_unknown": tail_cap is None or not scenarios,
        }
        if outside:
            outputs.append(result)
            continue

        observed_low = _integrate(bid_curve, strike, high_strike, interpolation_method) * basis_factor
        observed_high = _integrate(ask_curve, strike, high_strike, interpolation_method) * basis_factor
        result["observed_range_call"] = {
            "lower": observed_low,
            "upper": observed_high,
            "integration_domain": [strike, high_strike],
            "interpolation_method": interpolation_method,
            "units": "underlying_price_units_per_underlying_unit",
            "value_kind": value_kind,
        }
        if tail_cap is not None:
            tail_width = tail_cap - high_strike
            last_bid = bid_curve[-1][1]
            last_ask = ask_curve[-1][1]
            for scenario in scenarios:
                fraction = float(scenario["remaining_fraction"])
                tail_low = tail_width * (last_bid + last_bid * fraction) / 2.0 * basis_factor
                tail_high = tail_width * (last_ask + last_ask * fraction) / 2.0 * basis_factor
                result["tail_scenarios"].append({
                    "name": str(scenario["name"]),
                    "assumption": (
                        f"linearly moves from the last observed digital price to "
                        f"{fraction:g} of that price at cap {tail_cap:g}, then zero beyond cap"
                    ),
                    "cap": tail_cap,
                    "tail_lower": tail_low,
                    "tail_upper": tail_high,
                    "total_lower": observed_low + tail_low,
                    "total_upper": observed_high + tail_high,
                    "value_kind": value_kind,
                })
        outputs.append(result)

    convention = document.get("price_convention")
    if not isinstance(convention, str) or not convention.strip():
        raise ValueError("price_convention must state what the quote values represent")
    return {
        "schema_version": "options.synthetic_call_reconstruction.v1",
        "fixture_status": "synthetic",
        "label": "synthetic call-equivalent values; not listed option quotes",
        "underlying": document.get("underlying"),
        "expiry": document.get("expiry"),
        "event_relation": document.get("event_relation"),
        "price_basis": price_basis,
        "price_convention": convention,
        "payout": payout,
        "discount_factor": discount_factor,
        "tail_cap": tail_cap,
        "tail_beyond_cap_assumption": "zero digital value beyond the declared cap within each displayed scenario",
        "warning": (
            "An integrated PM event-price curve is not automatically an arbitrage-free option price "
            "or a risk-neutral distribution."
        ),
        "inputs": points,
        "results": outputs,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path, help="synthetic digital-curve JSON")
    parser.add_argument("--output", type=Path, help="write JSON here instead of stdout")
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    result = reconstruct_calls(document)
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    if args.output:
        args.output.write_text(encoded, encoding="utf-8")
    else:
        print(encoded, end="")


if __name__ == "__main__":
    main()
