#!/usr/bin/env python3
"""Compare synthetic PM-derived BS-equivalent IV with matched European calls."""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from typing import Any


def _normal_cdf(value: float) -> float:
    return 0.5 * (1.0 + math.erf(value / math.sqrt(2.0)))


def _positive(value: Any, field: str, allow_zero: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value):
        raise ValueError(f"{field} must be a finite number")
    result = float(value)
    if result < 0 if allow_zero else result <= 0:
        raise ValueError(f"{field} must be {'nonnegative' if allow_zero else 'positive'}")
    return result


def bs_call_price(spot: float, strike: float, time_years: float,
                  rate: float, dividend_yield: float, volatility: float) -> float:
    """European Black–Scholes call value with continuous rate and dividend yields."""
    spot = _positive(spot, "spot")
    strike = _positive(strike, "strike")
    time_years = _positive(time_years, "time_years", allow_zero=True)
    volatility = _positive(volatility, "volatility", allow_zero=True)
    if not math.isfinite(rate) or not math.isfinite(dividend_yield):
        raise ValueError("rate and dividend_yield must be finite")
    if time_years == 0:
        return max(spot - strike, 0.0)
    if volatility == 0:
        return max(spot * math.exp(-dividend_yield * time_years)
                   - strike * math.exp(-rate * time_years), 0.0)
    vol_sqrt_t = volatility * math.sqrt(time_years)
    d1 = (math.log(spot / strike)
          + (rate - dividend_yield + 0.5 * volatility * volatility) * time_years) / vol_sqrt_t
    d2 = d1 - vol_sqrt_t
    return (spot * math.exp(-dividend_yield * time_years) * _normal_cdf(d1)
            - strike * math.exp(-rate * time_years) * _normal_cdf(d2))


def implied_volatility(call_price: float, spot: float, strike: float, time_years: float,
                       rate: float, dividend_yield: float,
                       tolerance: float = 1e-12, max_volatility: float = 8.0) -> dict[str, Any]:
    """Invert a European call price by bisection, returning an explicit failure reason."""
    values = [call_price, spot, strike, time_years, rate, dividend_yield]
    if any(not math.isfinite(value) for value in values):
        return {"iv": None, "valid": False, "reason": "non_finite_input"}
    if spot <= 0 or strike <= 0 or time_years <= 0:
        return {"iv": None, "valid": False, "reason": "spot_strike_and_time_must_be_positive"}
    discounted_spot = spot * math.exp(-dividend_yield * time_years)
    discounted_strike = strike * math.exp(-rate * time_years)
    lower_bound = max(discounted_spot - discounted_strike, 0.0)
    upper_bound = discounted_spot
    scale_tol = tolerance * max(1.0, spot, strike, abs(call_price))
    if call_price < lower_bound - scale_tol or call_price > upper_bound + scale_tol:
        return {"iv": None, "valid": False, "reason": "outside_european_call_bounds",
                "lower_bound": lower_bound, "upper_bound": upper_bound}
    if abs(call_price - lower_bound) <= scale_tol:
        return {"iv": 0.0, "valid": True, "reason": None,
                "lower_bound": lower_bound, "upper_bound": upper_bound}
    if call_price >= upper_bound - scale_tol:
        return {"iv": None, "valid": False, "reason": "no_finite_iv_at_upper_bound",
                "lower_bound": lower_bound, "upper_bound": upper_bound}

    low, high = 0.0, 0.5
    while high < max_volatility and bs_call_price(spot, strike, time_years, rate, dividend_yield, high) < call_price:
        high = min(max_volatility, high * 2.0)
    if bs_call_price(spot, strike, time_years, rate, dividend_yield, high) < call_price:
        return {"iv": None, "valid": False, "reason": "volatility_bracket_not_found",
                "lower_bound": lower_bound, "upper_bound": upper_bound}
    for _ in range(120):
        mid = (low + high) / 2.0
        model_price = bs_call_price(spot, strike, time_years, rate, dividend_yield, mid)
        if model_price < call_price:
            low = mid
        else:
            high = mid
        if high - low < 1e-12:
            break
    return {"iv": (low + high) / 2.0, "valid": True, "reason": None,
            "lower_bound": lower_bound, "upper_bound": upper_bound}


def _match_key(row: dict[str, Any]) -> tuple[Any, ...]:
    return (
        row.get("underlying"), row.get("expiry"), row.get("snapshot_time"),
        float(row.get("strike")), str(row.get("option_style", "")).lower(),
        str(row.get("option_type", "")).lower(),
    )


