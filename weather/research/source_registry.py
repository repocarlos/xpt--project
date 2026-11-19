"""Weather source inventory validation; it does not authorize any source."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Mapping


USES = {"access", "internal_analysis", "raw_retention", "normalized_retention", "derivation", "sharing", "retail_display"}
USE_STATUSES = {"approved", "limited", "blocked", "no_go"}
COVERAGE_STATUSES = {"verified", "claimed", "unknown"}


def validate_source_register(register: Mapping[str, Any]) -> list[str]:
    errors: list[str] = []
    records = register.get("source_uses")
    if not isinstance(records, list) or not records:
        return ["source_uses must contain one row per source and intended use"]
    seen: set[tuple[str, str, str]] = set()
    for index, row in enumerate(records):
        if not isinstance(row, Mapping):
            errors.append(f"row {index} must be an object")
            continue
        prefix = f"row {index}"
        for field in ("candidate_ref", "family", "venue_or_source_type", "geography", "data_tier"):
            if not _text(row.get(field)):
                errors.append(f"{prefix} missing {field}")
        use = row.get("intended_use")
        if use not in USES:
            errors.append(f"{prefix} has invalid intended_use")
        status = row.get("use_status")
        if status not in USE_STATUSES:
            errors.append(f"{prefix} has invalid use_status")
        key = (str(row.get("candidate_ref")), str(row.get("family")), str(use))
        if key in seen:
            errors.append(f"{prefix} duplicates a source/family/use row")
        seen.add(key)
        if status == "approved" and not _text(row.get("approval_evidence_ref")):
            errors.append(f"{prefix} approved use requires approval_evidence_ref")
        if use in {"raw_retention", "normalized_retention"} and status == "approved" and not _text(row.get("retention_until")):
            errors.append(f"{prefix} approved retention requires retention_until")
        if use in {"raw_retention", "normalized_retention"} and status == "approved" and not _future_timestamp(row.get("retention_until")):
            errors.append(f"{prefix} approved retention requires a non-expired timezone-aware retention_until")
        if row.get("coverage_status") not in COVERAGE_STATUSES:
            errors.append(f"{prefix} has invalid coverage_status")
        if row.get("coverage_status") in {"verified", "claimed"}:
            if not _text(row.get("coverage_evidence_ref")) or not _text(row.get("coverage_as_of")):
                errors.append(f"{prefix} measured or claimed coverage requires evidence and as-of date")
        if row.get("estimated_bytes") is not None:
            value = row.get("estimated_bytes")
            if isinstance(value, bool) or not isinstance(value, int) or value < 0:
                errors.append(f"{prefix} estimated_bytes must be a non-negative integer")
            if not _text(row.get("estimate_assumptions")) or not _text(row.get("estimate_evidence_ref")):
                errors.append(f"{prefix} volume estimate requires assumptions and evidence")

    reviewer = register.get("second_reviewer", {})
    reviewer_ready = isinstance(reviewer, Mapping) and reviewer.get("weather_qualified") is True and _text(reviewer.get("reviewer_ref")) and _text(reviewer.get("qualification_evidence_ref"))
    if register.get("raw_inspection_allowed") is True:
        if not reviewer_ready:
            errors.append("raw inspection requires a qualified second reviewer and evidence")
        required = {"access", "internal_analysis", "raw_retention"}
        for candidate_ref, family in {(str(row.get("candidate_ref")), str(row.get("family"))) for row in records if isinstance(row, Mapping)}:
            approved = {row.get("intended_use") for row in records if isinstance(row, Mapping) and str(row.get("candidate_ref")) == candidate_ref and str(row.get("family")) == family and row.get("use_status") == "approved"}
            if not required.issubset(approved):
                errors.append(f"raw inspection blocked for {candidate_ref}/{family}: required uses are not all approved")
    return errors


def can_inspect_raw_rows(register: Mapping[str, Any]) -> bool:
    """Return true only if the register is valid and every raw-inspection gate passes."""
    if validate_source_register(register):
        return False
    if register.get("raw_inspection_allowed") is not True:
        return False
    reviewer = register.get("second_reviewer", {})
    if not isinstance(reviewer, Mapping) or reviewer.get("weather_qualified") is not True:
        return False
    required = {"access", "internal_analysis", "raw_retention"}
    records = register["source_uses"]
    for candidate_ref, family in {(str(row["candidate_ref"]), str(row["family"])) for row in records}:
        approved = {row["intended_use"] for row in records if str(row["candidate_ref"]) == candidate_ref and str(row["family"]) == family and row["use_status"] == "approved"}
        if not required.issubset(approved):
            return False
    return True


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())


def _future_timestamp(value: Any) -> bool:
    if not isinstance(value, str):
        return False
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return False
    return parsed.tzinfo is not None and parsed.astimezone(timezone.utc) > datetime.now(timezone.utc)
