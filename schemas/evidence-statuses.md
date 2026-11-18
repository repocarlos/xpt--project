# Evidence statuses and claim language

This registry gives readers a consistent account of what a study supports. A status is a **claim category**, not a quality grade, an investment recommendation, or a numeric score for comparing unrelated sectors. Do not let a study headline upgrade an individual chart or metric with weaker evidence: label charts and datapoints at their own evidence level where needed.

| Status | Minimum evidence | Suitable wording | Avoid |
|---|---|---|---|
| `descriptive` | Traceable source and contract scope; timestamp/period; observed data summary. | “The market was quoted at…” / “In this sample, we observed…” | “The market is wrong”; unqualified forecast or signal claims. A displayed price convention is not necessarily a real-world probability. |
| `model_estimate` | Named method and inputs; assumptions and material sensitivity/uncertainty. | “The model estimates…” / “Under these assumptions…” | “The true probability is…” or “mispriced” without validation. |
| `validated_forecast` | Forecast timestamp precedes outcome; held-out, preferably chronological and event-grouped resolved sample; proper scoring rule, sample size, uncertainty, and baseline. | “On this held-out sample, forecasts scored…” | “Profitable” or “tradeable edge.” Forecast skill does not establish trading profitability. |
| `validated_finding` | Auditable outcome and provenance; stated evaluation design; dependence, missingness, and uncertainty addressed; held-out reproduction or justified validation and baseline. | “The analysis found… in this sample and design.” | Causal, universal, or profitability claims unless separately supported. |
| `candidate_discrepancy` | Outcomes/payoffs and settlement sources matched; quotes time-aligned; bid/ask/midpoint basis, spread, freshness, and gaps shown. | “A candidate price difference was observed…” | “Mispricing,” “arbitrage,” “free money,” or “executable edge.” A midpoint gap alone is not tradeable. |
| `executable_opportunity` | Defined trade, side, size, and exit/settlement; executable-side prices and size; fees, slippage, funding/hedging costs, and access included; positive net held-out chronological/event-aware results with uncertainty, baseline, capacity, and persistence addressed. | “The specified strategy had positive net results on the stated held-out sample and size assumptions…” | “Guaranteed,” “risk-free,” or “actionable now” from historical evidence alone. Use “arbitrage” only if both legs are equivalent and executable after costs. |

## Applying the labels

- Keep the **observed market price**, **model-derived quantity**, and **validated result** visibly distinct. For example, listed option prices imply a risk-neutral distribution; that is not automatically a real-world event probability.
- A study may use more than one kind of evidence. Give each chart or metric its own precise explanation; the overall status should be conservative and should not overstate any claim emphasized in the summary.
- `candidate_discrepancy` is appropriate for a matched, synchronized price difference under investigation. It does not imply persistence, tradeability, arbitrage, or positive returns.
- `executable_opportunity` is a high bar and needs the specific proposed trade evaluated at realistic executable prices, net of relevant costs, on held-out data. A forecast or model estimate does not qualify on its own.
- The categories do not collapse the weather, cross-venue, and options analyses into a shared performance score. Choose domain-specific charts and metrics.

## Illustrative fixture labels

The repository fixtures demonstrate these distinct meanings, not empirical results:

| Study fixture | Status | Why |
|---|---|---|
| Weather | `descriptive` | One illustrative quote/forecast alignment row, with no calibration evidence. |
| Polymarket–Kalshi | `candidate_discrepancy` | One illustrative synchronized midpoint comparison; no outcome scoring or executable analysis. |
| Options | `model_estimate` | An illustrative model-transformed surface point, not a listed quote or direct real-world probability. |

The six keys must match the `evidence_status` enum in [`study-record.schema.json`](study-record.schema.json). The standard-library fixture checker verifies that match and rejects unknown statuses. These definitions are ready for review; they have **not** yet been approved by the three research leads.
