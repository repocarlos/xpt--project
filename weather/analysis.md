# Kalshi NYC high temperature: model snapshot

**Market:** `KXHIGHNY-26OCT28`, event date October 28, 2026  
**Data pulled:** October 28, 2026 at 05:31 UTC  
**Forecast point:** Open-Meteo grid cell 40.75°N, 74.00°W, 44 m elevation, close to Central Park  
**Settlement:** the selected contract rules name New York City station `CLINYC` and The Weather Company. This is the binding outcome source for this event.

## What the snapshot says

The **60–61°F** contract was quoted at 60¢ bid / 61¢ ask. NOAA's 01Z National Blend of Models bulletin for station KNYC gives a maximum-temperature mean of 61°F and standard deviation of 1°F, with rounded percentiles 59°F (10th), 60°F (25th), 61°F (median), and 62°F (75th and 90th). If those rounded mean/SD values are treated as a Gaussian and the reported high is rounded to the nearest whole degree, the estimated chance of 60–61°F is about **62.5%**. That's only 1.5 percentage points above the 61¢ ask before fees: no useful edge by itself.

The global ensemble member counts put more probability on **62–63°F**: 51–67% across ICON, ECMWF and GEFS, against a 24¢ Kalshi ask. The NBM mean/SD approximation puts that range near 30%, or about 6 percentage points above the ask before fees. This is the more interesting paper-only candidate, but the size of the apparent edge depends on how the NBM's rounded statistical fields map to the contract's whole-degree settlement.

The **59°F or below** Yes contract was 19¢ bid / 20¢ ask (the corresponding No ask was 81¢). None of the three raw ensembles had more than 3.3% of members below 60°F; the NBM Gaussian approximation is 6.7%. This makes No a second screening candidate, with roughly 12 percentage points gross under the NBM approximation. The NBM's 10th percentile is itself reported as 59°F, however, so the cold-tail estimate is especially sensitive to rounding and distribution shape.

**Read:** there is a model disagreement worth tracking, but no validated mispricing yet. The 60–61°F market looks close to the calibrated NBM benchmark. The 62–63°F Yes and ≤59°F No contracts are paper-only candidates; fees, settlement mapping, execution depth and calibration history could erase the apparent gaps.

## Model comparison

The Open-Meteo values below are the frequency of ensemble members whose local-day maximum rounds to the stated whole-degree range. These are raw member frequencies, not calibrated event probabilities.

| Forecast source | Members | Mean daily max | 10th–90th percentile | P(60–61°F) | P(62–63°F) | P(<60°F) |
|---|---:|---:|---:|---:|---:|---:|
| ECMWF IFS 0.25° ensemble | 50 | 61.58°F | 60.6–62.5°F | 38.0% | 62.0% | 0.0% |
| DWD ICON EPS (Open-Meteo seamless) | 39 | 61.36°F | 60.2–62.6°F | 46.2% | 51.3% | 2.6% |
| NCEP GEFS (Open-Meteo seamless) | 30 | 61.80°F | 60.3–63.0°F | 23.3% | 66.7% | 3.3% |
| NOAA NBM v5.0, KNYC 01Z | — | 61°F mean, 1°F SD | q10 59°, q25 60°, q50 61°, q75 62°, q90 62° | ~62.5%* | ~30.2%* | ~6.7%* |
| NWS hourly point forecast | deterministic | 62°F max | — | — | — | — |

\* NBM range probabilities are approximate Gaussian mass reconstructed from the text bulletin's integer-rounded mean/SD and a nearest-degree settlement assumption. The NBM bulletin publishes percentiles and statistical parameters, not these exact contract-bin probabilities. Its 01Z maximum is valid at 00Z Oct 29 (20:00 EDT Oct 28), so it is close to, but not an exact match for, the event's local-day reporting window.

## Contract quotes and rough NBM screen

| Contract | Yes bid / ask | No ask | NBM approximate Yes probability | Initial read |
|---|---:|---:|---:|---|
| 59°F or below | 19¢ / 20¢ | 81¢ | 6.7% | No screen: ~12 pp gross before fees |
| 60–61°F | 60¢ / 61¢ | 40¢ | 62.5% | Near fair at the ask; ~1.5 pp gross |
| 62–63°F | 23¢ / 24¢ | 77¢ | 30.2% | Yes screen: ~6 pp gross before fees |
| 64–65°F | 0¢ / 1¢ | 100¢ | 0.6% | No clear edge |

The contract API's ask sizes and trading volume are in `kalshi_market_rows.csv`; spreads and available size matter when turning these quotes into a tradable price. Kalshi fees vary by market, so the gross gaps above are not net expected value.

## What the model mix tells us

- **NOAA NBM is the best first probability benchmark for U.S. daily temperature ranges in this sample.** Its operational product includes calibrated maximum/minimum temperature guidance and quantiles. This pull used its KNYC station bulletin, not a raw-model member vote.
- **ECMWF, GEFS and ICON provide useful independent ensemble scenarios.** They help reveal forecast spread and potential model disagreement. In this run, all three center daily highs near 61–62°F, but assign very different member frequencies to the 60–61°F bucket. That spread is a reason to inspect calibration, not to average the three frequencies blindly.
- **The NWS hourly forecast is a simple deterministic sanity check.** It peaks at 62°F here, but gives no probability distribution by itself.
- **Settlement alignment still matters.** The market resolves on The Weather Company value for `CLINYC`; the NBM station bulletin uses KNYC and the global models use a nearby grid cell. The market rules also caution that preliminary readings may differ from the final reported value due to rounding/conversion.

## Reproduction and next step

Run `python3 analyze_market.py`. The script fetches the live Kalshi event, three Open-Meteo ensemble forecasts, the NWS hourly point forecast, and the NBM 01Z text bulletin. The snapshot files preserve the exact pull so the calculations can be checked later.

Before using either paper candidate, build a dated backtest: save forecast snapshots at consistent lead times, map the exact settlement station/day/window, compare forecast bins with the final Weather Company outcomes, and measure reliability and Brier/log scores by model and lead. Then subtract the market-specific fee and spread from any apparent edge. A single day cannot establish mispricing.
