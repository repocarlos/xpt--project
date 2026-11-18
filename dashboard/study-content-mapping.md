# Study schema to dashboard content mapping

**Status:** draft for research-lead and product review  
**Schema:** `schemas/study-record.schema.json` v1.0.0  
**UI basis:** `dashboard/wireframes.md`  
**Data note:** schema fixtures are illustrative; this mapping does not authorize live source data.

## Shared study envelope

| Schema path | Page component | Display and missing-value behavior |
|---|---|---|
| `schema_version` | Provenance details | Show in expandable reproducibility section; unsupported version blocks rendering and raises data-quality state. |
| `study_id` | Page metadata / stable route | Use as stable internal identifier; invalid/absent required ID is an error, not a title fallback. |
| `study_type` | Study kind badge | Human-readable type badge; unknown type is unavailable. |
| `sector` | Breadcrumb and sector label | Show group context; do not imply one pilot represents the full sector. |
| `title` | Page heading | Required; missing title is a data-quality error. |
| `research_question` | Summary panel | Plain-language question near title. |
| `example_notice` (optional) | Persistent notice | If present, display before metrics (e.g. synthetic fixture notice); never remove a fixture warning. |
| `contract_scope.description` | Contract context | Explain pilot market scope in plain language. |
| `contract_scope.markets[*].venue` | Contract identity | Show the market venue beside the contract example. |
| `contract_scope.markets[*].market_id` | Contract identity / source link | Display only where source terms permit; otherwise show a permitted masked label, never fabricate an ID. |
| `contract_scope.markets[*].question` | “What does it resolve on?” | Show the exact contract question. |
| `contract_scope.markets[*].resolution_source` | Resolution context | Name and link the settlement source when permitted. |
| `contract_scope.markets[*].rule_version` | Resolution context | Show rule version/capture date and link to the immutable rule text. |
| `contract_scope.markets[*].timezone` | Resolution context | Always pair event dates/times with this timezone. |
| `contract_scope.markets[*].valid_from`, `valid_to` (optional) | Resolution context | Show effective range if supplied; otherwise omit the range, not the rule itself. |
| `data_coverage.start`, `end` | Sample coverage | Show event/data period with explicit timezone convention. |
| `data_coverage.sample_count` | Sample coverage | Show unit of count from study definition (events/contracts/quotes), not a bare number. |
| `data_coverage.coverage_summary` | Coverage summary | Required plain-language coverage statement. |
| `data_coverage.known_gaps[*]` | Coverage caveats | Render as visible gaps; do not silently omit missing periods/markets. |
| `method.summary` | Method panel | Explain comparison and decision-time choices. |
| `method.benchmark` (optional) | Benchmark label | Name benchmark and source; if absent, say no benchmark is specified. |
| `method.analysis_version` (optional) | Reproducibility | Link/tag the analysis version if present. |
| `method.evaluation_split` (optional) | Evaluation design | Show chronological/event split for scored results; if absent, do not imply held-out validation. |
| `findings.summary` | Finding summary | Place evidence status adjacent to the text; do not use stronger wording than the registry allows. |
| `findings.metrics[*].name`, `value`, `unit`, `definition` | Metric cards/table | Show name, value, unit, and definition together. A missing required metric cell is “not reported,” not zero. |
| `uncertainty.summary`, `uncertainty.items[*]` | Uncertainty panel | Show summary and itemized caveats next to interpretation. |
| `limitations[*]` | Limitations panel | Always visible in the main page flow; never bury or omit. |
| `evidence_status` | Evidence badge | Resolve wording via `schemas/evidence-statuses.json`; show minimum evidence and avoid an ordinal cross-sector score. |
| `updated_at` | Study artifact freshness | Label “Study updated”; do not call it a market quote time. |
| `sources[*].name`, `uri`, `role` | Sources panel | Name each source, its study role, and permitted source link. Missing required source blocks publication. |
| `sources[*].accessed_at` (optional) | Sources/freshness | Show retrieval time if present; distinguish from event time and quote time. |
| `sources[*].usage_terms` (optional) | Sources/rights details | Link or summarize terms; do not treat text presence as an approved-rights flag. |
| `reproducibility.repository_uri`, `code_path`, `code_commit` (commit optional) | Reproducibility | Link the code and pin the exact commit when available. |
| `reproducibility.data_manifest_uri` | Data provenance | Link the permitted immutable manifest. Rights state must come from that manifest/approved rights registry, not inferred from a source name. |
| `reproducibility.settlement_rules_uri` (optional) | Resolution rules | Link the versioned rule record if supplied. |

