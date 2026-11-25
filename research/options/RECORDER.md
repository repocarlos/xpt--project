# Options fixture recorder

This is a local, synthetic-fixture recorder for testing the options study's Parquet and manifest contract. It has no venue API client, credentials, or enabled live mode. The source-approval and durable-storage decisions remain open, so no market data is collected or written by this tool.

Run from the repository root:

```sh
python3 -m research.options.record_fixture \
  --fixture research/options/fixtures/recorder_fixture_v1.json \
  --output-root /tmp/options-recorder-fixtures
```

The output uses venue/date/market partition directories. The sidecar manifest records the synthetic status, rights blocker, schema version, source identifiers, settlement-rule versions, transformation list, logical record hash, local-only storage status, code revision, and per-file byte count and SHA-256. Exact duplicate fixture rows are collapsed; distinct quote records remain distinct. Re-running the same fixture replaces its own generated dataset directory rather than appending rows.

Verify a dataset with DuckDB:

```sql
SELECT venue, record_type, count(*)
FROM read_parquet('/tmp/options-recorder-fixtures/fixture-*/**/*.parquet')
GROUP BY venue, record_type;
```

`--live` always exits with a refusal before creating output. Live collection requires separate approval for access, collection, raw storage, derivation, team sharing and display, plus an approved durable team-owned target, cadence, retention and backup owner. Those decisions must be made before adding a source adapter.

The fixture shape is versioned independently as `options.recorder_fixture.v1`. Align it with the reviewed GRO-72 options schema and GRO-26 shared storage convention before any production ingestion. This implementation does not establish data permissions or satisfy the empirical matched-sample gate.
