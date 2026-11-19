"""Evidence-gated selection of weather cohorts from the broader candidate universe."""

from __future__ import annotations

from typing import Any, Mapping


COHORT_STATUSES = {"candidate", "selected", "excluded", "deferred", "blocked"}


def validate_selection(register: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    candidates = register.get("cohorts")
    if not isinstance(candidates, list) or not candidates:
        return ["cohorts must include the multi-family candidate universe"]
    seen: set[str] = set()
    selected = 0
    for index, row in enumerate(candidates):
        if not isinstance(row, Mapping):
            errors.append(f"cohort {index} must be an object")
            continue
        prefix = f"cohort {index}"
        cohort_id = row.get("cohort_id")
        if not _text(cohort_id):
            errors.append(f"{prefix} missing cohort_id")
        elif cohort_id in seen:
            errors.append(f"duplicate cohort_id: {cohort_id}")
        seen.add(str(cohort_id))
        family = row.get("family")
        if not _text(family):
            errors.append(f"{prefix} missing family")
        status = row.get("status")
        if status not in COHORT_STATUSES:
            errors.append(f"{prefix} has invalid status")
        if status in {"excluded", "deferred", "blocked"} and not _text(row.get("decision_reason")):
            errors.append(f"{prefix} requires decision_reason")
        if status != "selected":
            continue
        selected += 1
        for field in ("venue", "geography", "event_horizon", "settlement_observable"):
            if not _text(row.get(field)):
                errors.append(f"{prefix} selected cohort requires {field}")
        if row.get("source_use_status") != "approved" or not _text(row.get("source_use_evidence_ref")):
            errors.append(f"{prefix} selected cohort requires approved source use and evidence")
        if row.get("settlement_status") != "verified" or not _text(row.get("settlement_evidence_ref")):
            errors.append(f"{prefix} selected cohort requires verified settlement evidence")
        if row.get("coverage_status") != "verified" or not _text(row.get("coverage_evidence_ref")):
            errors.append(f"{prefix} selected cohort requires verified coverage evidence")
        if row.get("forecast_match_status") != "verified" or not _text(row.get("forecast_evidence_ref")):
            errors.append(f"{prefix} selected cohort requires verified forecast match evidence")
        if row.get("volume_status") != "verified" or not _text(row.get("volume_evidence_ref")) or not _text(row.get("volume_assumptions")):
            errors.append(f"{prefix} selected cohort requires evidenced volume estimate and assumptions")
        if row.get("second_reviewer_qualified") is not True or not _text(row.get("second_reviewer_ref")):
            errors.append(f"{prefix} selected cohort requires a qualified second reviewer")
    decision = register.get("selection_decision")
    if decision not in {"pending", "select", "revise", "no_go"}:
        errors.append("selection_decision must be pending, select, revise, or no_go")
    if decision == "select" and not selected:
        errors.append("select decision requires at least one selected cohort")
    if decision in {"revise", "no_go"} and not _text(register.get("decision_evidence_ref")):
        errors.append("revise/no_go decision requires decision_evidence_ref")
    if register.get("selection_decision") != "select" and selected:
        errors.append("selected cohort rows require selection_decision=select")
    return errors


def ready_to_select(register: Mapping[str, Any]) -> bool:
    return register.get("selection_decision") == "select" and not validate_selection(register)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