## Domain modules and chart inputs

### Weather: daily temperature markets

| Schema path | Component / chart input | Display behavior |
|---|---|---|
| `domain.kind` | Weather module selector | Must equal `weather`; otherwise reject this module. |
| `domain.market_probabilities[*].market_id`, `outcome` | Market outcome table | Join to the exact contract identity; show bucket and YES/NO orientation. |
| `domain.market_probabilities[*].yes_bid`, `yes_ask`, `midpoint` | Market quote panel / time-series | Label each side; midpoint is an observed display convention, not an executable price or a true probability. |
| `domain.market_probabilities[*].quote_time` | Quote freshness | Show quote timestamp/timezone beside each displayed price. |
| `domain.forecast_probabilities[*].model`, `outcome`, `probability` | External forecast table / comparison chart | Keep forecast probability separate from market-implied price; label units/outcome. |
| `domain.forecast_probabilities[*].issued_at`, `valid_time` | Forecast-vintage details | Show both issue time and target validity time; a forecast issued after the quote/outcome is not a valid comparison. |
| `domain.calibration[*].metric`, `value`, `sample_count`, `split` (optional) | Reliability/calibration panel | Show Brier/log loss with sample count and split. If absent, say calibration not evaluated; do not infer forecast skill. |

Recommended view: market quote and forecast probabilities by lead time, followed by calibration only when present. Surface station, local date, threshold, quote time, and forecast issue time.

### Cross-venue: Polymarket and Kalshi

| Schema path | Component / chart input | Display behavior |
|---|---|---|
| `domain.kind` | Cross-venue module selector | Must equal `cross_venue`; otherwise reject this module. |
| `domain.matched_pairs[*].market_a_id`, `market_b_id` | Matched-contract table | Show venue and exact ID only if permitted; both IDs required to present a pair. |
| `domain.matched_pairs[*].equivalence_summary` | Settlement-match panel | State outcome, payout, source, and rule comparison; unmatched pairs are not price-gap comparisons. |
| `domain.quote_observations[*].market_id`, `venue` | Paired quote table | Link each quote to its venue/contract. |
| `domain.quote_observations[*].bid`, `ask`, `midpoint` | Paired quote plot/table | Label quote side; show spread; midpoint is descriptive only. |
| `domain.quote_observations[*].observed_at`, `stale` | Alignment and freshness | Display timestamps and stale flag; out-of-tolerance quotes are excluded from synchronized gaps or explicitly marked unaligned. |
| `domain.gap_summary.signed_midpoint_gap`, `absolute_midpoint_gap`, `quote_basis` (optional) | Gap summary | Show direction, size, midpoint basis, and that it is a candidate discrepancy; never imply execution/profitability. |

Recommended view: paired prices over synchronized time, with settlement-equivalence state, bid/ask spread, data gaps, and stale quotes visible.

### Options: threshold probabilities and listed-option comparison

| Schema path | Component / chart input | Display behavior |
|---|---|---|
| `domain.kind` | Options module selector | Must equal `options`; otherwise reject this module. |
| `domain.underlying`, `expiry`, `benchmark_style` | Contract/benchmark context | Show ticker/reference definition, expiry, and exercise style; retain currency, timezone, and settlement convention from the contract/source context. |
| `domain.threshold_curve[*].strike` | Threshold chart x-axis | Label strike/threshold and underlying units. |
| `domain.threshold_curve[*].yes_bid`, `yes_ask` | Digital probability bounds | Show quote sides as bounds; do not collapse to an unlabeled midpoint. |
| `domain.threshold_curve[*].observed_at` | Quote freshness | Show time alignment with the listed-options benchmark. |
| `domain.surface_points[*].log_moneyness`, `maturity_years` | IV surface axes | Show definition, units, and maturity convention. |
| `domain.surface_points[*].pm_bs_equivalent_iv`, `listed_iv` | Comparison surface/table | Label prediction-market-derived Black–Scholes-equivalent IV separately from listed IV; neither is a direct real-world probability. |
| `domain.surface_points[*].quote_uncertainty` | Uncertainty/sensitivity | Show quote-derived interval or sensitivity; if missing, flag uncertainty as unquantified. |
| `domain.reconstruction_assumptions[*]` (optional) | Assumptions panel | List assumptions behind digital-to-call and IV reconstruction; if missing, no reconstructed surface claim. |

