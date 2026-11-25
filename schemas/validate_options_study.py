#!/usr/bin/env python3
"""Check core options-fixture structure and source-use gates using stdlib only.

This intentionally is not a complete JSON Schema 2020-12 validator. Use a full
validator before connecting the schema to production ingestion.
"""

import argparse
import hashlib
import json
from pathlib import Path


REQUIRED_BY_TYPE = {
    "pm_threshold_quote": [
        "venue", "event_id", "market_id", "contract_id", "underlying", "strike",
        "expiry", "event_definition", "yes_quote",
    ],
    "listed_option_quote": [
        "venue", "option_id", "underlying", "right", "strike", "expiry",
        "exercise_style", "settlement_style", "quote",
    ],
    "normalized_match": [
        "pm_record_id", "option_record_ids", "reference_price", "forward_price",
        "rates", "dividends_or_carry", "max_quote_skew_seconds", "match_status",
        "quality_flags",
    ],
    "derived_estimate": [
        "input_record_ids", "claim_type", "estimate_type", "value", "uncertainty",
        "assumptions", "limitations",
    ],
}
BASE_REQUIRED = ["record_id", "record_type", "data_status", "source", "observed_at_utc"]
ALLOWED_RIGHTS = {"approved", "blocked", "unresolved", "not_applicable"}


def validate_snapshot(snapshot, requested_uses=()):
    """Raise ValueError for missing core fields or an unapproved real-data use."""
    if snapshot.get("schema_version") != "1.0.0":
        raise ValueError("unsupported schema_version")
    synthetic = snapshot.get("synthetic_fixture")
    if not isinstance(synthetic, bool):
        raise ValueError("synthetic_fixture must be a boolean")
    manifest = snapshot.get("manifest")
    if not isinstance(manifest, dict):
        raise ValueError("manifest is required")
    if manifest.get("synthetic_fixture") is not synthetic:
        raise ValueError("snapshot and manifest synthetic_fixture flags differ")
    records = snapshot.get("records")
    if not isinstance(records, list) or not records:
        raise ValueError("records must be a non-empty list")
    seen_ids = set()
    for record in records:
        kind = record.get("record_type")
        if kind not in REQUIRED_BY_TYPE:
            raise ValueError(f"unsupported record_type: {kind}")
        required = BASE_REQUIRED + REQUIRED_BY_TYPE[kind]
        missing = [field for field in required if field not in record]
        if missing:
            raise ValueError(f"{kind} missing required fields: {', '.join(missing)}")
        if record["record_id"] in seen_ids:
            raise ValueError(f"duplicate record_id: {record['record_id']}")
        seen_ids.add(record["record_id"])
        if record["data_status"] not in {"observed", "synthetic"}:
            raise ValueError(f"unsupported data_status in {record['record_id']}")
        if synthetic and record["data_status"] != "synthetic":
            raise ValueError("synthetic fixture cannot contain observed records")
        if record["data_status"] == "synthetic" and not synthetic:
            raise ValueError("synthetic record must be inside a synthetic fixture")

        source = record.get("source")
        rights = source.get("rights") if isinstance(source, dict) else None
        if not isinstance(rights, dict):
            raise ValueError(f"source rights missing in {record['record_id']}")
        for use, status in rights.items():
            if use in {"access", "internal_research", "raw_storage", "derived_data", "team_sharing", "dashboard_display", "commercial_use"} and status not in ALLOWED_RIGHTS:
                raise ValueError(f"invalid rights status {status!r} for {use}")

        if record["data_status"] == "observed":
            if rights.get("access") != "approved":
                raise ValueError(f"access is not approved for {record['record_id']}")
            for use in requested_uses:
                if rights.get(use) != "approved":
                    raise ValueError(f"{use} is not approved for {record['record_id']}")

    artifact = manifest.get("artifact")
    if not isinstance(artifact, dict):
        raise ValueError("manifest artifact is required")
    artifact_path = Path(__file__).resolve().parents[1] / artifact.get("path", "")
    if not artifact_path.is_file():
        raise ValueError(f"manifest artifact does not exist: {artifact_path}")
    payload = artifact_path.read_bytes()
    if len(payload) != artifact.get("byte_count"):
        raise ValueError("manifest artifact byte_count does not match the file")
    if hashlib.sha256(payload).hexdigest() != artifact.get("sha256"):
        raise ValueError("manifest artifact sha256 does not match the file")
    if artifact.get("row_count") != len(records):
        raise ValueError("manifest artifact row_count does not match records")
    if json.loads(payload.decode("utf-8")) != records:
        raise ValueError("manifest artifact payload differs from snapshot records")
    return True


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", nargs="?", default=str(Path(__file__).parent / "examples/options-study.synthetic.json"))
    parser.add_argument("--requested-use", action="append", default=[], help="Required approved use for observed records; may be repeated")
    args = parser.parse_args()
    snapshot = json.loads(Path(args.snapshot).read_text(encoding="utf-8"))
    validate_snapshot(snapshot, args.requested_use)
    print(f"Valid core structure and rights gate: {args.snapshot}")


if __name__ == "__main__":
    main()
