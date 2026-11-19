# Source-neutral weather research helpers

This package contains validation and analysis utilities for the staged weather
study. The helpers operate on caller-provided records; they do not fetch market,
settlement, or forecast data.

## Settlement mappings

`settlement.validate_mapping` checks a family-aware mapping record for the event,
weather variable and unit, spatial support, timezone, validity window, resolution
authority and source, settlement rule/version, mapping status, and source-use
status. Verified mappings also need independent reviewer and evidence references;
ambiguous mappings need an explanation.

`settlement.outcome_join_eligible` is stricter: the mapping must be verified,
source use must be approved, and an approval evidence reference must be present.
Synthetic fixtures can exercise this path. Real mappings and outcome joins remain
blocked until the source-specific use and retention terms are recorded by the
authorized owner.

## Coverage reports

`coverage.build_coverage_report` aggregates caller-supplied manifest summaries
by weather family and data tier. Each denominator must be explicit; an unknown
denominator remains unknown instead of becoming zero. The report keeps backfill
and prospective summaries separate and requires source approval evidence before
classifying complete coverage as ready. It does not inspect market, outcome, or
forecast observations.

## Normalized batches

`dataset.require_source_permissions` must run before an adapter opens or iterates
its input. Normalization requires approved internal analysis and normalized-data
retention, plus a permission evidence reference. Source IDs are removed unless
their retention is explicitly permitted. `normalize_batch` canonicalizes UTC
timestamps, deduplicates identical `(record_type, record_key)` rows, and rejects
conflicting duplicates. Manifests contain counts and checksums, not record
payloads; Parquet output is written only after the same approval check. Current
fixtures use synthetic records only.

## Forecast alignment

`alignment.align_forecast` converts aware timestamps to UTC and accepts a pair
only when the issue time is no later than the decision time and the forecast
covers the contract window with matching variable, unit, timezone, and complete
location set. It reports rejection reasons and lead time; it does not infer
probabilities from ensemble spread or claim calibrated uncertainty.

## Market/model baseline

`baseline.compare_models` retains Yes/No sides, midpoint, spread, quote age,
model/run provenance, and family for each model separately. Midpoints remain
descriptive; executable side comparisons require evidence-backed approval,
verified settlement mapping, a coherent fresh top-of-book quote, and an eligible
forecast alignment. Incomplete ladders and data-quality flags stay visible. A
candidate gap is only a validation candidate, never a trading signal.

## Calibration validation

`calibration.chronological_event_split` orders events by their latest decision
time and keeps all records for one event together. `score_probabilities` reports
Brier score, clipped log loss, reliability-bin counts/rates, and Wilson intervals
for observed rates. `evaluate_chronological_holdout` requires an explicit
minimum holdout-event count and flags sparse results. Metrics require approved
source-use evidence and describe probability calibration only, not profitability.

## Dashboard handoff

`handoff-template.md` is a pending, source-neutral Weather report skeleton.
`handoff.validate_handoff` checks its family scope, evidence classes, deferred
family requirements, and recommendation. Observed/validated claims need approved
source status and validation references; the template contains no findings.

## Paper screen

`screen.screen_candidate` accepts an explicit policy for calibration sample
size, log loss, quote age, spread, minimum edge, and fill assumption. It requires
approved sources, verified settlement, aligned forecast, chronological held-out
calibration, top-of-book price and displayed size, and explicit fees. Results
can include a one-unit hypothetical settlement payoff, but always set
`live_execution` to false; candles and midpoint quotes cannot produce a paper
candidate.

Run the package's synthetic checks with:

```sh
python3 -m unittest discover -s weather/research/tests -p 'test_*.py'
```
