# Weather market extraction

This folder contains a reproducible, single-market snapshot for the Kalshi New York City daily high temperature event on **October 28, 2026**.

Start with [`analysis.md`](analysis.md) for the findings. Run `python3 analyze_market.py` to fetch a new live snapshot; the market prices and forecasts will change, and the NBM archive only retains recent operational text files. The checked-in JSON/CSV/TXT files preserve the snapshot used in the analysis.

## Sources

- [Kalshi event page](https://kalshi.com/markets/kxhighny/highest-temperature-in-nyc/kxhighny-26oct28) and public [Kalshi markets API](https://api.elections.kalshi.com/trade-api/v2/markets?series_ticker=KXHIGHNY&status=open&limit=1000)
- [Open-Meteo Ensemble API docs](https://open-meteo.com/en/docs/ensemble-api)
- [NOAA NBM overview](https://vlab.noaa.gov/web/mdl/nbm), [NBM text product docs](https://vlab.noaa.gov/web/mdl/nbm-text-products), and [the archived 01Z KNYC NBP bulletin](https://noaa-nbm-grib2-pds.s3.amazonaws.com/blend.20261028/01/text/blend_nbptx.t01z)
- [NWS API documentation](https://www.weather.gov/documentation/services-web-api)
- [Kalshi fees](https://help.kalshi.com/en/articles/13823805-fees)

## Files

- `analysis.md` — market/model comparison and caveats
- `analyze_market.py` — extraction and probability calculation script
- `kalshi_market_snapshot.json`, `kalshi_market_rows.csv` — event rules and quote snapshot
- `open_meteo_ensemble_snapshot.json`, `ensemble_member_daily_maxima.csv`, `ensemble_model_summary.csv` — ensemble data and daily maxima
- `market_model_comparison.csv` — one row per contract range: bid/ask/mid implied odds, each global model, equal-weight model average, separate NBM estimate, and gross edges before fees
- `model_market_probabilities.csv` — raw member frequencies by contract range and quote
- `nbm_knyc_nbp_bulletin.txt`, `nbm_knyc_nbp_summary.json`, `nbm_market_probability_approx.csv` — NOAA bulletin and Gaussian approximation
- `nws_hourly_snapshot.json`, `nws_target_day_periods.json` — deterministic NWS hourly forecast
