"""Validate the study-record fixtures against the schema's supported keywords.

This small standard-library checker intentionally supports the keywords used by
study-record.schema.json, so the repository does not need a third-party runtime
dependency just to inspect the illustrative examples.
"""

from __future__ import annotations

import copy
import json
import re
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parent
SCHEMA_PATH = ROOT / "study-record.schema.json"
STATUS_REGISTRY_PATH = ROOT / "evidence-statuses.json"
EXAMPLES = sorted((ROOT / "examples").glob("*.json"))


class ValidationError(ValueError):
    pass


def resolve_ref(schema: dict[str, Any], ref: str) -> dict[str, Any]:
    if not ref.startswith("#/$defs/"):
        raise ValidationError(f"Unsupported schema reference: {ref}")
    name = ref.removeprefix("#/$defs/")
    try:
        return schema["$defs"][name]
    except KeyError as exc:
        raise ValidationError(f"Unknown schema reference: {ref}") from exc


def type_matches(value: Any, expected: str) -> bool:
    if expected == "object":
        return isinstance(value, dict)
    if expected == "array":
        return isinstance(value, list)
    if expected == "string":
        return isinstance(value, str)
    if expected == "integer":
        return isinstance(value, int) and not isinstance(value, bool)
    if expected == "number":
        return isinstance(value, (int, float)) and not isinstance(value, bool)
    if expected == "boolean":
        return isinstance(value, bool)
    if expected == "null":
        return value is None
    raise ValidationError(f"Unsupported JSON Schema type: {expected}")


def validate(value: Any, rule: dict[str, Any], root: dict[str, Any], path: str = "$", depth: int = 0) -> None:
    if depth > 40:
        raise ValidationError(f"Schema recursion limit exceeded at {path}")
    if "$ref" in rule:
        validate(value, resolve_ref(root, rule["$ref"]), root, path, depth + 1)

    if "oneOf" in rule:
        successes = 0
        errors = []
        for option in rule["oneOf"]:
            try:
                validate(value, option, root, path, depth + 1)
                successes += 1
            except ValidationError as exc:
                errors.append(str(exc))
        if successes != 1:
            raise ValidationError(f"{path}: expected exactly one oneOf branch, got {successes}; {errors}")

    if "type" in rule:
        expected = rule["type"] if isinstance(rule["type"], list) else [rule["type"]]
        if not any(type_matches(value, kind) for kind in expected):
            raise ValidationError(f"{path}: expected type {expected}")
    if "const" in rule and value != rule["const"]:
        raise ValidationError(f"{path}: expected constant {rule['const']!r}")
    if "enum" in rule and value not in rule["enum"]:
        raise ValidationError(f"{path}: value {value!r} is not in enum")

    if isinstance(value, dict):
        missing = [key for key in rule.get("required", []) if key not in value]
        if missing:
            raise ValidationError(f"{path}: missing required properties {missing}")
        properties = rule.get("properties", {})
        if rule.get("additionalProperties") is False:
            extra = sorted(set(value) - set(properties))
            if extra:
                raise ValidationError(f"{path}: unexpected properties {extra}")
        for key, child_rule in properties.items():
            if key in value:
                validate(value[key], child_rule, root, f"{path}.{key}", depth + 1)

    if isinstance(value, list):
        if len(value) < rule.get("minItems", 0):
            raise ValidationError(f"{path}: fewer than minItems")
        if "items" in rule:
            for index, item in enumerate(value):
                validate(item, rule["items"], root, f"{path}[{index}]", depth + 1)

    if isinstance(value, str):
        if len(value) < rule.get("minLength", 0):
            raise ValidationError(f"{path}: shorter than minLength")
        if "pattern" in rule and re.search(rule["pattern"], value) is None:
            raise ValidationError(f"{path}: does not match pattern")

    if isinstance(value, (int, float)) and not isinstance(value, bool):
        if value < rule.get("minimum", float("-inf")):
            raise ValidationError(f"{path}: below minimum")
        if value > rule.get("maximum", float("inf")):
            raise ValidationError(f"{path}: above maximum")
        if value <= rule.get("exclusiveMinimum", float("-inf")):
            raise ValidationError(f"{path}: not above exclusiveMinimum")


def validate_status_registry(schema: dict[str, Any], registry: dict[str, Any]) -> None:
    schema_statuses = set(schema["properties"]["evidence_status"]["enum"])
    registry_statuses = {entry["key"] for entry in registry.get("statuses", [])}
    if schema_statuses != registry_statuses:
        missing = sorted(schema_statuses - registry_statuses)
        extra = sorted(registry_statuses - schema_statuses)
        raise ValidationError(f"Evidence status registry mismatch; missing={missing}, extra={extra}")
    required_fields = {"minimum_evidence", "allowed_wording", "avoid_wording", "example"}
    for entry in registry["statuses"]:
        if not required_fields.issubset(entry):
            raise ValidationError(f"Status {entry.get('key')!r} is missing registry fields")


def validate_record_status(record: dict[str, Any], registry: dict[str, Any]) -> None:
    known = {entry["key"] for entry in registry["statuses"]}
    if record.get("evidence_status") not in known:
        raise ValidationError(f"Unknown evidence status: {record.get('evidence_status')!r}")


def main() -> None:
    schema = json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))
    registry = json.loads(STATUS_REGISTRY_PATH.read_text(encoding="utf-8"))
    validate_status_registry(schema, registry)
    print(f"PASS evidence status registry ({len(registry['statuses'])} entries match schema enum)")
    if not EXAMPLES:
        raise SystemExit("No study examples found")

    kinds = set()
    for example_path in EXAMPLES:
        record = json.loads(example_path.read_text(encoding="utf-8"))
        validate(record, schema, schema)
        validate_record_status(record, registry)
        kinds.add(record["domain"]["kind"])
        print(f"PASS {example_path.relative_to(ROOT)}")

    expected_kinds = {"weather", "cross_venue", "options"}
    if kinds != expected_kinds:
        raise SystemExit(f"Expected domain kinds {expected_kinds}, found {kinds}")

    negative = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
    negative = copy.deepcopy(negative)
    del negative["title"]
    try:
        validate(negative, schema, schema)
    except ValidationError:
        print("PASS missing-required-field rejection")
    else:
        raise SystemExit("Invalid record unexpectedly passed validation")

    negative_status = json.loads(EXAMPLES[0].read_text(encoding="utf-8"))
    negative_status["evidence_status"] = "unreviewed_claim"
    try:
        validate_record_status(negative_status, registry)
    except ValidationError:
        print("PASS unknown evidence status rejection")
    else:
        raise SystemExit("Unknown evidence status unexpectedly passed validation")

    incomplete_registry = copy.deepcopy(registry)
    incomplete_registry["statuses"].pop()
    try:
        validate_status_registry(schema, incomplete_registry)
    except ValidationError:
        print("PASS missing registry entry rejection")
    else:
        raise SystemExit("Registry missing a schema status unexpectedly passed validation")

    print(f"Validated {len(EXAMPLES)} examples and three negative cases.")


if __name__ == "__main__":
    main()
