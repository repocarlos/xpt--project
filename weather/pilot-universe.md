# Weather Market Universe and Cohort Selection Protocol

**Protocol version:** 2
**Prepared:** 2026-11-19
**Status:** Source-neutral framework drafted; no new market IDs or rows added. Source-specific use rights and cohort coverage remain unresolved.

## Purpose and scope

Build a broad, extensible inventory of weather prediction-market events and select research cohorts from evidence. The research is not limited to NYC or daily temperature. Candidate families include temperature, precipitation and rain, snowfall, heat and cold events, wind and severe weather, tropical cyclones, and other hazards when their settlement rules and forecast evidence can be matched.

The inventory is a discovery and planning artifact. Listing a family or a source does not mean its data has been accessed, its coverage verified, or its use approved. Do not inspect or extract rows from sources whose intended uses are unresolved.

## Cohort status

Assign each candidate cohort exactly one status and record the evidence supporting transitions:

1. **Candidate** — family, venue, geography, event horizon, and likely settlement observable are described from permitted discovery sources.
2. **Metadata ready** — settlement fields and forecast mapping can be represented; ambiguities and evidence references are recorded.
3. **Rights approved** — the source owner or applicable license documents permission for each intended use: access, internal analysis, retention, derived data, sharing, and display.
4. **Coverage qualified** — approved evidence establishes history, quote/outcome availability, forecast vintage coverage, and estimated storage volume.
5. **Selected** — inclusion and exclusions are frozen for the analysis window before outcome-conditioned comparison.
6. **Deferred or no-go** — reason, unresolved gate, and condition for reconsideration are recorded.

Do not move a cohort forward based only on a venue API route, an existing local file, or another cohort's approval.

## Candidate family catalog

This is a taxonomy for discovery, not a claim that all families have available or comparable data. Add rows when permitted source documentation or approved metadata identifies a concrete cohort.

| Family | Example event variable | Settlement dimensions to verify | Forecast dimensions to match | Main comparability risks |
|---|---|---|---|---|
| Temperature | Daily high/low, hourly temperature, threshold exceedance | Station or grid, local day/hour, unit, aggregation, boundary inclusivity, source and rule version | Model, issue/run time, valid interval, location/grid, ensemble or distribution | Station differences, local-day definitions, unit conversion, overlapping buckets |
| Precipitation and rain | Daily total, hourly accumulation, rain/no-rain | Gauge or grid, accumulation window, trace threshold, unit, timezone, resolution source | Accumulation period, issue/valid time, grid, ensemble distribution | Gauge/grid mismatch, trace conventions, window boundaries |
| Snowfall | Snow accumulation, snow/no-snow | Observation source, liquid-equivalent versus snow depth, local window, unit, rule version | Snow variable, accumulation window, location/elevation, issue time | Measurement conventions, melting/settlement timing, elevation |
| Heat and cold | Heat index, wind chill, heatwave/freeze duration | Metric formula, station/source, duration rule, threshold, local time window | Derived metric formula, input variables, lead time, location | Formula/version differences, multi-day dependence, threshold ladders |
| Wind and severe weather | Sustained/gust speed, storm occurrence | Station/grid, gust definition, sustained interval, warning or observation source, event window | Variable, averaging interval, grid, issue and valid times | Gust versus sustained winds, warnings versus observations, spatial resolution |
| Tropical cyclones | Formation, track, landfall, intensity | Named authority, event identity, basin, landfall definition, intensity scale, time/version | Track/intensity forecast cycle, issue time, lead, geographic definition | Post-event best-track revisions, basin naming, forecast cone versus event point |
| Other hazards | Flood, drought, fire weather, severe convective event | Authoritative index/observation, spatial unit, threshold, duration, rule version | Matching index or input variables, spatial scale, issue/valid time | Composite indices, retrospective revisions, sparse events, inconsistent geography |

