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
