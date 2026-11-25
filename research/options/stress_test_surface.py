#!/usr/bin/env python3
"""Run synthetic interpolation, quote-side, tail, and discounting sensitivities."""
from __future__ import annotations
import argparse, copy, json
from pathlib import Path
from typing import Any
from research.options.compare_iv_surfaces import compare_surfaces, plot_comparison
from research.options.reconstruct_calls import reconstruct_calls

def _quote_sides(curve: dict[str, Any], side: str) -> dict[str, Any]:
    output = copy.deepcopy(curve)
    if side == "quoted_interval": return output
    for point in output["points"]:
        if side == "bid": point["ask"] = point["bid"]
        elif side == "ask": point["bid"] = point["ask"]
        elif side == "mid":
            midpoint = (point["bid"] + point["ask"]) / 2.0
            point["bid"] = point["ask"] = midpoint
        else: raise ValueError(f"unknown quote-side scenario: {side}")
    return output

def _summarize_gaps(rows: list[dict[str, Any]]) -> dict[str, Any]:
    gaps = [row["delta_iv"]["midpoint_percentage_points"] for row in rows
            if row.get("status") == "candidate_dislocation_only" and row.get("delta_iv") is not None]
    return {"valid_iv_cells": len(gaps), "invalid_or_unmatched_cells": len(rows)-len(gaps),
            "minimum_delta_iv_midpoint_percentage_points": min(gaps) if gaps else None,
            "maximum_delta_iv_midpoint_percentage_points": max(gaps) if gaps else None}

def run_sensitivity(document: dict[str, Any]) -> dict[str, Any]:
    if document.get("schema_version") != "options.sensitivity.v1":
        raise ValueError("schema_version must be 'options.sensitivity.v1'")
    if document.get("fixture_status") != "synthetic":
        raise ValueError("only explicitly synthetic sensitivity inputs are accepted")
    listed_calls = document.get("listed_calls", [])
    output_scenarios = []
    quote_sides = ("quoted_interval", "bid", "mid", "ask")
    interpolation_methods = ("piecewise_linear", "left_step", "right_step")
    discount_modes = ("apply_discount_factor", "no_discount_factor")
    for source_curve in document.get("digital_curves", []):
        base_tail = source_curve.get("tail")
        if not base_tail or not base_tail.get("scenarios"):
            raise ValueError("each digital curve requires declared tail scenarios")
        expiry = source_curve.get("expiry")
        for quote_side in quote_sides:
            for interpolation in interpolation_methods:
                for tail_scenario in base_tail["scenarios"]:
                    for discount_mode in discount_modes:
                        curve = _quote_sides(source_curve, quote_side)
                        curve["interpolation_method"] = interpolation
                        curve["tail"]["scenarios"] = [copy.deepcopy(tail_scenario)]
                        if discount_mode == "no_discount_factor": curve.pop("discount_factor", None)
                        reconstructed = reconstruct_calls(curve)
                        pm_calls, call_rows = [], []
                        for result in reconstructed["results"]:
                            if result["outside_observed_coverage"] or not result["tail_scenarios"]: continue
                            calls = result["tail_scenarios"][0]
                            basis = ("present_value_per_unit_payout" if calls["value_kind"] == "synthetic_call_present_value_equivalent"
                                     else "undiscounted_event_price")
                            pm_calls.append({"underlying":curve["underlying"],"expiry":curve["expiry"],
                                "snapshot_time":curve["snapshot_time"],"strike":result["strike"],
                                "option_style":"European","option_type":"call","price_basis":basis,
                                "price_lower":calls["total_lower"],"price_upper":calls["total_upper"],
                                "spot":curve["spot"],"time_years":curve["time_years"],
                                "rate":curve["rate"],"dividend_yield":curve["dividend_yield"]})
                            call_rows.append({"strike":result["strike"],
                                "observed_range_lower":result["observed_range_call"]["lower"],
                                "observed_range_upper":result["observed_range_call"]["upper"],
                                "tail_lower":calls["tail_lower"],"tail_upper":calls["tail_upper"],
                                "total_lower":calls["total_lower"],"total_upper":calls["total_upper"],"price_basis":basis})
                        comparison = compare_surfaces({"schema_version":"options.iv_comparison.v1",
                            "fixture_status":"synthetic","pm_calls":pm_calls,"listed_calls":listed_calls})
                        comparison_rows = []
                        for row in comparison["rows"]:
                            comparison_rows.append({key: row[key] for key in (
                                "underlying", "expiry", "snapshot_time", "strike", "option_style",
                                "option_type", "price_basis", "pm_iv", "listed_iv", "delta_iv",
                                "log_moneyness", "time_years", "status", "reason", "claim_label",
                            ) if key in row})
                        scenario_name = (f"{expiry}|quote={quote_side}|interp={interpolation}|"
                            f"tail={tail_scenario['name']}|discount={discount_mode}")
                        output_scenarios.append({"scenario":scenario_name,"expiry":expiry,
                            "contract_terms":{
                                "underlying":curve["underlying"],
                                "event_relation":curve.get("event_relation"),
                                "expiry":curve["expiry"],
                                "snapshot_time":curve["snapshot_time"],
                                "time_years":curve["time_years"],
                                "payout":curve["payout"],
                                "threshold_coverage":[min(p["threshold"] for p in curve["points"]),max(p["threshold"] for p in curve["points"])],
                                "requested_call_strikes":curve["requested_strikes"],
                                "listed_benchmark_style":"synthetic European calls",
                            },
                            "assumptions":{"quote_side":quote_side,"interpolation_method":interpolation,
                                "tail_scenario":tail_scenario["name"],"discount_mode":discount_mode},
                            "digital_curve":[{"threshold":p["threshold"],"bid":p["bid"],"ask":p["ask"]} for p in curve["points"]],
                            "synthetic_calls":call_rows,"comparison_rows":comparison_rows,
                            "gap_summary":_summarize_gaps(comparison_rows)})
    return {"schema_version":"options.sensitivity_results.v1","fixture_status":"synthetic",
        "label":"assumption sensitivity on synthetic PM-like prices and synthetic listed-option quotes",
        "validation_status":"no empirical calibration or outcome validation",
        "warning":"Scenario gaps are synthetic diagnostics only. They do not show observed market disagreement, a forecast advantage, mispricing, profitability, or tradability.",
        "scenario_count":len(output_scenarios),"scenarios":output_scenarios}

