# Research data storage and manifest conventions

**Status:** proposed team convention; research-lead confirmation and storage-vendor setup are pending.
**Last reviewed:** 2026-11-18

## Storage roles

| Home | Keep here | Do not use it for |
|---|---|---|
| Shared Git repository | Analysis/ingestion code, schemas, documentation, tests, and small synthetic fixtures | Raw or canonical market, forecast, options, or settlement datasets; credentials; provider responses unless a source-specific policy explicitly permits this artifact |
| Team-controlled durable object storage | Canonical raw/normalized/derived data in versioned Parquet datasets; append-only, versioned contract rules; manifests | The only copy of code or undocumented outputs |
| XPT Files | Small, reviewable reports, charts, manifests, and permitted frozen extracts | The canonical archive or any raw/derived source data whose rights do not permit upload and sharing |
| Harness VPS / working directory | Temporary processing copies and code checkout | The only durable copy, a shared archive, or a backup |

Use Parquet for new tabular datasets. Partition datasets by `venue=<slug>/date=YYYY-MM-DD/`; keep market identifiers in row fields and file names (or a bounded market partition only when it avoids tiny files). Keep settlement-rule text and versions in a separate append-only record so a changed rule does not silently overwrite the definition used by an earlier study. Keep raw, normalized, and derived datasets in separate prefixes, each with a dataset version.

Choose a team-controlled S3-compatible store before any live collector starts. It must support persistent team access, object versioning, encryption in transit and at rest, least-privilege credentials, and a separate backup/restore path. Record retention and restoration ownership with the vendor decision. Do not put storage credentials in Git, task descriptions, XPT Files, or manifests.

## Source-use gate

An endpoint, account, sample file, or vendor marketing claim is not permission. Before collecting or retaining a source, record the current terms/version and confirm each intended use independently: access, internal research, raw storage, derived data, team sharing, dashboard display, and commercial use where relevant. Mark each status `approved`, `blocked`, or `not_applicable`, with the approving basis and date. A collector must refuse to persist non-synthetic data unless every use required by that pipeline is `approved`. Recheck terms when the source, audience, or use changes. The current source-by-source status is in [`source-inventory.md`](source-inventory.md).

The included `manifest.example.json` is synthetic and carries no market data. It demonstrates fields only; it does not approve any source or storage location.

## Manifest requirements

Every dataset version has one immutable manifest alongside the dataset. Required fields:

- manifest and dataset schema versions;
- stable dataset ID and source provider/source ID, documentation URL, access method, and terms review date;
- collection timestamp and event-time coverage as ISO 8601 UTC; preserve the source's local settlement timezone separately;
- exact source venue/event/market/contract identifiers and settlement-rule version;
- transformation names and versions, parameters, and parent dataset IDs/checksums;
- separate rights statuses and basis for all uses represented by the dataset;
- artifact path, format, row count, byte count, and SHA-256 checksum of the exact stored object;
- storage URI, immutable dataset version, and creation code commit.

Do not overwrite a manifest or dataset version. A correction creates a new version linked to its parent, with the reason and timestamp. For streaming snapshots, store source event time separately from received/collected time; never label a local date as UTC without conversion.

## Before first live capture

1. Research lead confirms market IDs, settlement source/rule versions, and data semantics.
2. Source owner records written rights or an applicable license for capture, retention, transformation, team access, and intended dashboard display.
3. Team chooses the durable object store, retention policy, backup destination, and access-control owner.
4. Recorder validates each manifest and refuses unapproved sources; test on synthetic fixtures first.
5. Save the manifest, schema version, code revision, and object checksum before publishing any study output.

See [`/docs/research/data-collection-plan`](https://app.xpt.ai/columbiafineng/docs/research/data-collection-plan) for source paths, retention caveats, and study sequencing.
