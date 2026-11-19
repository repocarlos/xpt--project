"""Validation for a Weather-sector study handoff; no empirical claims are added."""

from __future__ import annotations

from typing import Any, Mapping


EVIDENCE_CLASSES = {"observed_price", "model_estimate", "held_out_result", "candidate_gap"}
CLAIM_STATUSES = {"pending", "synthetic", "observed", "validated", "insufficient"}
RECOMMENDATIONS = {"proceed", "revise", "stop"}


def validate_handoff(document: Mapping[str, Any]) -> list[str]:
    """Return completeness/label errors for a source-neutral dashboard handoff."""
    errors: list[str] = []
    for field in ("question", "period", "family_scopes", "settlement", "coverage", "comparisons",
                  "uncertainty", "costs", "storage", "limitations", "deferred_families",
                  "reproducibility_refs", "recommendation"):
        if field not in document or document[field] in (None, "", [], {}):
            errors.append(f"missing required section: {field}")
    if "cross_sector_score" in document:
        errors.append("Weather handoff must not force metrics into a cross-sector score")
    recommendation = document.get("recommendation")
    if recommendation is not None and recommendation not in RECOMMENDATIONS:
        errors.append("recommendation must be proceed, revise, or stop")
    comparisons = document.get("comparisons", [])
    if not isinstance(comparisons, list):
        errors.append("comparisons must be a list")
    else:
        for index, row in enumerate(comparisons):
            if not isinstance(row, Mapping):
                errors.append(f"comparison {index} must be an object")
                continue
            prefix = f"comparison {index}"
            if row.get("evidence_class") not in EVIDENCE_CLASSES:
                errors.append(f"{prefix} has invalid evidence_class")
            if row.get("claim_status") not in CLAIM_STATUSES:
                errors.append(f"{prefix} has invalid claim_status")
            if row.get("claim_status") == "validated" and not _text(row.get("validation_evidence_ref")):
                errors.append(f"{prefix} validated claim requires validation_evidence_ref")
            if row.get("source_use_status") != "approved" and row.get("claim_status") in {"observed", "validated"}:
                errors.append(f"{prefix} cannot report observed or validated claim without source approval")
    scopes = document.get("family_scopes", [])
    if not isinstance(scopes, list):
        errors.append("family_scopes must be a list")
    else:
        for index, scope in enumerate(scopes):
            if not isinstance(scope, Mapping) or not _text(scope.get("family")) or scope.get("status") not in {"selected", "deferred", "blocked"}:
                errors.append(f"family scope {index} needs family and selected/deferred/blocked status")
    deferred = document.get("deferred_families", [])
    if isinstance(deferred, list):
        for index, family in enumerate(deferred):
            if not isinstance(family, Mapping) or not _text(family.get("family")) or not _text(family.get("evidence_needed")):
                errors.append(f"deferred family {index} needs family and evidence_needed")
    if document.get("source_use_status") != "approved":
        if any(isinstance(row, Mapping) and row.get("claim_status") in {"observed", "validated"} for row in comparisons if isinstance(comparisons, list)):
            errors.append("unapproved handoff cannot contain observed or validated comparison claims")
    return errors


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
