# Options-study data contract

**Status:** synthetic schema example for review; it does not approve any market-data source or storage destination.

## Record layers

The versioned JSON Schema at `schemas/options-study.schema.json` describes the logical shape of a study snapshot. A snapshot may contain four record types:

1. `pm_threshold_quote`: one terminal threshold contract's YES quote and its exact settlement definition.
2. `listed_option_quote`: one listed option quote, including exercise and settlement style.
3. `normalized_match`: the join between quote records, including the reference price, timestamp tolerance, carry inputs, and quality flags.
4. `derived_estimate`: a PM digital bound or a synthetic-call/Black–Scholes-equivalent estimate, with assumptions and uncertainty preserved.

Quote sides, sizes, source identifiers, event time, receipt time, and local settlement timezone are separate fields. Missing or rejected inputs should be represented by explicit flags or omitted records with a reason; they must not be silently replaced with stale data. A `derived_estimate` records its claim type: a PM event-price convention is not automatically a risk-neutral probability, and a PM-derived Black–Scholes-equivalent IV is not a listed vanilla IV quote.

## Rights and persistence gate

Each source carries separate statuses for access, internal research, raw storage, derived data, team sharing, dashboard display, and commercial use. `unresolved` or `blocked` means the relevant pipeline must not collect or persist that source's real data. Endpoint availability, an account, or a sample file is not permission. The source-use review and allowed uses must be recorded before real data is collected, retained, derived, shared, or displayed.

The included fixture is invented and uses `synthetic_fixture: true`; it contains no venue identifiers or observed market prices. It is safe to keep with code and schemas in Git. Do not place real raw or derived data in Git or XPT Files unless a source-specific policy expressly permits it.

## Storage path

MotherDuck Lite is a temporary, internal-only analysis path. Keep the logical records portable and export tabular research datasets to Parquet. Before live capture or external retail testing, choose a team-controlled durable object store, versioning, access controls, retention owner, and a separate backup/restore path. The harness working directory is temporary and must not be the sole copy. The shared convention remains subject to review in GRO-26; this options document does not supersede it.

For each persisted dataset version, keep an immutable manifest with source and terms-review provenance, settlement-rule version, timezone, collection/event-time coverage, transformations and parent versions, schema version, storage URI, exact-object SHA-256, and code revision. A correction creates a new version rather than overwriting prior data.

## Fixture and schema

`schemas/examples/options-study.synthetic.json` demonstrates a matched synthetic threshold/options snapshot. Its numerical values and identifiers are fabricated solely to exercise the record shape. The manifest checksums the exact `schemas/examples/options-study.synthetic.records.json` payload, avoiding a self-referential checksum. `schemas/options-study.schema.json` is the machine-readable contract; its version is carried by the fixture and manifest.
