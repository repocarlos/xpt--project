# Weather sector study handoff

**Status:** Pending source approval and empirical validation. This template contains no market findings.

## Question and scope

- Research question: pending
- Study period and decision-time convention: pending
- Selected families/cohorts and rationale: pending
- Deferred families and evidence needed to add them: pending

## Settlement and data coverage

For each family, document contract rule/version, authoritative resolution, mapping review, source-use status, date coverage, event denominator, quote tier, outcome coverage, forecast-vintage coverage, and missingness. Keep backfill and prospective capture separate.

## Methods and evidence classes

Label each row as one of: `observed_price`, `model_estimate`, `held_out_result`, or `candidate_gap`. Also label claim status as `pending`, `synthetic`, `observed`, `validated`, or `insufficient`. A candidate gap is never a proven opportunity.

## Results and uncertainty

- Market quote context: Yes/No bid/ask, midpoint, spread, quote age/type, and missing depth.
- Forecast evidence: model/run, issue time, valid window, spatial mapping, variable/unit, lead, and alignment coverage.
- Calibration: chronological event holdout dates, event and observation counts, Brier/log loss, reliability intervals, and sparse-family warnings.
- Paper screen: policy, fees/fill assumptions, candidate and eligible event counts, hypothetical outcome method, and sensitivity.
- Costs, retention, estimated/measured volume, storage, exports and reproducibility references.
- Limitations and unresolved source/settlement/coverage risks.

## Recommendation

Choose `proceed`, `revise`, or `stop` and give evidence, owners, and next decision date. Keep Weather metrics family-specific; do not force them into a cross-sector score.

## Dashboard handoff checklist

- [ ] Approved source-use and retention evidence is linked.
- [ ] Settlement mapping and independent review are complete per family.
- [ ] Quotes are distinguished from midpoints/candles and forecasts pass issue-time alignment.
- [ ] Validation is chronological and event-level; uncertainty and sparse samples are shown.
- [ ] Candidate gaps are not presented as proven opportunities.
- [ ] Static history and prospective capture tiers are documented separately.
- [ ] Deferred families list the evidence needed to add them.
- [ ] Reproducible sources, transformations, manifests and exports are linked.
