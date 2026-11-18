"""Validate dataset manifest structure and block unapproved real-source records."""

from __future__ import annotations

import json
import re
from datetime import date, datetime, timezone
from pathlib import Path
from typing import Any


ALLOWED_RIGHTS = {"approved", "blocked", "not_applicable"}
REQUIRED_RIGHTS = {
    "access", "internal_research", "raw_storage", "derived_data",
    "team_sharing", "dashboard_display", "commercial_use",
}
SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
COMMIT_RE = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
REQUIRED = {
    "manifest_version", "dataset_id", "dataset_version", "synthetic_fixture",
    "schema_version", "source", "collected_at_utc", "event_time_start_utc",
    "event_time_end_utc", "settlement_timezone", "identifiers", "transformations",
    "rights", "artifact", "code_commit", "parent_manifests",
}


class ManifestError(ValueError):
    pass


def _utc_timestamp(value: Any, field: str) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ManifestError(f"{field} must be an ISO 8601 UTC timestamp ending in Z")
    try:
        parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    except ValueError as exc:
        raise ManifestError(f"{field} is not a valid ISO 8601 timestamp") from exc
    if parsed.utcoffset() != timezone.utc.utcoffset(parsed):
        raise ManifestError(f"{field} must be UTC")
    return parsed


def validate(manifest: dict[str, Any]) -> None:
    missing = REQUIRED - set(manifest)
    if missing:
        raise ManifestError(f"missing required fields: {sorted(missing)}")
    if not isinstance(manifest["synthetic_fixture"], bool):
        raise ManifestError("synthetic_fixture must be boolean")

    source = manifest["source"]
    if not isinstance(source, dict) or not all(source.get(k) for k in ("provider", "source_id", "access_method")):
        raise ManifestError("source must include provider, source_id, and access_method")
    if not isinstance(source.get("terms_reviewed_at"), str):
        raise ManifestError("source.terms_reviewed_at is required")
    try:
        date.fromisoformat(source["terms_reviewed_at"])
    except ValueError as exc:
        raise ManifestError("source.terms_reviewed_at must be YYYY-MM-DD") from exc

    collected = _utc_timestamp(manifest["collected_at_utc"], "collected_at_utc")
    event_start = _utc_timestamp(manifest["event_time_start_utc"], "event_time_start_utc")
    event_end = _utc_timestamp(manifest["event_time_end_utc"], "event_time_end_utc")
    if event_end < event_start:
        raise ManifestError("event time coverage ends before it starts")
    if collected.tzinfo is None:
        raise ManifestError("collected_at_utc must be timezone-aware")

    if not isinstance(manifest["identifiers"], list) or not manifest["identifiers"]:
        raise ManifestError("identifiers must be a non-empty list")
    for item in manifest["identifiers"]:
        if not isinstance(item, dict) or not all(item.get(k) for k in ("venue", "event_id", "market_id", "settlement_rule_version")):
            raise ManifestError("each identifier needs venue, event_id, market_id, and settlement_rule_version")
    if not isinstance(manifest["transformations"], list) or not manifest["transformations"]:
        raise ManifestError("transformations must be a non-empty list")

    rights = manifest["rights"]
    if not isinstance(rights, dict) or REQUIRED_RIGHTS - set(rights):
        raise ManifestError("rights must contain a status for each required use")
    if any(rights[key] not in ALLOWED_RIGHTS for key in REQUIRED_RIGHTS):
        raise ManifestError("rights statuses must be approved, blocked, or not_applicable")
    if not rights.get("basis") or not rights.get("reviewed_at"):
        raise ManifestError("rights basis and reviewed_at are required")
    try:
        date.fromisoformat(rights["reviewed_at"])
    except ValueError as exc:
        raise ManifestError("rights.reviewed_at must be YYYY-MM-DD") from exc

    if not manifest["synthetic_fixture"]:
        if source["provider"] == "synthetic_fixture":
            raise ManifestError("real-source record cannot claim the synthetic provider")
        if any(rights[key] != "approved" for key in REQUIRED_RIGHTS):
            raise ManifestError("real-source manifest blocked: all required rights must be approved")

    artifact = manifest["artifact"]
    if not isinstance(artifact, dict) or not all(artifact.get(k) is not None for k in ("storage_uri", "format", "row_count", "byte_count", "sha256")):
        raise ManifestError("artifact must include URI, format, row_count, byte_count, and sha256")
    if not SHA256_RE.fullmatch(str(artifact["sha256"])):
        raise ManifestError("artifact.sha256 must be 64 lowercase hexadecimal characters")
    if not isinstance(artifact["row_count"], int) or artifact["row_count"] < 0:
        raise ManifestError("artifact.row_count must be a non-negative integer")
    if not isinstance(artifact["byte_count"], int) or artifact["byte_count"] < 0:
        raise ManifestError("artifact.byte_count must be a non-negative integer")
    if not COMMIT_RE.fullmatch(str(manifest["code_commit"])):
        raise ManifestError("code_commit must be a 40- or 64-character hexadecimal commit")


def main() -> None:
    path = Path(__file__).with_name("manifest.example.json")
    manifest = json.loads(path.read_text(encoding="utf-8"))
    validate(manifest)
    print("PASS synthetic manifest fields, timestamps, rights statuses, and checksum shape")


if __name__ == "__main__":
    main()