Keep unlike settlement definitions separate. Pool cohorts only after equivalence of outcome, event identity, time window, units, and spatial support is documented.

## Candidate and cohort record

Use one metadata record per venue-contract-event combination, then group records into versioned cohorts. Use stable internal identifiers; do not place unauthorized source identifiers or market values in this protocol.

Required fields:

* **Identity:** internal event key, cohort version, family, venue/source reference, contract reference when permitted, event start/end, local date or interval, timezone.
* **Place and variable:** country/region/city or grid reference, station/grid identifier where permitted, variable, unit, spatial resolution, elevation if material.
* **Settlement:** resolution authority, observation source, aggregation window, threshold/bucket, boundary convention, rule version/effective date, resolution timestamp, mapping status, reviewer and evidence reference.
* **Market evidence:** quote type/cadence, history period, event count, quote-side availability, outcome status, known depth/size limits, missingness and coverage denominator. Do not infer executable depth from candles.
* **Forecast evidence:** source and model family, archive period, issue/run and valid-time availability, location mapping, lead-time coverage, probability conversion feasibility.
* **Governance and scale:** source-specific use-rights reference and status by intended use, retention limit, estimated row/byte volume, partition plan, storage target, refresh cadence, and migration/export requirement.
* **Decision:** cohort status, inclusion/exclusion reason, decision date, owner, second-person reviewer, next gate, and caveats.

Keep raw quotes, outcomes, and forecast values in a separately controlled dataset only after the applicable rights and retention are documented. Link a selected cohort to a versioned manifest and checksum rather than copying raw values into this catalog.

## Selection and expansion rules

1. Inventory multiple families, venues, regions, and horizons before choosing cohorts. Do not assume NYC, a single venue, or daily temperature is the default.
2. Rank cohorts using documented settlement clarity, quote and outcome history, forecast vintage alignment, geographic/seasonal breadth, sample support, expected volume, and permitted uses. Preserve the evidence and weights used; do not score unknown coverage as zero or as a pass.
3. Freeze each cohort version and inclusion/exclusion reasons before comparing forecasts with outcomes or searching for probability gaps.
4. Establish family-specific sample and coverage thresholds from the available design and intended analysis before looking at outcome-conditioned results. Report denominators and missingness by family, venue, geography, and horizon; do not reuse the former NYC proposal as a global threshold.
5. Expand in waves: approved source metadata and schema; initial coverage audit; first selected cohort or cohorts; validated ingestion; then additional families and longer history as rights, volume, and data quality allow.
6. Record a no-go or revise decision when settlement mapping is ambiguous, vintage/quote coverage is inadequate, a source is not approved, or expected volume exceeds approved storage/retention.

## Source use and storage gates

The project source inventory does not currently establish intended-use permission for every weather market, settlement, or forecast source. Confirm access, internal research, retention, transformation, sharing, and retail display separately for each source. Until an approval or applicable license is recorded, do not inspect, parse, copy, derive, commit, or display that source's rows.

For approved cohorts, retain immutable source/version manifests and transformation provenance. Use portable, partitioned Parquet snapshots as the export and migration boundary. MotherDuck Lite may support a temporary internal research prototype only; it is not a public or retail serving target. Size partitions and refresh cadence from approved coverage evidence, enforce storage limits, and record checksums and retention dates. XPT Files are for small review artifacts, not the canonical raw-data archive.

## Review and next steps

1. Complete the weather-specific source and usage inventory and storage/manifest decisions.
2. Confirm which venues, regions, date horizon, and refresh cadence are in the first discovery pass; record a second weather-qualified reviewer.
3. Populate candidate records only from permitted discovery material. Keep unresolved sources marked blocked.
4. Map settlement semantics and audit history/forecast coverage per cohort before any large extraction.
5. Select and freeze cohorts only after rights, settlement, coverage, and storage gates pass.

This protocol is not approval to collect data, a coverage claim, or a trading recommendation.
