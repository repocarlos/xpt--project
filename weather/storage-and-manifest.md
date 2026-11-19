# Weather Data Storage and Capture Plan

**Version:** 1
**Prepared:** 2026-11-19
**Status:** Design only. No storage service was provisioned and no source data was captured.

## Governing rules

1. A source route, public endpoint, or existing file does not establish permission. Before retrieval, record the applicable license or written approval for access, internal analysis, raw retention, transformation, derived data, sharing, and retail display separately.
2. Apply the most restrictive source retention and use condition to each raw, normalized, and derived dataset. If retention of raw responses is not allowed, retain only the permitted fields and a provenance manifest.
3. Keep MotherDuck Lite as a temporary internal research prototype. Do not expose it to retail users or treat it as the durable canonical archive. Keep research schemas portable and use Parquet for export and migration.
4. The canonical long-term archive and serving destination remain a project decision. Do not provision or promise one until its owner, permissions, region, budget, access controls, backup, and retention are approved.
5. Use XPT Files for small review artifacts, not as the canonical archive for large weather histories.

## Dataset lifecycle

| Stage | Entry condition | Required record and action | Exit condition |
|---|---|---|---|
| Candidate inventory | Permitted source discovery | Family, venue/source, geography, date horizon, intended use, known terms, likely cadence, unknowns | Source-specific review is assigned |
| Rights and retention review | Candidate documented | Approval/license reference for each intended use; retention and derived-data limits | Required access, internal analysis, and retention uses are approved |
| Coverage and volume estimate | Approved documentation or permitted metadata | Date range, event and quote/outcome coverage, forecast vintage coverage, estimated rows/bytes, refresh needs | Feasible volume, retention, and storage path are documented |
| Limited authorized capture | Source approval and capture plan complete | Versioned manifest, bounded date/family scope, checksums, quality counts, access controls | Reproducible validation passes and actual volume is measured |
| Historical backfill and refresh | Limited capture reviewed; expansion approved | Idempotent backfill in bounded partitions; schedule follows provider limits and study need | Family-level coverage and storage budgets remain within the approved plan |
| Normalize and derive | Field-level permission permits processing | Versioned transformations, stable event keys, missingness and corrections preserved | Output reconciles to source manifests |
| Export, migrate, or expire | Export rights and target approved | Parquet snapshot and manifest; migration check; retention/deletion evidence | Destination verifies checksum or expiry is recorded |

Never advance a source through a lifecycle stage based only on a workspace task being marked done; the permission evidence itself must be recorded.

## Source and dataset manifest

Create one immutable manifest per retrieval batch, licensed dataset version, or exported partition. Use a separate manifest for each source and permission scope; do not combine raw and derived data with different rights.

| Field | Required meaning |
|---|---|
| `manifest_id` | Stable internal identifier for this immutable batch |
| `source_name`, `source_version` | Provider/source identity and API, archive, or publication version when available |
| `license_or_approval_ref` | Link or internal record for the applicable terms; `unresolved` blocks capture |
| `permitted_uses` | Explicit allowed uses and restrictions for this batch |
| `family`, `cohort_id`, `cohort_version` | Weather family and frozen cohort definition represented |
| `retrieved_at_utc`, `source_as_of` | Retrieval time and source publication/as-of time if distinct |
| `coverage_start`, `coverage_end`, `timezone` | Event-time coverage and the calendar/timezone interpretation |
| `schema_version`, `extractor_version`, `transform_version` | Reproducible schema and code lineage |
| `partition_paths` | Immutable object or file paths covered by the manifest |
| `row_count`, `byte_count` | Reconciled record and storage counts |
| `null_counts`, `quality_counts` | Missingness, duplicate, parse, mapping, and validation summaries |
| `sha256` | Checksum for every immutable file or a documented aggregate checksum |
| `retention_until`, `access_classification` | Earliest required expiry and permitted audience |
| `supersedes_manifest_id`, `correction_reason` | Explicit link when a corrected source version replaces earlier data |

An empty template can be prepared before source approval, but it must contain no provider identifiers, observed values, credentials, or copied source responses. A completed manifest must refer to the evidence that authorizes its batch.

## Partitioning and volume planning

Partition by source, weather family, and event date (for example, year/month) when permitted by source terms. Keep partitions large enough to avoid one small file per event, while bounding backfill and correction scope. Choose file and partition size only after measuring an authorized sample and the expected query patterns.

Estimate total storage from measured cohort rates rather than a blanket daily volume:

* `events × quote observations per event × average encoded quote bytes`
* `events × forecast models × runs/leads × members or probability bins × average encoded forecast bytes`
* settlement and contract metadata, manifest/index overhead, and permitted raw-source copies
* retained historical versions and corrections, plus export/migration overlap

Record assumptions separately for each family, source, refresh cadence, and retention period. Re-estimate after a bounded approved capture and before adding a family or expanding the history window. If measured growth exceeds the approved budget or retention limit, stop expansion and revise the plan.

## Reproducibility, corrections, and recovery

* Make ingestion idempotent using the permitted source key plus source version and observation timestamp. Re-running the same manifest must not add duplicate logical records.
* Preserve source corrections as new manifest versions or explicit superseding records; never silently overwrite a resolved value or settlement rule.
* Keep normalized data partitioned and versioned with the source manifest, cohort version, schema version, and transformation version.
* Before migration, export a bounded Parquet snapshot, verify every file checksum, compare row counts and coverage summaries, then import into the candidate target and rerun the same reconciliation.
* Document backup and restore procedures only after a durable target is selected. MotherDuck Lite alone is not the archive or backup plan.
* Enforce source-specific deletion dates and record expiry/deletion completion; a manifest does not extend a source's permitted retention.

## Readiness checklist for large extraction

- [ ] Weather-specific source rights are recorded for every required intended use.
- [ ] Shared source and storage standards plus the weather children are reviewed.
- [ ] Settlement mapping and forecast-vintage coverage are qualified by family.
- [ ] Approved sample sizes, history window, cadence, byte estimates, and retention are measured and reviewed.
- [ ] Manifest/schema versions and immutable partition paths are agreed.
- [ ] Internal access controls, backup/restore, export, and migration responsibilities are assigned.
- [ ] A stop condition is defined for rights changes, budget/retention limits, or quality failures.

Until every relevant item passes, use schema-only documentation or synthetic fixtures; do not run live extraction.
