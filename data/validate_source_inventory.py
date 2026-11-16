"""Check required source inventory fields and Markdown/JSON row-key parity."""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
INVENTORY = ROOT / "source-inventory.json"
MARKDOWN = ROOT / "source-inventory.md"
REQUIRED = {
    "source_id", "legs", "owners", "role", "provider", "endpoints_or_identifiers",
    "documented_coverage", "cadence", "retention_or_limits", "usage_terms_status",
    "usage_terms", "material_gaps", "next_verification", "proposed_capture_start",
    "status", "references",
}


class InventoryError(ValueError):
    pass


def validate(data: dict[str, Any], markdown: str) -> None:
    rows = data.get("sources")
    if not isinstance(rows, list) or not rows:
        raise InventoryError("sources must be a non-empty list")
    ids = [row.get("source_id") for row in rows]
    if len(ids) != len(set(ids)):
        raise InventoryError("source_id values must be unique")
    for row in rows:
        missing = REQUIRED - set(row)
        if missing:
            raise InventoryError(f"{row.get('source_id')}: missing fields {sorted(missing)}")
        if row["status"] not in data["status_values"]:
            raise InventoryError(f"{row['source_id']}: unknown status {row['status']!r}")
        if row["usage_terms_status"] not in data["status_values"]:
            raise InventoryError(f"{row['source_id']}: unknown usage status")
        if not row["owners"] or not row["legs"] or not row["references"]:
            raise InventoryError(f"{row['source_id']}: owners, legs, and references must be present")
        for reference in row["references"]:
            if not reference.get("url", "").strip():
                raise InventoryError(f"{row['source_id']}: reference URL is empty")

    markdown_ids = set(re.findall(r"^\| `([^`]+)` \|", markdown, flags=re.MULTILINE))
    if markdown_ids != set(ids):
        raise InventoryError(f"Markdown/JSON source IDs differ: md={sorted(markdown_ids)}, json={sorted(ids)}")


def main() -> None:
    data = json.loads(INVENTORY.read_text(encoding="utf-8"))
    markdown = MARKDOWN.read_text(encoding="utf-8")
    validate(data, markdown)
    print(f"PASS {len(data['sources'])} source rows; required fields, references, and Markdown IDs match")

    invalid = copy.deepcopy(data)
    del invalid["sources"][0]["owners"]
    try:
        validate(invalid, markdown)
    except InventoryError:
        print("PASS missing required-field rejection")
    else:
        raise SystemExit("Inventory missing a required field unexpectedly passed validation")


if __name__ == "__main__":
    main()
