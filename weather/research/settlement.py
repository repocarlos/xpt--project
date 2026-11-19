"""Validation for family-aware weather settlement mappings.

This module validates mapping metadata only. It does not fetch contracts or
resolve outcomes; real records require source-specific usage approval.
"""

from __future__ import annotations

from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError
from typing import Any, Mapping


SPATIAL_SUPPORT_TYPES = {"station", "grid", "polygon", "basin", "location_set"}
MAPPING_STATUSES = {"verified", "provisional", "ambiguous"}

_REQUIRED = (
    "event_key",
    "family",
    "variable",
    "unit",
    "spatial_support_type",
    "spatial_support_ref",
    "timezone",
    "valid_start",
    "valid_end",
    "resolution_authority",
    "resolution_source",
    "settlement_rule",
    "rule_version",
    "mapping_status",
    "source_use_status",
)


def validate_mapping(mapping: Mapping[str, Any]) -> list[str]:
    """Return validation errors; an empty list means metadata is well formed."""
    errors: list[str] = []
    for field in _REQUIRED:
        value = mapping.get(field)
        if value is None or (isinstance(value, str) and not value.strip()):
            errors.append(f"missing required field: {field}")

    status = mapping.get("mapping_status")
    if status is not None and status not in MAPPING_STATUSES:
        errors.append("mapping_status must be verified, provisional, or ambiguous")

    spatial_type = mapping.get("spatial_support_type")
    if spatial_type is not None and spatial_type not in SPATIAL_SUPPORT_TYPES:
        errors.append("unsupported spatial_support_type")

    timezone = mapping.get("timezone")
    if isinstance(timezone, str) and timezone.strip():
        try:
            ZoneInfo(timezone)
        except ZoneInfoNotFoundError:
            errors.append("timezone must be a valid IANA timezone")

    start = _parse_datetime(mapping.get("valid_start"), "valid_start", errors)
    end = _parse_datetime(mapping.get("valid_end"), "valid_end", errors)
    if start and end:
        if start.tzinfo is None or end.tzinfo is None:
            errors.append("valid_start and valid_end must include a timezone offset")
        elif end <= start:
            errors.append("valid_end must be later than valid_start")

    if status == "ambiguous" and not _nonempty(mapping.get("ambiguity_reason")):
        errors.append("ambiguous mappings require ambiguity_reason")
    if status == "verified":
        if not _nonempty(mapping.get("reviewer_ref")):
            errors.append("verified mappings require reviewer_ref")
        if not _nonempty(mapping.get("evidence_ref")):
            errors.append("verified mappings require evidence_ref")

    return errors


def outcome_join_eligible(mapping: Mapping[str, Any]) -> bool:
    """Whether a mapping can be used to join an outcome for analysis."""
    return (
        not validate_mapping(mapping)
        and mapping.get("mapping_status") == "verified"
        and mapping.get("source_use_status") == "approved"
        and _nonempty(mapping.get("source_use_evidence_ref"))
    )


def _parse_datetime(value: Any, field: str, errors: list[str]) -> datetime | None:
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        errors.append(f"{field} must be ISO-8601")
        return None


def _nonempty(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())

