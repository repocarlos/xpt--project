# Prediction-market study records

The shared study-record contract is in [`study-record.schema.json`](study-record.schema.json). It supplies a common reader-facing envelope while keeping weather probabilities, cross-venue quote gaps, and options-derived surfaces in separate typed `domain` variants. These outputs are not one cross-study score.

The records in [`examples/`](examples/) are illustrative fixtures, not market data or findings. They show the fields expected for the Weather, Polymarket–Kalshi, and options studies.

## Validation

Run the standard-library checker from the repository root:

```sh
python3 schemas/validate_study_examples.py
```

The checker validates the schema keywords used by this contract, all example fixtures, and rejection of a record missing a required field. The schema uses JSON Schema draft 2020-12.

## Versioning and review

The `schema_version` value is `1.0.0`. Increment the major version for breaking required-field or semantic changes, minor for compatible additions, and patch for clarifying descriptions that do not change validation. Each study record should keep its schema version with its data manifest.

Evidence-state definitions, minimum evidence, and allowed/avoided claim language are in [`evidence-statuses.md`](evidence-statuses.md) and [`evidence-statuses.json`](evidence-statuses.json). They are claim categories, not cross-study scores. The registry and schema enum are checked together. Definitions are ready for the three research leads' review; do not describe them as approved until that review happens.
