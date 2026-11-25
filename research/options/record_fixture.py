"""Write explicitly synthetic options-study fixtures to local Parquet.

There is intentionally no live source adapter in this module. A fixture run is
useful for validating schemas and downstream code, but is not permission to
collect, retain, derive, share, or display source data.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import re
import shutil
import subprocess
import sys
import tempfile
import uuid
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import pyarrow as pa
import pyarrow.parquet as pq


SCHEMA_VERSION = "options.recorder.v1"
MANIFEST_VERSION = "options.recorder_manifest.v1"
PRODUCER = "xpt-options-fixture-recorder"
SYNTHETIC_RIGHTS = "not_applicable_synthetic_fixture"
PATH_TOKEN = re.compile(r"^[A-Za-z0-9._-]+$")

STRING_COLUMNS = (
    "record_id", "venue", "event_date", "record_type", "market_id",
    "source_id", "underlying", "expiry", "observed_at_utc", "timezone",
    "settlement_rule_version", "settlement_reference", "currency",
    "fixture_status", "collection_rights_status", "raw_storage_rights_status",
    "derivation_rights_status", "team_sharing_rights_status",
    "display_rights_status", "transformations_json",
)
SCHEMA = pa.schema([
    *[pa.field(name, pa.string(), nullable=False) for name in STRING_COLUMNS],
    pa.field("strike", pa.float64()),
    pa.field("bid", pa.float64()),
    pa.field("ask", pa.float64()),
    pa.field("bid_size", pa.int64()),
    pa.field("ask_size", pa.int64()),
])
REQUIRED = {
    "record_id", "venue", "record_type", "market_id", "source_id",
    "underlying", "expiry", "observed_at_utc", "timezone",
    "settlement_rule_version", "settlement_reference", "currency",
    "bid", "ask", "transformations", "source_rights",
}
RIGHTS_FIELDS = (
    "collection", "raw_storage", "derivation", "team_sharing", "display",
)


def _canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _utc_timestamp(value: Any, field: str) -> tuple[str, str]:
    if not isinstance(value, str):
        raise ValueError(f"{field} must be an ISO-8601 string with a UTC offset")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError(f"{field} must be an ISO-8601 string with a UTC offset") from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f"{field} must include a UTC offset")
    normalized = parsed.astimezone(timezone.utc)
    return normalized.isoformat().replace("+00:00", "Z"), normalized.date().isoformat()


def _path_token(value: str, field: str) -> str:
    if not isinstance(value, str) or not PATH_TOKEN.fullmatch(value) or value in {".", ".."}:
        raise ValueError(f"{field} must contain only letters, digits, dot, underscore or hyphen")
    return value


def validate_fixture(document: dict[str, Any]) -> tuple[list[dict[str, Any]], int]:
    """Validate and normalize fixture rows; reject any observed-source input."""
    if document.get("schema_version") != "options.recorder_fixture.v1":
        raise ValueError("schema_version must be 'options.recorder_fixture.v1'")
    if document.get("fixture_status") != "synthetic":
        raise ValueError("only fixture_status='synthetic' is accepted; observed data is blocked")
    if not isinstance(document.get("rights_blocker"), str) or not document["rights_blocker"].strip():
        raise ValueError("rights_blocker must explain why live collection remains disabled")
    records = document.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty array")

    normalized: list[tuple[str, dict[str, Any]]] = []
    id_content: dict[str, str] = {}
    for index, source in enumerate(records):
        if not isinstance(source, dict):
            raise ValueError(f"records[{index}] must be an object")
        missing = sorted(REQUIRED - source.keys())
        if missing:
            raise ValueError(f"records[{index}] is missing required fields: {', '.join(missing)}")
        rights = source["source_rights"]
        if not isinstance(rights, dict) or any(rights.get(name) != SYNTHETIC_RIGHTS for name in RIGHTS_FIELDS):
            raise ValueError(
                f"records[{index}] source_rights must mark each intended use as {SYNTHETIC_RIGHTS}"
            )
        observed_at, event_date = _utc_timestamp(source["observed_at_utc"], f"records[{index}].observed_at_utc")
        try:
            ZoneInfo(source["timezone"])
        except (ZoneInfoNotFoundError, TypeError) as exc:
            raise ValueError(f"records[{index}].timezone must be a valid IANA time zone") from exc
        for name in ("venue", "market_id"):
            _path_token(source[name], f"records[{index}].{name}")
        if not isinstance(source["transformations"], list) or not all(
            isinstance(item, str) and item for item in source["transformations"]
        ):
            raise ValueError(f"records[{index}].transformations must be a list of non-empty strings")
        bid, ask = source["bid"], source["ask"]
        if not isinstance(bid, (int, float)) or not isinstance(ask, (int, float)):
            raise ValueError(f"records[{index}] bid and ask must be numeric")
        if bid < 0 or ask < bid:
            raise ValueError(f"records[{index}] requires 0 <= bid <= ask")
        row: dict[str, Any] = {
            "record_id": str(source["record_id"]),
            "venue": source["venue"],
            "event_date": event_date,
            "record_type": str(source["record_type"]),
            "market_id": source["market_id"],
            "source_id": str(source["source_id"]),
            "underlying": str(source["underlying"]),
            "expiry": str(source["expiry"]),
            "observed_at_utc": observed_at,
            "timezone": source["timezone"],
            "settlement_rule_version": str(source["settlement_rule_version"]),
            "settlement_reference": str(source["settlement_reference"]),
            "currency": str(source["currency"]),
            "fixture_status": "synthetic",
            **{f"{name}_rights_status": SYNTHETIC_RIGHTS for name in RIGHTS_FIELDS},
            "transformations_json": _canonical_json(source["transformations"]),
            "strike": source.get("strike"),
            "bid": float(bid),
            "ask": float(ask),
            "bid_size": source.get("bid_size"),
            "ask_size": source.get("ask_size"),
        }
        for name in ("strike",):
            value = row[name]
            if value is not None and (not isinstance(value, (int, float)) or value < 0):
                raise ValueError(f"records[{index}].{name} must be non-negative numeric or null")
            if value is not None:
                row[name] = float(value)
        for name in ("bid_size", "ask_size"):
            value = row[name]
            if value is not None and (not isinstance(value, int) or value < 0):
                raise ValueError(f"records[{index}].{name} must be a non-negative integer or null")

        fingerprint = _sha256_bytes(_canonical_json(row).encode("utf-8"))
        prior_fingerprint = id_content.get(row["record_id"])
        if prior_fingerprint is not None and prior_fingerprint != fingerprint:
            raise ValueError(f"record_id {row['record_id']!r} is reused for conflicting records")
        id_content[row["record_id"]] = fingerprint
        normalized.append((fingerprint, row))

    unique = {fingerprint: row for fingerprint, row in normalized}
    ordered = [unique[key] for key in sorted(unique)]
    duplicates_removed = len(records) - len(ordered)
    return ordered, duplicates_removed


def _git_revision() -> str | None:
    try:
        result = subprocess.run(
            ["git", "rev-parse", "HEAD"], capture_output=True, text=True, check=True,
        )
        return result.stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        return None


def _file_entries(root: Path) -> list[dict[str, Any]]:
    entries = []
    for path in sorted(root.rglob("*.parquet")):
        entries.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": _sha256_file(path),
        })
    return entries


def verify_manifest(dataset_dir: Path) -> bool:
    """Verify every Parquet file against the sidecar manifest."""
    manifest = json.loads((dataset_dir / "manifest.json").read_text(encoding="utf-8"))
    if manifest.get("manifest_version") != MANIFEST_VERSION:
        raise ValueError("unsupported manifest version")
    if manifest.get("producer") != PRODUCER or manifest.get("fixture_status") != "synthetic":
        raise ValueError("manifest is not owned by the synthetic fixture recorder")
    for entry in manifest.get("files", []):
        path = (dataset_dir / entry["path"]).resolve()
        if dataset_dir.resolve() not in path.parents or not path.is_file():
            raise ValueError(f"manifest path is missing or escapes dataset directory: {entry['path']}")
        if path.stat().st_size != entry["size_bytes"] or _sha256_file(path) != entry["sha256"]:
            raise ValueError(f"manifest checksum mismatch for {entry['path']}")
    return True


def write_fixture(document: dict[str, Any], output_root: Path) -> tuple[Path, dict[str, Any]]:
    rows, duplicates_removed = validate_fixture(document)
    canonical_records = _canonical_json(rows).encode("utf-8")
    logical_hash = _sha256_bytes(canonical_records)
    dataset_id = f"fixture-{logical_hash[:16]}"
    fixture_hash = _sha256_bytes(_canonical_json(document).encode("utf-8"))
    output_root = Path(output_root)
    dataset_dir = output_root / dataset_id
    output_root.mkdir(parents=True, exist_ok=True)

    if dataset_dir.exists():
        manifest_path = dataset_dir / "manifest.json"
        if not manifest_path.is_file():
            raise ValueError(f"refusing to replace unrecognized output directory: {dataset_dir}")
        previous = json.loads(manifest_path.read_text(encoding="utf-8"))
        if (previous.get("producer") != PRODUCER or previous.get("fixture_status") != "synthetic"
                or previous.get("dataset_id") != dataset_id):
            raise ValueError(f"refusing to replace unrecognized output directory: {dataset_dir}")

    stage = Path(tempfile.mkdtemp(prefix=f".{dataset_id}.tmp-", dir=output_root))
    backup = output_root / f".{dataset_id}.backup-{uuid.uuid4().hex}"
    try:
        groups: dict[tuple[str, str, str], list[dict[str, Any]]] = defaultdict(list)
        for row in rows:
            groups[(row["venue"], row["event_date"], row["market_id"])].append(row)
        for (venue, event_date, market_id), group in sorted(groups.items()):
            partition_dir = stage / f"venue={venue}" / f"date={event_date}" / f"market={market_id}"
            partition_dir.mkdir(parents=True, exist_ok=True)
            table = pa.Table.from_pylist(group, schema=SCHEMA)
            pq.write_table(table, partition_dir / "part-000.parquet", compression="zstd")

        source_ids = sorted({row["source_id"] for row in rows})
        settlement_versions = sorted({row["settlement_rule_version"] for row in rows})
        manifest = {
            "manifest_version": MANIFEST_VERSION,
            "producer": PRODUCER,
            "dataset_id": dataset_id,
            "dataset_kind": "local_synthetic_fixture",
            "fixture_status": "synthetic",
            "schema_version": SCHEMA_VERSION,
            "fixture_sha256": fixture_hash,
            "logical_records_sha256": logical_hash,
            "record_count": len(rows),
            "duplicates_removed": duplicates_removed,
            "source_ids": source_ids,
            "settlement_rule_versions": settlement_versions,
            "timezone_convention": "observed_at_utc normalized to UTC; source timezone retained per record",
            "partitioning": ["venue", "date (UTC observation date)", "market"],
            "transformations": ["fixture validation", "UTC timestamp normalization", "exact duplicate removal"],
            "source_rights": {
                "access": SYNTHETIC_RIGHTS,
                "collection": SYNTHETIC_RIGHTS,
                "raw_storage": SYNTHETIC_RIGHTS,
                "derivation": SYNTHETIC_RIGHTS,
                "team_sharing": SYNTHETIC_RIGHTS,
                "display": SYNTHETIC_RIGHTS,
                "live_collection": "blocked_unresolved_source_approval",
                "blocker": document["rights_blocker"],
            },
            "cadence": "not_selected_live_capture_disabled",
            "retention": "not_selected_live_capture_disabled",
            "storage_target": "caller_selected_local_fixture_path_not_durable_team_storage",
            "code_revision": _git_revision(),
            "created_at_utc": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
            "files": [],
        }
        manifest["files"] = _file_entries(stage)
        (stage / "manifest.json").write_text(
            json.dumps(manifest, indent=2, sort_keys=True, allow_nan=False) + "\n",
            encoding="utf-8",
        )
        verify_manifest(stage)

        if dataset_dir.exists():
            dataset_dir.rename(backup)
        try:
            stage.rename(dataset_dir)
        except Exception:
            if backup.exists():
                backup.rename(dataset_dir)
            raise
        if backup.exists():
            shutil.rmtree(backup)
    except Exception:
        if stage.exists():
            shutil.rmtree(stage)
        if backup.exists() and not dataset_dir.exists():
            backup.rename(dataset_dir)
        raise
    return dataset_dir, manifest


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fixture", type=Path, help="JSON fixture explicitly labeled synthetic")
    parser.add_argument("--output-root", type=Path, help="local output directory for synthetic fixtures")
    parser.add_argument("--live", action="store_true", help="live collection is deliberately disabled")
    args = parser.parse_args(argv)
    if args.live:
        print("LIVE COLLECTION BLOCKED: source approvals and durable storage are unresolved; no output written.", file=sys.stderr)
        return 2
    if args.fixture is None or args.output_root is None:
        parser.error("--fixture and --output-root are required; live collection is not implemented")
    try:
        document = json.loads(args.fixture.read_text(encoding="utf-8"))
        if not isinstance(document, dict):
            raise ValueError("fixture root must be a JSON object")
        dataset_dir, manifest = write_fixture(document, args.output_root)
    except (OSError, json.JSONDecodeError, ValueError) as exc:
        print(f"FIXTURE RECORDING FAILED: {exc}", file=sys.stderr)
        return 1
    print(json.dumps({
        "status": "synthetic_fixture_written",
        "dataset_dir": str(dataset_dir),
        "record_count": manifest["record_count"],
        "duplicates_removed": manifest["duplicates_removed"],
        "manifest": str(dataset_dir / "manifest.json"),
    }, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
