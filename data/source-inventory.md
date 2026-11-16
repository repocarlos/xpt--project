# Prediction-market analytics source inventory

**Reviewed:** 2026-11-16  
**Status:** Candidate sources and documented terms are inventoried; exact pilot coverage and each lead's confirmation are pending. This is not approval to collect or redistribute data.

## Key finding: resolve data rights before capture

Public API access is not the same as permission to build a shared archive or show raw/derived market data on a retail-facing dashboard. The currently published [Kalshi Developer Agreement](https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf) limits API use to facilitating a member's own trading and prohibits storing/caching data except for that use, as well as sharing data without prior written authorization. The [Polymarket Terms of Use](https://polymarket.com/tos) restrict some data use by capital-market clients and market-data distributors absent a written agreement. Cboe's [DataShop policies](https://datashop.cboe.com/data-policies) point to product-specific licenses; external redistribution needs additional rights. The intended audience/use may trigger different terms, so the project must get written clarification or select an expressly licensed source **before** collecting, caching, storing, uploading, or displaying venue/vendor data.

The source inventory's proposed 2026-11-17 venue capture date is conditional on that rights gate. No collector is started by this task. The existing repository already contains a prior weather pilot snapshot; the source-rights basis for retaining or publishing it should be reviewed before it is reused or expanded. This task adds no raw market data or credentials.

## Summary matrix

| Source ID | Leg | Owner(s) | Source | Status | Capture timing |
|---|---|---|---|---|---|
| `kalshi-market-data` | Weather, cross-venue | Carlos López-Ibor Romero; Adele Palsson | Kalshi APIs | Permission required | 2026-11-17 only if rights are confirmed |
| `polymarket-market-data` | Cross-venue, options | Adele Palsson; Alay Patel | Gamma, CLOB, Data API v2 | Permission required | 2026-11-17 only if rights are confirmed |
| `nws-point-forecast` | Weather | Carlos López-Ibor Romero | NWS API | Owner confirmation pending | 2026-11-16 if retained as a benchmark |
| `open-meteo-ensemble` | Weather | Carlos López-Ibor Romero | Open-Meteo Ensemble API | Owner confirmation pending | 2026-11-16 after use/license check |
| `noaa-nbm-forecast` | Weather | Carlos López-Ibor Romero | NOAA NBM text products/archive | Owner confirmation pending | 2026-11-16 after source/use check |
| `ncei-weather-observations` | Weather | Carlos López-Ibor Romero | NCEI CDO / GHCN-Daily | Owner confirmation pending | Historical backfill after station selection |
| `weather-company-settlement` | Weather | Carlos López-Ibor Romero | The Weather Company per contract rules | Owner confirmation pending | Before the next scored event, after access/terms check |
| `cboe-listed-options` | Options | Alay Patel | Cboe DataShop Option EOD Summary (candidate) | Permission required | After product/license approval |

## Weather leg — Carlos

| Source / role | Identifiers and documented history | Cadence, retention, usage terms | Material gaps and next check |
|---|---|---|---|
| **Kalshi market data** — market rules, quotes, candles, trades/books | `KXHIGHNY` series; market/event ticker and exact rule version. Kalshi separates live and historical endpoints; old market, candle, and trade data may move to historical APIs. Exact start date and per-market depth coverage are unverified. | REST or WebSocket. API limits can change. The Developer Agreement restricts collection/storage except to facilitate the member's own trading and sharing without prior written authorization. | Obtain written project-use rights or a licensed alternative before more capture. Confirm quote history, settlement source, fee schedule, and rule versions for chosen markets. |
| **NWS point/hourly forecast** — deterministic benchmark | `/points/{lat},{lon}` gives grid metadata and the hourly endpoint. Forecast horizon is the next seven days; past periods are removed from live responses. | Current API data is intended as open/free for any purpose with reasonable, unpublished rate limits; identify the app with the required User-Agent. Capture each forecast vintage with issued and valid times if this remains in scope. | Not a vintage archive. The point grid can change; forecast grid and market's settlement station/local day must be aligned. |
| **Open-Meteo ensemble** — existing pilot's NCEP GEFS, ECMWF IFS, and DWD ICON members | Existing code requests `gfs_seamless`, `ecmwf_ifs025`, and `icon_seamless` near Central Park. Ensemble API docs describe 3 days of historical member data and a normal 7-day forecast (up to 36 days for supported models); Previous Runs API offers model-specific fixed lead-time archives, whose exact coverage needs a pilot check. | Model run cadence varies; preserve model/version, issue time, member, lead, valid time, and grid. Free API is non-commercial only and CC BY 4.0 attribution applies; assess whether the intended dashboard is commercial or needs a paid license. | Three days of history is not enough for a long OOS backtest. Verify licensed use, model-specific historical coverage, grid alignment, and attribution before extending the existing snapshots. |
| **NOAA NBM bulletin/archive** — probabilistic benchmark | Existing pilot uses the 01Z NBP text bulletin for `KNYC`, file pattern `blend.YYYYMMDD/HH/text/blend_nbptx.tHHz`. NOAA's NBM archive page points to archived operational daily data; exact start/retention of the selected text bulletin remains unverified. | NBM runs hourly; the existing example used a 01Z issue. Save vintage, station, valid period, units, and bulletin fields. Product-specific reuse terms were not established in this review. | KNYC is not the contract's named `CLINYC` / The Weather Company outcome. Rounded NBM parameters do not directly give exact contract-bin probabilities. Confirm archive sample and use terms. |
| **NCEI CDO / GHCN-Daily** — independent historical observation check | Select `GHCND` station and data type (for example, daily max temperature); record station history from HOMR. Long station histories exist but coverage varies by station and element; records update daily where possible. | CDO access is free; API requires token and is limited to 5 requests/sec and 10,000/day. Some non-U.S. observations may carry WMO commercial re-export restrictions; confirm the exact dataset terms. | This is not the binding Weather Company value named in the current contract. Confirm whether it is only a secondary check, exact station/day completeness, quality flags, and finalization. |
| **The Weather Company** — binding outcome per current contract rules | Existing weather analysis says the NYC contract resolves on the Weather Company value for station `CLINYC`. No authorized historical outcome feed, coverage period, or project access terms are in the repo. | Publication/revision schedule and storage/display rights unknown. Preserve exact contract rule text and version. | Obtain the source data and terms for the exact event; do not substitute NCEI/NWS station data without explicitly changing the research question. |

## Polymarket–Kalshi leg — Adele

Use exact condition/market IDs, outcome orientation, settlement rules, resolution sources, and synchronized timestamps. Kalshi requires an authorization/licensed-source gate as above. Polymarket's current Data API v2 docs show price history with resolution-dependent buckets and a 15-day maximum explicit range; current docs describe coarse full-history buckets and minimum fine-history retention floors of at least 7 days at 1-minute, 60 days at 5-minute, and 90 days at 30-minute. Endpoint/version details differ, so record which endpoint was queried and its returned `resolution_seconds`; confirm exact pilot coverage with a permitted sample. Price history is not historical executable depth.

Polymarket Terms restrict some data use by capital-market clients and market-data distributors without a written agreement. Because this product is intended to explain prediction markets to retail investors, confirm the project's classification and rights for its intended distribution before archiving or displaying market data. A midpoint gap remains descriptive until quote freshness, executable side/size, fees, and matched payoff rules are established.

## Options leg — Alay

Cboe's [Option EOD Summary](https://datashop.cboe.com/option-eod-summary) is a candidate daily product: its page says historical availability begins January 2012 and describes NBBO bid/ask and size for option series, but exact symbol/date availability and product fields still need a sample. EOD quotes may not satisfy the synchronized intraday comparison. No provider, symbol set, expiry, subscription, or license is selected.

Cboe DataShop has product-specific contracts; external distribution requires additional licensing, and any SIP/OPRA rights must be separately checked. Before purchase or ingestion, confirm internal research/storage and retail-dashboard display rights, costs, availability for the exact underlying/expiry/strike ladder, and whether the product supports the desired quote time. The prediction-market contract's threshold, expiry, underlying reference, and settlement must match the options benchmark.

## Capture and storage decisions

1. **Start forecast-vintage preservation now where permitted.** Proposed date: 2026-11-16. NWS forecast responses roll forward and the current endpoint removes past periods; Open-Meteo has only limited member-history windows; NBM operational products may be transient. Each lead must confirm the source/model and any license before collection.
2. **Do not start direct Kalshi or Polymarket archive capture yet.** Proposed date: 2026-11-17 only if written permission or an approved licensed archive covers the research use, storage, and intended dashboard audience. Otherwise, keep the source blocked and identify a licensed alternative.
3. **Do not buy or ingest options data yet.** First obtain a product sample/coverage report and written terms for internal research and external display; then check full-chain/expiry coverage.
4. Keep code, schemas, and this inventory in Git. Do not place raw data in Git or XPT Files until source terms and the approved versioned storage/access policy are recorded. Version contract rules and manifests separately from data.
5. Start with metadata, price history, and trades only after the rights gate; defer full-depth books until the execution gate justifies their cost and retention burden.

## Owner review needed

* **Carlos:** confirm the weather market rule/settlement source; whether NWS, Open-Meteo, NBM, and NCEI remain in the pilot; exact station, grid, issue time, lead time, and allowed data use.
* **Adele:** confirm the exact cross-venue pairs, matching/rule sources, endpoint versions, and rights for the research archive/dashboard.
* **Alay:** confirm the option source/product, quote granularity, budget, internal and external use license, and storage decision.

All three confirmations are pending. These sources and proposed dates are an inventory for review, not authorization to collect data.

## Primary references reviewed 2026-11-16

* Kalshi: [Historical Data docs](https://docs.kalshi.com/getting_started/historical_data); [Developer Agreement](https://kalshi-public-docs.s3.amazonaws.com/Kalshi-Developer-Agreement.pdf); [Data Terms](https://kalshi-public-docs.s3.amazonaws.com/kalshi-data-terms-of-service.pdf).
* Polymarket: [Prices and Order Books](https://docs.polymarket.com/market-data/prices-order-books); [Real-Time Data](https://docs.polymarket.com/market-data/realtime-data); [Terms of Use](https://polymarket.com/tos).
* Weather: [NWS API](https://www.weather.gov/documentation/services-web-api); [NOWData FAQ](https://www.weather.gov/climateservices/nowdatafaq); [Open-Meteo Ensemble](https://open-meteo.com/en/docs/ensemble-api), [Previous Runs](https://open-meteo.com/en/docs/previous-runs-api), [Terms](https://open-meteo.com/en/terms), [License](https://open-meteo.com/en/licence); [NOAA NBM Text Archives](https://vlab.noaa.gov/web/mdl/nbm-text-archives); [NCEI CDO API](https://www.ncei.noaa.gov/cdo-web/webservices/v2), [CDO FAQ](https://www.ncei.noaa.gov/cdo-web/faq), and [GHCN-Daily documentation](https://www.ncei.noaa.gov/pub/data/cdo/documentation/GHCND_documentation.pdf).
* Options: [Cboe Option EOD Summary](https://datashop.cboe.com/option-eod-summary); [Cboe DataShop policies](https://datashop.cboe.com/data-policies).
