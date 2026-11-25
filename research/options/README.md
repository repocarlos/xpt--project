# Synthetic PM threshold curve research

This directory contains a synthetic-only numerical prototype for the options leg. It does not collect or persist live prediction-market or listed-options data. Empirical work remains gated on source rights and an approved, synchronized sample.

## Normalize and align inputs

`align_inputs.py` first checks that any real source is approved separately for collection, raw storage, derivation, team sharing, and dashboard display. If any permission is unresolved it emits a blocker with no rows. Synthetic fixtures can be aligned for method testing. A matched record requires the same underlying, expiry, settlement reference, European call chain, and quote timestamps within the configured tolerance. It preserves the full listed strike chain beside each PM threshold and reports PM-side and option-side quality flags separately. A threshold with no exact listed strike can still be aligned to the same-expiry chain; later surface estimation must account for coverage and interpolation.

```sh
python3 -m research.options.align_inputs \
  research/options/fixtures/alignment_v1.json \
  --output /tmp/aligned-options-inputs.json
```

## Derive a PM digital event-price curve

`derive_digital_curve.py` orients YES/NO quotes to the strict terminal event S(T) > K, preserves exact rule text and quote bounds, cross-checks opposite-side complement intervals, and reports raw monotonicity and coverage. Inclusive/strict mismatches, stale/wide inputs, complement inconsistencies, and unmatched rows remain flagged; nothing is smoothed. This output is still a PM event-price convention, not an option risk-neutral probability.

```sh
python3 -m research.options.derive_digital_curve \
  research/options/artifacts/aligned-synthetic-fixture.json \
  --output /tmp/synthetic-digital-curve.json
```

## Reconstructing call-equivalent values

A terminal digital claim with strike x and unit payout has price p(x). Where the curve can be interpreted as consistently discounted state-claim prices, the call identity is:

C(K) = integral from K to infinity of p(x) dx.

The implementation defaults to integrating piecewise-linear segments with the trapezoidal rule. It also exposes left-step and right-step integration as sensitivity scenarios. It carries bid and ask curves separately, so the output is a lower/upper range. It does not fix non-monotone inputs or imply a risk-neutral measure from prediction-market prices.

Input JSON uses `schema_version: options.digital_curve.v1`. Quotes are premiums for the specified cash payout:

- `price_basis: present_value_per_unit_payout`: quote prices already represent present-value prices; no extra discount factor is accepted.
- `price_basis: undiscounted_event_price`: values remain event-price integrals unless an explicit `discount_factor` is supplied, in which case that factor is applied once.
- `tail` is optional. Without it, only the observed-range subtotal is returned and the full call tail remains unknown. A declared cap and scenarios give sensitivities by linearly moving from the last observed digital value to the declared fraction at the cap, then setting the digital value to zero beyond it. This is a sensitivity convention, not an empirical tail estimate.

Every output is labeled synthetic and not a listed option quote. It includes the observed coverage, excluded quote IDs, monotonicity flags, quote range, price convention, and tail assumptions. Points outside observed coverage return no value. A curve is not marked eligible for model use if it is non-monotone, contains excluded quotes, lacks an explicit tail, or lacks tail scenarios.

Run the fixture:

```sh
python3 research/options/reconstruct_calls.py \
  research/options/fixtures/digital_curve_v1.json \
  --output /tmp/options-calls.json
python3 -m unittest discover -s research/options/tests -v
```

## Black–Scholes-equivalent IV comparison

`compare_iv_surfaces.py` inverts only European call present values under a continuous-rate/dividend Black–Scholes convention. It carries PM synthetic call bounds and listed bid/ask prices to IV intervals, then joins only exact underlying/expiry/snapshot/strike/style/type keys with matching spot, time, rate, and dividend inputs. It computes log-moneyness as ln(K/F) using F = S exp((r-q)T). Unmatched or invalid cells are retained with reasons.

The comparison values and heatmap are synthetic fixtures. PM-derived IV is explicitly labeled as a BS-equivalent transformation, while the listed reference has its own label; the displayed ΔIV is a candidate dislocation only. There is no data ingestion, empirical claim, or trade signal in this prototype.

```sh
python3 research/options/compare_iv_surfaces.py \
  research/options/fixtures/surface_comparison_v1.json \
  --output /tmp/options-iv-comparison.json \
  --plot /tmp/options-iv-comparison.png
```

Run the synthetic assumption stress grid and write the JSON results, Markdown handoff, and optional baseline chart:

```sh
python3 -m research.options.stress_test_surface \
  research/options/fixtures/sensitivity_v1.json \
  --output /tmp/options-stress.json \
  --report /tmp/options-handoff.md \
  --plot /tmp/options-stress.png
```

The committed generated example is in `research/options/artifacts/`; it is synthetic, not observed market data.