def _iv_bounds(low_price: float, high_price: float, row: dict[str, Any]) -> dict[str, Any]:
    lower = implied_volatility(
        low_price, row["spot"], row["strike"], row["time_years"],
        row["rate"], row["dividend_yield"],
    )
    upper = implied_volatility(
        high_price, row["spot"], row["strike"], row["time_years"],
        row["rate"], row["dividend_yield"],
    )
    return {
        "lower": lower["iv"] if lower["valid"] else None,
        "upper": upper["iv"] if upper["valid"] else None,
        "lower_valid": lower["valid"],
        "upper_valid": upper["valid"],
        "lower_reason": lower["reason"],
        "upper_reason": upper["reason"],
    }


def compare_surfaces(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "options.iv_comparison.v1":
        raise ValueError("schema_version must be 'options.iv_comparison.v1'")
    if document.get("fixture_status") != "synthetic":
        raise ValueError("only explicitly synthetic inputs are accepted")
    pm_calls = document.get("pm_calls", [])
    listed_calls = document.get("listed_calls", [])
    listed_by_key: dict[tuple[Any, ...], dict[str, Any]] = {}
    for row in listed_calls:
        key = _match_key(row)
        if key in listed_by_key:
            raise ValueError(f"duplicate listed-call key: {key}")
        listed_by_key[key] = row

    rows = []
    for pm in pm_calls:
        row = {
            "underlying": pm.get("underlying"),
            "expiry": pm.get("expiry"),
            "snapshot_time": pm.get("snapshot_time"),
            "strike": pm.get("strike"),
            "option_style": pm.get("option_style"),
            "option_type": pm.get("option_type"),
            "price_basis": pm.get("price_basis"),
            "pm_call_price_interval": {
                "lower": pm.get("price_lower"),
                "upper": pm.get("price_upper"),
            },
        }
        try:
            strike = _positive(pm.get("strike"), "strike")
            spot = _positive(pm.get("spot"), "spot")
            time_years = _positive(pm.get("time_years"), "time_years")
            rate = float(pm["rate"])
            dividend_yield = float(pm["dividend_yield"])
            if not math.isfinite(rate) or not math.isfinite(dividend_yield):
                raise ValueError("rate and dividend_yield must be finite")
            row["spot"] = spot
            row["time_years"] = time_years
            row["valuation_assumptions"] = {
                "rate_continuous": rate,
                "dividend_yield_continuous": dividend_yield,
                "model": "European Black–Scholes; continuous compounding",
            }
            price_low = _positive(pm.get("price_lower"), "price_lower", allow_zero=True)
            price_high = _positive(pm.get("price_upper"), "price_upper", allow_zero=True)
            if price_low > price_high:
                raise ValueError("price_lower must not exceed price_upper")
            if pm.get("price_basis") != "present_value_per_unit_payout":
                raise ValueError("PM synthetic call must be a present-value equivalent")
            if str(pm.get("option_style", "")).lower() != "european":
                raise ValueError("PM equivalent must use the European call convention")
            if str(pm.get("option_type", "")).lower() != "call":
                raise ValueError("only call-equivalent values are supported")
            pm_iv = _iv_bounds(price_low, price_high, {
                "spot": spot, "strike": strike, "time_years": time_years,
                "rate": rate, "dividend_yield": dividend_yield,
            })
            row["pm_iv"] = pm_iv
        except (KeyError, TypeError, ValueError, OverflowError) as exc:
            row.update({"pm_iv": None, "status": "invalid_pm_input", "reason": str(exc)})
            rows.append(row)
            continue

        listed = listed_by_key.get(_match_key(pm))
        if listed is None:
            row.update({"status": "unmatched_listed_quote", "reason": "no exact metadata match"})
            rows.append(row)
            continue
        if str(listed.get("option_style", "")).lower() != "european" or str(listed.get("option_type", "")).lower() != "call":
            row.update({"status": "ineligible_listed_style_or_type", "reason": "benchmark must be a European call"})
            rows.append(row)
            continue
        valuation_fields = ("spot", "time_years", "rate", "dividend_yield")
        try:
            mismatch = any(
                not math.isclose(float(pm[field]), float(listed[field]), rel_tol=0, abs_tol=1e-12)
                for field in valuation_fields
            )
        except (KeyError, TypeError, ValueError):
            row.update({"status": "invalid_listed_metadata", "reason": "listed valuation inputs are missing or invalid"})
            rows.append(row)
            continue
        if mismatch:
            row.update({"status": "valuation_input_mismatch", "reason": "spot, time, rate, and dividend yield must match"})
            rows.append(row)
            continue
        try:
            bid = _positive(listed.get("bid"), "listed bid", allow_zero=True)
            ask = _positive(listed.get("ask"), "listed ask", allow_zero=True)
            if bid > ask:
                raise ValueError("listed bid must not exceed ask")
        except (TypeError, ValueError) as exc:
            row.update({"status": "invalid_listed_quote", "reason": str(exc)})
            rows.append(row)
            continue

        listed_iv = _iv_bounds(bid, ask, {
            "spot": spot, "strike": strike, "time_years": time_years,
            "rate": rate, "dividend_yield": dividend_yield,
        })
        row["listed_iv"] = listed_iv
        row["listed_call_bid_ask"] = {"bid": bid, "ask": ask}
        row["time_years"] = time_years
        row["log_moneyness"] = math.log(strike / (spot * math.exp((rate - dividend_yield) * time_years)))
        if all((pm_iv["lower_valid"], pm_iv["upper_valid"],
                listed_iv["lower_valid"], listed_iv["upper_valid"])):
            gap_low = pm_iv["lower"] - listed_iv["upper"]
            gap_high = pm_iv["upper"] - listed_iv["lower"]
            row["delta_iv"] = {
                "lower": gap_low,
                "upper": gap_high,
                "midpoint": (gap_low + gap_high) / 2.0,
                "units": "volatility points",
                "lower_percentage_points": 100.0 * gap_low,
                "upper_percentage_points": 100.0 * gap_high,
                "midpoint_percentage_points": 50.0 * (gap_low + gap_high),
            }
            row["status"] = "candidate_dislocation_only"
            row["claim_label"] = "candidate volatility dislocation; not evidence of a proven or tradable mispricing"
        else:
            row["status"] = "invalid_iv_inversion"
            row["reason"] = "one or more price bounds have no valid finite implied volatility"
            row["delta_iv"] = None
        rows.append(row)

    return {
        "schema_version": "options.iv_surface_comparison.v1",
        "fixture_status": "synthetic",
        "label": "PM-derived Black–Scholes-equivalent IV vs listed European-option IV",
        "interpretation": "The PM-derived surface is a model transformation of binary prices, not a listed IV quote or a calibrated real-world forecast.",
        "candidate_gap_warning": "A delta-IV gap alone does not establish mispricing, profitability, or tradability.",
        "rows": rows,
        "summary": {
            "pm_rows": len(pm_calls),
            "matched_rows": sum(row.get("status") == "candidate_dislocation_only" for row in rows),
            "unmatched_or_invalid_rows": sum(row.get("status") != "candidate_dislocation_only" for row in rows),
        },
    }


def plot_comparison(comparison: dict[str, Any], output_path: Path) -> None:
    """Write a labeled scatter-surface view for available matched synthetic cells."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    usable = [row for row in comparison.get("rows", [])
              if row.get("status") == "candidate_dislocation_only" and row.get("delta_iv") is not None]
    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), constrained_layout=True)
    specs = [
        ("pm_iv", "PM-derived BS-equivalent IV midpoint (%)", lambda r: 50 * (r["pm_iv"]["lower"] + r["pm_iv"]["upper"])),
        ("listed_iv", "Listed European IV midpoint (%)", lambda r: 50 * (r["listed_iv"]["lower"] + r["listed_iv"]["upper"])),
        ("delta_iv", "ΔIV midpoint (volatility points)", lambda r: r["delta_iv"]["midpoint_percentage_points"]),
    ]
    for ax, (_, title, get_value) in zip(axes, specs):
        ax.set_title(title)
        ax.set_xlabel("Log-moneyness ln(K/F)")
        ax.set_ylabel("Time to expiry (years)")
        if usable:
            x = [row["log_moneyness"] for row in usable]
            y = [float(row.get("time_years", 0.0)) for row in usable]
            values = [get_value(row) for row in usable]
            scatter = ax.scatter(x, y, c=values, cmap="coolwarm", s=100, edgecolors="black")
            fig.colorbar(scatter, ax=ax, label=title)
        else:
            ax.text(0.5, 0.5, "No matched valid cells", ha="center", va="center", transform=ax.transAxes)
        ax.grid(alpha=0.25)
    fig.suptitle("Synthetic example — candidate gaps are not proven mispricings")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--plot", type=Path)
    args = parser.parse_args()
    document = json.loads(args.input.read_text(encoding="utf-8"))
    result = compare_surfaces(document)
    encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(encoded, encoding="utf-8")
    if args.plot:
        plot_comparison(result, args.plot)


if __name__ == "__main__":
    main()