Recommended view: threshold curve with bid/ask bounds, plus a separate risk-neutral/Black–Scholes-equivalent surface comparison. Keep quote quality and listed-option liquidity caveats adjacent.

## Exact schema-path coverage index

The tables above group sibling paths for readability. This index makes every leaf path explicit for implementation and review:

| Exact schema path | Mapped component |
|---|---|
| `contract_scope.markets[*].valid_to` | Contract effective range, when supplied. |
| `data_coverage.end` | Sample coverage period end. |
| `findings.metrics[*].value`, `findings.metrics[*].unit`, `findings.metrics[*].definition` | Metric value, unit, and definition in the metric card/table. |
| `sources[*].uri`, `sources[*].role` | Permitted source link and purpose in the provenance panel. |
| `reproducibility.code_path`, `reproducibility.code_commit` | Code reference and pinned revision in reproducibility. |
| `domain.market_probabilities[*].outcome` | Weather outcome/bucket label. |
| `domain.market_probabilities[*].yes_ask`, `domain.market_probabilities[*].midpoint` | Weather quote panel, labeled as ask and descriptive midpoint. |
| `domain.forecast_probabilities[*].valid_time`, `domain.forecast_probabilities[*].outcome`, `domain.forecast_probabilities[*].probability` | Weather comparison row with target time, outcome and external probability. |
| `domain.calibration[*].value`, `domain.calibration[*].sample_count`, `domain.calibration[*].split` | Calibration measure, evaluated sample count and split label. |
| `domain.matched_pairs[*].market_b_id` | Second market identity in the Cross-venue matched-pair table. |
| `domain.quote_observations[*].venue`, `domain.quote_observations[*].ask`, `domain.quote_observations[*].midpoint`, `domain.quote_observations[*].stale` | Cross-venue quote pair with venue, ask, descriptive midpoint, and stale flag. |
| `domain.gap_summary.absolute_midpoint_gap`, `domain.gap_summary.quote_basis` | Absolute candidate-gap size and the quote basis used to calculate it. |
| `domain.expiry`, `domain.benchmark_style` | Options benchmark/contract context. |
| `domain.threshold_curve[*].yes_ask` | Options threshold quote bounds. |
| `domain.surface_points[*].maturity_years`, `domain.surface_points[*].listed_iv` | Options surface maturity axis and listed-options comparison surface. |

## Shared data states and contract gaps

* **Rights-blocked:** suppress source values, chart points, and derived metrics; show “Unavailable while data-use permission is reviewed.” Rights must be resolved by manifest/rights registry before rendering data.
* **Synthetic:** persistent “Synthetic example — not a market observation” notice; never reuse real venue branding or imply measured values.
* **Frozen:** show dataset period and “Frozen analysis — as of [time]”; `updated_at` is not a quote time.
* **Missing required field:** show a data-quality/unavailable panel and report the schema error; do not silently drop the section or substitute zero.
* **Missing optional output:** show “Not evaluated/not supplied” when readers could otherwise infer a negative result; only collapse genuinely supplementary details.
* **Stale:** derive the last-observed time from quote/forecast fields, but suppress “current” until each source has an approved freshness threshold. The schema has timestamps but no universal stale threshold; this remains a content-contract decision.
* **Market rights:** `sources.usage_terms` is descriptive text, not a normalized approval state. A production renderer needs a join to the approved source-rights record referenced by the data manifest.
* **Current schema gap:** there is no common `source_rights_status` or `freshness_threshold` field in the study record. Do not infer approval or freshness from the presence of a URL/timestamp. Resolve in GRO-18/GRO-54 before production data display.

## Review checklist

* Carlos: confirm Weather mapping, quote/time alignment, station and calibration presentation.
* Adele: confirm Cross-venue mapping, retail wording, and navigation/content placement.
* Alay: confirm Options mapping, benchmark/expiry context, and rights/provenance join.
* All three: identify any required pilot field missing from schema or mapping; mark their review status before treating this contract as approved.