def render_handoff(results: dict[str, Any], command: str) -> str:
    by_expiry: dict[str, list[dict[str, Any]]] = {}
    for scenario in results["scenarios"]: by_expiry.setdefault(scenario["expiry"], []).append(scenario)
    lines=["# Options surface stress test — synthetic handoff","",
        "**Evidence state:** synthetic fixture only. No observed PM prices, actual listed-option quotes, or resolved outcomes were used.","",
        "**Recommendation:** stop empirical publication and trading claims until source use is approved and exact matched historical inputs are available. Continue only as a method prototype.","",
        "## What the pipeline represents","",
        "- Digital thresholds: synthetic PM-like bid/ask prices.",
        "- Transformed estimates: integrated synthetic call-equivalent ranges and European Black–Scholes-equivalent IV ranges.",
        "- Listed benchmark: synthetic European call quotes generated for testing, not exchange observations.",
        "- Validation: arithmetic and handling tests passed; no forecast calibration or executable trading validation.","",
        "## Sensitivity coverage","",
        f"- Scenario count: {results['scenario_count']}.",
        "- Axes: quote side (quoted interval, bid, mid, ask); interpolation (piecewise linear, left step, right step); declared tail scenarios; discount factor applied vs omitted.",
        "- Missing or invalid IV cells stay visible with a reason; no missing quotes are filled.","",
        "| Expiry | Scenarios | ΔIV midpoint range (percentage points) | Valid IV cells | Invalid/unmatched cells |",
        "|---|---:|---:|---:|---:|"]
    for expiry, scenarios in sorted(by_expiry.items()):
        gaps=[r["delta_iv"]["midpoint_percentage_points"] for s in scenarios for r in s["comparison_rows"]
            if r.get("status")=="candidate_dislocation_only" and r.get("delta_iv") is not None]
        valid=len(gaps); total=sum(len(s["comparison_rows"]) for s in scenarios)
        gap_range=f"{min(gaps):.3f} to {max(gaps):.3f}" if gaps else "not available"
        lines.append(f"| {expiry} | {len(scenarios)} | {gap_range} | {valid} | {total-valid} |")
    lines.extend(["","## Synthetic contract terms","",])
    for expiry, scenarios in sorted(by_expiry.items()):
        terms = scenarios[0]["contract_terms"]
        lines.append(
            f"- {expiry}: {terms['underlying']} terminal event {terms['event_relation']} K; "
            f"snapshot {terms['snapshot_time']}; synthetic horizon {terms['time_years']} years; "
            f"payout {terms['payout']}; threshold coverage {terms['threshold_coverage'][0]:g}–"
            f"{terms['threshold_coverage'][1]:g}; requested call strikes "
            f"{', '.join(f'{x:g}' for x in terms['requested_call_strikes'])}."
        )
        lines.append("  Observed venue/source and settlement references: unavailable; all thresholds are synthetic.")
    lines.extend(["","The numeric ranges above are sensitivities of synthetic examples only; they are not current market gaps.","",
        "## Reproduction","",f"    {command}","",
        "## Gates before an empirical rerun","",
        "1. Confirm source permission separately for collection, raw storage, derivation, team sharing, and display.",
        "2. Match terminal event, threshold orientation, underlying reference, expiry, settlement time/source, and European option style.",
        "3. Obtain synchronized two-sided PM and listed-option quotes with sizes and documented quote freshness.",
        "4. Approve strike coverage, timestamp tolerance, interpolation, tail, rates, dividends, and discounting conventions.",
        "5. Keep any later tradability claim behind executable costs, hedge/funding assumptions, capacity, and held-out evaluation.","",
        "An IV difference by itself is a candidate dislocation only, not proof of mispricing or an edge.",""])
    return "\n".join(lines)

def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input",type=Path); parser.add_argument("--output",type=Path,required=True)
    parser.add_argument("--report",type=Path,required=True); parser.add_argument("--plot",type=Path)
    args=parser.parse_args(); document=json.loads(args.input.read_text(encoding="utf-8"))
    results=run_sensitivity(document)
    command=(f"python3 -m research.options.stress_test_surface {args.input} --output {args.output} --report {args.report}"+
        (f" --plot {args.plot}" if args.plot else ""))
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(results,indent=2,sort_keys=True,allow_nan=False)+"\n",encoding="utf-8")
    args.report.parent.mkdir(parents=True,exist_ok=True); args.report.write_text(render_handoff(results,command),encoding="utf-8")
    if args.plot:
        baseline=next(s["comparison_rows"] for s in results["scenarios"]
            if s["assumptions"]["quote_side"]=="quoted_interval"
            and s["assumptions"]["interpolation_method"]=="piecewise_linear"
            and s["assumptions"]["discount_mode"]=="apply_discount_factor")
        plot_comparison({"rows":baseline},args.plot)

if __name__=="__main__": main()
