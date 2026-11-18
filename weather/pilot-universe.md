# NYC Daily High Temperature Pilot Universe

**Protocol version:** 1  
**Prepared:** 2026-11-18  
**Status:** Candidate-selection rules drafted; no market IDs populated. Awaiting source-use rights and weather-lead review.

## Research scope

Select contracts that resolve on the maximum temperature for one New York City local calendar day. Each event is keyed by venue, market ID, local event date, settlement station, temperature variable and unit, bucket/threshold, resolution source, observation window, and settlement-rule version. Keep each venue contract as its own observation until equivalence is verified.

Precipitation, snowfall, wind, hazards, multi-day aggregates, contracts for a different location or station, and contracts with unresolved or materially ambiguous settlement rules are out of scope.

## Proposed selection rules (Carlos to confirm)

1. Include only single-day NYC maximum-temperature contracts whose resolution rule identifies the settlement station, local date, measurement source, units, and observation window.
2. Treat threshold boundaries literally. Record inclusivity and units for every bucket. Only call a ladder exhaustive or mutually exclusive when its complete rule set supports that claim; otherwise analyze each contract separately.
3. Freeze the candidate list before examining model/forecast differences or outcome-conditioned performance. Record all exclusions and their reasons.
4. Use a common decision snapshot at **12:00 America/New_York on the preceding local calendar day**, accepting the nearest quote observation within **±5 minutes**. Retain bid, ask, displayed sizes when licensed, timestamp, and source. Do not treat the midpoint as executable.
5. Require a resolved official outcome from the station/source named in the contract rules. An unrelated station observation is not a substitute.
6. Proposed minimum: **30 unique event dates** and at least **80% coverage** of the frozen candidate set for both the decision-time quote and resolved outcome. Report coverage separately by horizon/bucket; do not relax the threshold after seeing results.
7. Keep wide spreads and missing sizes visible as quality flags; do not silently drop otherwise valid contracts for making the result look cleaner.

These numerical cutoffs and the 12:00 ET snapshot are proposals, not approved study decisions. Carlos should confirm or amend them before extracting data.

## Rights and data gate

As of 2026-11-18, the project inventory does not record approved rights for using the existing Kalshi snapshot in the shared research archive. The selected Kalshi API route and the presence of files in the repository do not establish permission. Settlement observations and forecast vintages also need source-specific rights and provenance review.

Until written authorization or an applicable license is recorded for each source and intended use:

* Do not inspect, parse, copy, derive, commit, or display market rows from the unresolved Kalshi snapshot.
* Do not add candidate market IDs, quotes, or outcomes to this repository.
* Use only a separately approved/licensed substitute, or leave the candidate universe pending.

The status below records a blocked gate, not an assertion that the universe has been checked.

| Input | Intended role | Internal research | Shared storage | Retail display | Coverage checked | Status |
|---|---|---|---|---|---|---|
| Kalshi | Contract metadata, quotes, settlement rules/outcomes | unresolved | unresolved | unresolved | no | blocked |
| Settlement source named in each contract | Official resolved temperature | unresolved | unresolved | unresolved | no | blocked |
| Forecast reference (later workstream) | Forecast vintage at decision time | unresolved | unresolved | unresolved | no | blocked |

## Candidate register fields

When the rights and review gates pass, add one row per venue-market-event combination with:

* `venue`, `market_id`, `event_date_local`, `timezone`
* `city`, `settlement_station_id`, `temperature_variable`, `unit`
* `bucket_lower`, `bucket_upper`, `boundary_convention`
* `resolution_source`, `observation_window`, `rule_version_or_capture_date`
* `quote_target_time_utc`, `quote_observed_time_utc`, `quote_within_tolerance`
* `quote_coverage_available`, `settlement_outcome_available`, `source_rights_reference`
* `selection_decision`, `exclusion_reason`

Do not put raw quote or settlement values in this index. Store authorized data only in the approved versioned data store, linked by a controlled dataset reference and checksum.

## Review and next step

Carlos: confirm or correct the scope, station/event identity, snapshot timing/tolerance, 30-event minimum, 80% coverage cutoff, and exclusions. After source rights are approved, populate and validate the dated register, then pass the station/rule mapping to GRO-28 and the coverage audit to GRO-29. Until then, no pilot IDs are selected and this task is not complete.
