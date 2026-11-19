# Weather Market Universe: Metadata and Dataset Contract

**Version:** 1
**Prepared:** 2026-11-19
**Status:** Source-neutral specification; no source rows or credentials included.

## Design goals

Support a large historical dataset across multiple weather event families while preserving the details needed to determine what a contract settles on, what information was available at each quote time, and whether the data may be used for a given purpose. Add families through metadata and variable registries rather than family-specific columns or a forced cross-family score.

## Entity and key model

Use normalized entities with stable internal keys and versioned source references. One event can map to multiple contracts and quote snapshots; one forecast run can cover many events. A contract must not be treated as an event outcome until its settlement mapping is verified.

| Entity | Grain | Required fields |
|---|---|---|
| `weather_cohort` | Versioned study cohort | `cohort_id`, `cohort_version`, `family`, `status`, `selection_date`, `inclusion_rule_ref`, `source_use_status`, `review_status` |
| `weather_event` | One real-world weather event/window | `event_key`, `family`, `variable`, `location_key`, `valid_start_utc`, `valid_end_utc`, `timezone`, `season_or_period` |
| `weather_contract` | Venue contract linked to an event | `contract_key`, `event_key`, permitted `source_contract_ref`, venue, rule version, threshold/bucket, unit, boundary rule, settlement authority, mapping status |
| `weather_quote` | One quote observation/side set | `contract_key`, observed UTC time, source time, bid, ask, sizes only when permitted, quote type, source manifest, quality flags |
| `weather_forecast` | One model-run/location/variable/valid-window output | model, run ID, issue UTC time, valid window, location mapping, variable, unit, lead, member or probability representation, source manifest |
| `weather_outcome` | One authoritative settlement observation | `event_key`, resolution source, observed value or resolved category, unit, observed window, resolution time, rule version, provenance, revision status |
| `source_manifest` | One immutable retrieval or licensed data batch | source, license/use reference, intended uses, retrieval time, source version, date range, row count, byte count, checksum, retention date, transformation version |
| `coverage_summary` | Cohort/source/family/time slice | denominator definition, event count, quote/outcome/forecast counts, missingness, date range, estimated bytes, evidence reference |

Keep dimensions normalized: `family` and `variable` come from registries; location mapping can point to a station, grid cell, polygon, basin, or other explicit spatial support. Cross-location and joint-outcome cohorts must retain the complete location set and dependence definition. Preserve both source timestamps and normalized UTC timestamps, plus local timezone and window definitions. Long-horizon climate or seasonal benchmarks must retain their climatology reference period and revisions; short-range daily forecasts are not a substitute.

## Data quality and analysis rules

* Keep Yes bid, Yes ask, No bid, No ask, midpoint, spread, sizes, and quote age distinct when available and permitted. A midpoint is not an executable quote.
* Preserve contract bucket boundaries and units exactly. Do not infer a complete or mutually exclusive ladder from partial contracts.
* A forecast is eligible for a decision snapshot only if its issue time is no later than that snapshot. Match valid interval, variable, unit, and spatial support; retain the original model/run identity.
* Keep settlement corrections or revised authoritative observations versioned. Do not silently overwrite resolved outcomes.
* Calculate coverage with explicit denominators at cohort, family, geography, horizon, and source levels. Missing values are not zero, and unavailable quote depth is not inferred from candles.
* Use event-level chronological splits. Related contracts for the same event stay in one split. Pool families only when outcome definitions are demonstrably comparable.

## Large-data layout and manifests

For the operational lifecycle, manifest fields, volume sizing, retention, migration, and stop gates, follow [Weather Data Storage and Capture Plan](storage-and-manifest.md).

1. Store only approved sources and permitted fields. The manifest must reference the approval/license and intended uses, not merely a source URL.
2. Write immutable raw/landing snapshots separately from normalized research tables where retention terms permit. Never mix raw and derived permissions.
3. Use versioned Parquet partitions such as `source/family/year/month` or `source/family/event_date`; choose partition size from observed query patterns and approved volume. Avoid one tiny file per event and avoid unbounded monolithic files.
4. Write a manifest for every batch with schema version, date coverage, row and byte counts, null/quality counts, source timestamps, retrieval code version, transformation version, checksum, and retention date.
5. Make transformations idempotent by manifest and source key. Preserve corrections as new versions or explicit superseding records.
6. Use MotherDuck Lite only for an internal prototype during its applicable plan/terms. Keep schemas and transforms portable and test export/import through Parquet before any migration or external serving. The long-term canonical archive and public serving target still need an approved project decision.
7. Estimate growth from authorized coverage samples before setting a refresh cadence or retention promise. Stop expansion before an approved storage or retention limit is exceeded.

## Governance gates

Track each source's permitted use independently for access, internal analysis, retention, derived outputs, team sharing, and retail display. Candidate discovery is not equivalent to raw-data approval. If any required permission is unresolved, use an empty schema or clearly synthetic fixture and do not access source rows.

## Validation checklist

- Every contract references an event and a versioned settlement mapping.
- Every quote and forecast has source and observed/issue time provenance.
- Forecast issue time is not later than the decision time used in a comparison.
- Units, timezones, spatial mappings, and settlement windows are explicit.
- Manifests reconcile to partitions by row count, date range, and checksum.
- Re-runs do not duplicate records; source corrections remain traceable.
- Coverage is reported by weather family and does not hide sparse cohorts in a pooled total.
- No unapproved source rows or identifiers enter the repository, test fixtures, or dashboard artifacts.
