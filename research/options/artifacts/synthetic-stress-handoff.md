# Options surface stress test — synthetic handoff

**Evidence state:** synthetic fixture only. No observed PM prices, actual listed-option quotes, or resolved outcomes were used.

**Recommendation:** stop empirical publication and trading claims until source use is approved and exact matched historical inputs are available. Continue only as a method prototype.

## What the pipeline represents

- Digital thresholds: synthetic PM-like bid/ask prices.
- Transformed estimates: integrated synthetic call-equivalent ranges and European Black–Scholes-equivalent IV ranges.
- Listed benchmark: synthetic European call quotes generated for testing, not exchange observations.
- Validation: arithmetic and handling tests passed; no forecast calibration or executable trading validation.

## Sensitivity coverage

- Scenario count: 144.
- Axes: quote side (quoted interval, bid, mid, ask); interpolation (piecewise linear, left step, right step); declared tail scenarios; discount factor applied vs omitted.
- Missing or invalid IV cells stay visible with a reason; no missing quotes are filled.

| Expiry | Scenarios | ΔIV midpoint range (percentage points) | Valid IV cells | Invalid/unmatched cells |
|---|---:|---:|---:|---:|
| 2027-03-19 | 72 | -17.808 to 42.431 | 124 | 164 |
| 2027-06-18 | 72 | -8.642 to 26.021 | 132 | 156 |

## Synthetic contract terms

- 2027-03-19: SYNTH terminal event > K; snapshot 2026-11-25T16:00:00Z; synthetic horizon 0.25 years; payout 1.0; threshold coverage 60–140; requested call strikes 85, 95, 105, 115.
  Observed venue/source and settlement references: unavailable; all thresholds are synthetic.
- 2027-06-18: SYNTH terminal event > K; snapshot 2026-11-25T16:00:00Z; synthetic horizon 0.5 years; payout 1.0; threshold coverage 60–140; requested call strikes 85, 95, 105, 115.
  Observed venue/source and settlement references: unavailable; all thresholds are synthetic.

The numeric ranges above are sensitivities of synthetic examples only; they are not current market gaps.

## Reproduction

    python3 -m research.options.stress_test_surface research/options/fixtures/sensitivity_v1.json --output research/options/artifacts/synthetic-stress-results.json --report research/options/artifacts/synthetic-stress-handoff.md --plot research/options/artifacts/synthetic-stress-surface.png

## Gates before an empirical rerun

1. Confirm source permission separately for collection, raw storage, derivation, team sharing, and display.
2. Match terminal event, threshold orientation, underlying reference, expiry, settlement time/source, and European option style.
3. Obtain synchronized two-sided PM and listed-option quotes with sizes and documented quote freshness.
4. Approve strike coverage, timestamp tolerance, interpolation, tail, rates, dividends, and discounting conventions.
5. Keep any later tradability claim behind executable costs, hedge/funding assumptions, capacity, and held-out evaluation.

An IV difference by itself is a candidate dislocation only, not proof of mispricing or an edge.
