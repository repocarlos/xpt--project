# Options study feasibility notes

## GRO-43 — threshold-market ladder selection

**Decision: no-go for a current pilot ladder from the evidence currently on hand.** The only detailed PM observations in the brainstorm are an expired 2026-10-30 snapshot with very wide books. They establish market shape, not current availability or usable surface quality. A new active candidate and a permitted source sample are required to reopen selection.

| Candidate | Event shape and expiry | Strike/bin coverage and resolution | Quote evidence | Gaps / disposition |
|---|---|---|---|---|
| [Polymarket MSFT close-above, Oct. 30, 2026](https://polymarket.com/event/msft-close-above-on-october-30-2026) | YES if MSFT terminal close is strictly above K; expiry at Oct. 30 4 p.m. ET | K = $520, $530, $540, $550, $560. Recorded rule: final regular-session one-minute Pyth close; equality resolves No. | Snapshot around Oct. 29 19:00 UTC: roughly $0.01 bid / $0.99 ask at $520–$550 and $0.001 / $0.999 at $560; little recent volume. | Expired; very wide; precise token/contract IDs, synchronized option chain, and same-underlying European benchmark are not in the record. Discovery only. |
| [Polymarket MSFT end-of-month ladder](https://polymarket.com/event/msft-above-in-october-2026) | End-of-month close-above, Oct. 30, 2026 | Recorded strikes include $435, $450, $465, $480, $495, $510, $525, $540, with additional strikes indicated. | Many books recorded 93–99 cents wide. | Expired; full rules/IDs, usable depth, and matched listed-option terms not established. |
| Polymarket AAPL / NVDA / TSLA close-above ladders | Daily close-above examples for Oct. 30, 2026 | Approximate strikes in the notes: AAPL $340–$360, NVDA $205–$225, TSLA $380–$420. | Individual synchronized bid/ask and depth evidence not recorded. | Discovery only; exact rule/source/IDs and listed benchmark match unverified. |
| [Kalshi $INX Oct. 30, 2026 event](https://external-api.kalshi.com/trade-api/v2/events/KXINX-26OCT30H1600?with_nested_markets=true) | S&P 500 index 4 p.m. EDT close, split into mutually exclusive range bins. | 30 bins, mostly $25-wide; 18/30 had positive volume. Example ticker `KXINX-26OCT30H1600-B7687`: 7,675–7,699.9999. | Example Yes bid 12¢ / ask 17¢, last 15¢, volume/OI 210. | Coarse bins can approximate a survival curve by summation, but this is an index event and does not match the MSFT ladder; expired. Source-use approval remains a separate gate. |

### Reopen criteria

1. Identify an active terminal-close ladder and record each venue contract/token ID, threshold, rule URL, reference price source, timestamp/timezone, and resolution convention.
2. Confirm an options benchmark on the same underlying and expiry/reference time. For a single-name U.S. equity, account for American exercise; do not use a European call-slope formula directly unless a European-style contract is actually available and matched.
3. Obtain a source-approved coverage sample with synchronized two-sided quotes, strike coverage, and sizes. Keep source permission separate from endpoint accessibility.

Until those criteria pass, downstream synchronized inputs and PM digital probabilities should be treated as blocked for empirical data. No new market data was collected for this note.

## GRO-44 — options benchmark mapping

**Decision: no matched listed-options benchmark can be approved from the current record; do not process option quotes yet.**

| PM candidate | PM terminal event/reference | Listed benchmark status | Match decision |
|---|---|---|---|
| MSFT close-above ladder | MSFT strictly above K at Oct. 30, 2026 4 p.m. ET; recorded reference is the final regular-session one-minute Pyth close; equality is No. | No dated options chain or exact series is in the record. U.S. single-name options are American-style; a European call-slope benchmark would be invalid without an actually matched European instrument. An American-adjusted comparator would require same-time quotes plus dividends, rates, early-exercise treatment, and a bounded Pyth/option reference basis. | Unavailable; underlying appears nominally the same, but exact settlement and benchmark inputs are unverified. |
| Kalshi $INX range bins | S&P 500 index at the Oct. 30, 2026 4 p.m. EDT close, represented by $25-wide outcome bins. | A European index-options series could be a candidate only if its underlying, PM/AM settlement convention, expiry, observation time, and reference level match. No such series or chain is documented here. | Unavailable; do not substitute SPX options without series-level settlement matching. |
| AAPL / NVDA / TSLA examples | Approximate Oct. 30 close-above strikes; exact resolution metadata was not recorded. | No listed chain/series, timestamps, or option-style data recorded. | Unavailable. |

**Reopen rule:** select a current ladder first; then record the exact listed series and quote timestamp, underlying/reference, expiry, settlement style, and any basis. The options research owner must approve that mapping before quote processing. No payoff or settlement approximation is currently bounded, so none is recommended as a comparator.

## GRO-45 — quote-quality audit from recorded discovery evidence

This is a limited audit of the old discovery snapshot, not a current coverage study.

| Candidate / expiry | PM coverage and quote evidence | Freshness / depth | Listed options evidence | Screen result |
|---|---|---|---|---|
| MSFT Oct. 30, 2026 | 5 thresholds recorded. At $520–$550, approximate Yes bid/ask was $0.01/$0.99 (98¢ spread); at $560, $0.001/$0.999 (99.8¢ spread). | Snapshot around Oct. 29 19:00 UTC; contracts expired Oct. 30. Little recent volume was reported; per-strike sizes and depth absent. | 0 synchronized option quotes in the record. | Fail: expired, extremely wide, no benchmark quotes. |
| MSFT month-end Oct. 30, 2026 | At least 8 strikes indicated; many quoted books were 93–99¢ wide. | Expired; per-strike timestamps/sizes and depth absent. | 0 synchronized option quotes in the record. | Fail. |
| AAPL / NVDA / TSLA Oct. 30, 2026 | Approximate strike ranges only; no two-sided quote rows. | Expired; quote timestamps and depth absent. | 0 synchronized option quotes in the record. | Fail / unverified. |
| Kalshi $INX Oct. 30, 2026 | 30 bins, mostly $25 wide; 18 had positive volume. One example bin spread was 5¢ (12¢/17¢). | Snapshot evidence only for one example; no complete synchronized depth or per-bin sizes in the record. Expired. | 0 matched European index-option quote rows in the record. | Fail for current pilot; coarse, incomplete and unmatched. |

At the current review date (2026-11-19), the PM observations are about 21 days old and the contracts are expired. **Current usable strikes: 0; synchronized PM/options quote pairs: 0; listed quote freshness/depth: not observed.** This does not mean the venues have no data; it means the task's evidence file contains no approved, aligned sample.

Provisional screen for a future sample: one expiry; at least five distinct terminal thresholds spanning the forward; at least three central thresholds with two-sided PM books and spreads no wider than $0.10; PM and listed-option quotes no more than 60 seconds apart; listed quotes must be two-sided, uncrossed, and include size. These are pilot screening cutoffs only; tune them to intended order size before tradeability claims. Under this screen the existing ladders fail. A binary-derived Black–Scholes-equivalent IV remains a transformed estimate, not a listed IV quote.

**GRO-45 result: no-go pending a current, approved sample and an exact benchmark.** No live data was collected or persisted.
