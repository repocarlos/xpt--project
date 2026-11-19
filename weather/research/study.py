"""Family-isolated coordinator for approved weather comparison packages."""

from __future__ import annotations

from typing import Any, Iterable, Mapping

from weather.research.baseline import compare_models
from weather.research.calibration import evaluate_chronological_holdout


_GATES = (
    ("cohort_status", "selected", "cohort_not_selected"),
    ("source_use_status", "approved", "source_use_unapproved"),
    ("settlement_status", "verified", "settlement_unverified"),
    ("coverage_status", "verified", "coverage_unverified"),
)


def run_weather_study(
    family_packages: Iterable[Mapping[str, Any]], *,
    holdout_fraction: float,
    min_holdout_events_by_family: Mapping[str, int],
    reliability_bins: int = 10,
) -> dict[str, Any]:
    """Build separate family outputs; fail closed before touching package records."""
    outputs = []
    seen_cohorts: set[str] = set()
    for package in family_packages:
        reasons = _gate_reasons(package)
        cohort_id = package.get("cohort_id")
        if not isinstance(cohort_id, str) or not cohort_id:
            reasons.append("cohort_id_missing")
        elif cohort_id in seen_cohorts:
            reasons.append("duplicate_cohort_id")
        else:
            seen_cohorts.add(cohort_id)
        family = package.get("family")
        if not isinstance(family, str) or not family:
            reasons.append("family_missing")
        if reasons:
            outputs.append({
                "family": family,
                "cohort_id": cohort_id,
                "status": "blocked",
                "reasons": sorted(set(reasons)),
                "comparisons": [],
                "calibration": None,
                "evidence_class": "pending",
                "claim_status": "pending",
            })
            continue

        # Package records are only iterated after selection, rights, mapping, and reviewer gates pass.
        comparisons = []
        pairs = package.get("market_pairs", [])
        if not isinstance(pairs, list):
            raise ValueError("market_pairs must be a list")
        for pair in pairs:
            comparisons.extend(compare_models(
                pair["market"], pair["forecasts"], decision_at=pair["decision_at"],
                max_quote_age_seconds=pair["max_quote_age_seconds"],
                transaction_cost=pair.get("transaction_cost", 0.0),
                candidate_gap_threshold=pair.get("candidate_gap_threshold", 0.05),
            ))
        calibration = None
        calibration_status = "insufficient"
        calibration_records = package.get("calibration_records", [])
        if not isinstance(calibration_records, list):
            raise ValueError("calibration_records must be a list")
        if len({row.get("event_id") for row in calibration_records}) >= 2:
            threshold = min_holdout_events_by_family.get(family)
            if threshold is None:
                raise ValueError(f"minimum holdout event policy missing for family: {family}")
            try:
                calibration = evaluate_chronological_holdout(
                    calibration_records,
                    holdout_fraction=holdout_fraction,
                    bins=reliability_bins,
                    min_events_per_bin=1,
                    min_holdout_events=threshold,
                )
                calibration_status = "sparse" if calibration["sparse_holdout"] else "scored"
            except ValueError as exc:
                calibration_status = "insufficient"
                calibration = {"status": "insufficient", "reason": str(exc), "event_count": len({r.get("event_id") for r in calibration_records})}
        else:
            calibration = {"status": "insufficient", "reason": "fewer_than_two_events", "event_count": len({r.get("event_id") for r in calibration_records})}

        outputs.append({
            "family": family,
            "cohort_id": cohort_id,
            "status": "ready_for_review" if comparisons and calibration_status == "scored" else "insufficient",
            "reasons": [] if comparisons and calibration_status == "scored" else ["comparisons_or_calibration_insufficient"],
            "comparisons": comparisons,
            "comparison_count": len(comparisons),
            "calibration": calibration,
            "calibration_status": calibration_status,
            "market_pair_count": len(pairs),
            "coverage_summary": package.get("coverage_summary"),
            "limitations": package.get("limitations", []),
            "source_use_evidence_ref": package["source_use_evidence_ref"],
            "selection_evidence_ref": package["selection_evidence_ref"],
            "settlement_evidence_ref": package["settlement_evidence_ref"],
            "coverage_evidence_ref": package["coverage_evidence_ref"],
            "second_reviewer_ref": package["second_reviewer_ref"],
            "evidence_class": "held_out_result" if calibration_status in {"scored", "sparse"} else "pending",
            "claim_status": "synthetic" if package.get("fixture_status") == "synthetic" else "observed",
            "live_execution": False,
        })

    if not outputs or any(row["status"] == "blocked" for row in outputs):
        claim_status = "pending"
    elif all(row.get("claim_status") == "synthetic" for row in outputs):
        claim_status = "synthetic"
    else:
        claim_status = "observed"
    return {
        "schema_version": "weather-study-v1",
        "family_count": len(outputs),
        "families": outputs,
        "claim_status": claim_status,
        "pooling": "none_family_stratified",
        "interpretation": "research_comparison_and_calibration_not_profitability",
        "live_execution": False,
    }


def _gate_reasons(package: Mapping[str, Any]) -> list[str]:
    reasons = []
    for field, expected, reason in _GATES:
        if package.get(field) != expected:
            reasons.append(reason)
    for field, reason in (
        ("source_use_evidence_ref", "source_use_evidence_missing"),
        ("selection_evidence_ref", "selection_evidence_missing"),
        ("settlement_evidence_ref", "settlement_evidence_missing"),
        ("coverage_evidence_ref", "coverage_evidence_missing"),
        ("second_reviewer_ref", "second_reviewer_missing"),
    ):
        if not isinstance(package.get(field), str) or not package[field].strip():
            reasons.append(reason)
    if package.get("second_reviewer_qualified") is not True:
        reasons.append("second_reviewer_unqualified")
    return reasons
