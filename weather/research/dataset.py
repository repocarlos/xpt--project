"""Permission-gated normalization and manifest utilities for weather batches."""

from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
from typing import Any, Iterable, Mapping


REQUIRED_USES = {"internal_analysis", "retain_normalized"}
ALLOWED_RECORD_TYPES = {"event", "contract", "quote", "forecast", "outcome"}


def require_source_permissions(approval: Mapping[str, Any], required_uses: Iterable[str] = REQUIRED_USES) -> None:
    """Fail closed unless an evidence-backed approval covers every intended use."""
    if approval.get("status") != "approved":
        raise PermissionError("source use is not approved")
    if not _text(approval.get("approval_ref")):
        raise PermissionError("approval evidence reference is required")
    permitted = approval.get("permitted_uses")
    if not isinstance(permitted, (list, tuple, set)):
        raise PermissionError("permitted_uses must be an explicit collection")
    missing = set(required_uses) - set(permitted)
    if missing:
        raise PermissionError("approval does not cover: " + ", ".join(sorted(missing)))


def normalize_batch(
    records: Iterable[Mapping[str, Any]],
    *,
    approval: Mapping[str, Any],
    manifest_id: str,
    schema_version: str = "weather-v1",
) -> list[dict[str, Any]]:
    """Normalize a caller-supplied batch after checking rights, deduplicating by key."""
    # Keep this before touching the iterable so lazy adapters can invoke the guard first.
    require_source_permissions(approval)
    if not _text(manifest_id) or not _text(schema_version):
        raise ValueError("manifest_id and schema_version are required")

    normalized: dict[tuple[str, str], dict[str, Any]] = {}
    for source_row in records:
        row = dict(source_row)
        record_type = row.get("record_type")
        if record_type not in ALLOWED_RECORD_TYPES:
            raise ValueError("record_type must be event, contract, quote, forecast, or outcome")
        record_key = row.get("record_key")
        family = row.get("family")
        if not _text(record_key) or not _text(family):
            raise ValueError("record_key and family are required")
        if row.get("source_use_status") != "approved":
            raise PermissionError("record source_use_status must be approved")

        item = {
            **row,
            "record_key": str(record_key),
            "record_type": record_type,
            "family": str(family),
            "schema_version": schema_version,
            "manifest_id": manifest_id,
            "source_approval_ref": approval["approval_ref"],
        }
        for field in ("observed_at_utc", "issued_at_utc", "valid_start_utc", "valid_end_utc"):
            if item.get(field) is not None:
                item[field] = _utc_iso(item[field], field)
        if "source_record_id" in item and "retain_source_ids" not in set(approval.get("permitted_uses", [])):
            item.pop("source_record_id")

        key = (str(record_type), str(record_key))
        previous = normalized.get(key)
        if previous is not None and previous != item:
            raise ValueError(f"conflicting duplicate record: {record_type}/{record_key}")
        normalized[key] = item
    return [normalized[key] for key in sorted(normalized)]


def build_manifest(
    records: list[Mapping[str, Any]],
    *,
    approval: Mapping[str, Any],
    manifest_id: str,
    retrieved_at_utc: str,
    retention_until: str,
) -> dict[str, Any]:
    """Build an immutable batch manifest; payload content is not included."""
    require_source_permissions(approval)
    retrieved = _utc_iso(retrieved_at_utc, "retrieved_at_utc")
    retained_until = _utc_iso(retention_until, "retention_until")
    if datetime.fromisoformat(retained_until) < datetime.fromisoformat(retrieved):
        raise ValueError("retention_until cannot precede retrieval")
    canonical = json.dumps(records, sort_keys=True, separators=(",", ":"), default=str).encode("utf-8")
    return {
        "manifest_id": manifest_id,
        "schema_version": records[0].get("schema_version") if records else "weather-v1",
        "approval_ref": approval["approval_ref"],
        "permitted_uses": sorted(set(approval["permitted_uses"])),
        "retrieved_at_utc": retrieved,
        "retention_until": retained_until,
        "row_count": len(records),
        "families": sorted({str(row["family"]) for row in records}),
        "record_types": sorted({str(row["record_type"]) for row in records}),
        "sha256": hashlib.sha256(canonical).hexdigest(),
        "payload_included": False,
    }


def write_parquet_partition(records: list[Mapping[str, Any]], path: str | Path, approval: Mapping[str, Any]) -> dict[str, Any]:
    """Write normalized records to Parquet only when normalized retention is approved."""
    require_source_permissions(approval)
    if not records:
        raise ValueError("cannot write an empty partition")
    import pyarrow as pa
    import pyarrow.parquet as pq

    destination = Path(path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    table = pa.Table.from_pylist([dict(record) for record in records])
    pq.write_table(table, destination)
    digest = hashlib.sha256()
    with destination.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return {"path": str(destination), "row_count": table.num_rows, "byte_count": destination.stat().st_size, "sha256": digest.hexdigest()}


def _utc_iso(value: Any, field: str) -> str:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{field} must include a timezone")
    return parsed.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
