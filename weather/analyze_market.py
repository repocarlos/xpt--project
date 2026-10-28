#!/usr/bin/env python3
"""Fetch one Kalshi weather market and compare point ensemble daily highs.

The default snapshot targets the active KXHIGHNY Oct 28, 2026 event. Re-running
will fetch a new, non-identical snapshot from live public endpoints.
"""
from __future__ import annotations

import csv
import json
import math
import re
from datetime import datetime, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests

ROOT = Path(__file__).resolve().parent
SERIES = "KXHIGHNY"
TARGET_DATE = "2026-10-28"
LAT, LON = 40.7789, -73.9692  # Central Park / CLINYC vicinity
TZ = "America/New_York"
USER_AGENT = "XPT Agent support@xpt.ai"
MODELS = "gfs_seamless,ecmwf_ifs025,icon_seamless"
MODEL_NAMES = {
    "ncep_gefs_seamless": "NCEP GEFS (Open-Meteo seamless)",
    "ecmwf_ifs025_ensemble": "ECMWF IFS 0.25° ensemble",
    "icon_seamless_eps": "DWD ICON EPS (Open-Meteo seamless)",
}


def get_json(url: str, *, params=None, headers=None):
    response = requests.get(url, params=params, headers=headers, timeout=60)
    response.raise_for_status()
    return response.json(), response.url


def save_json(path: Path, obj):
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def market_data():
    data, url = get_json(
        "https://api.elections.kalshi.com/trade-api/v2/markets",
        params={"series_ticker": SERIES, "status": "open", "limit": 1000},
    )
    # Use the series event date encoded in the ticker, e.g. 26OCT28.
    day_code = datetime.strptime(TARGET_DATE, "%Y-%m-%d").strftime("%y%b%d").upper()
    matching = [m for m in data.get("markets", []) if f"-{day_code}-" in m["ticker"]]
    if not matching:
        raise RuntimeError(f"No open markets found for {SERIES} {TARGET_DATE}")
    snap = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "url": url,
            "event_date_local": TARGET_DATE, "series_ticker": SERIES,
            "markets": matching}
    save_json(ROOT / "kalshi_market_snapshot.json", snap)
    return matching, snap


def ensemble_data():
    data, url = get_json(
        "https://ensemble-api.open-meteo.com/v1/ensemble",
        params={"latitude": LAT, "longitude": LON, "hourly": "temperature_2m",
                "models": MODELS, "temperature_unit": "fahrenheit",
                "timezone": TZ, "forecast_days": 3},
    )
    snap = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(), "url": url,
            "request": {"latitude": LAT, "longitude": LON, "models": MODELS,
                        "temperature_unit": "fahrenheit", "timezone": TZ,
                        "forecast_days": 3}, "response": data}
    save_json(ROOT / "open_meteo_ensemble_snapshot.json", snap)
    return data


def nws_data():
    headers = {"User-Agent": USER_AGENT, "Accept": "application/geo+json"}
    point, point_url = get_json(f"https://api.weather.gov/points/{LAT},{LON}", headers=headers)
    hourly_url = point["properties"]["forecastHourly"]
    forecast, forecast_url = get_json(hourly_url, headers=headers)
    snap = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(),
            "point_url": point_url, "forecast_url": forecast_url,
            "grid": {k: point["properties"].get(k) for k in
                     ("gridId", "gridX", "gridY", "forecastZone", "timeZone")},
            "response": forecast}
    save_json(ROOT / "nws_hourly_snapshot.json", snap)
    return forecast


def nbm_data():
    # The public NBM station bulletin archive exposes a compact probabilistic
    # bulletin for the KNYC Central Park station. The 01Z cycle is the latest
    # completed cycle at the time of this sample.
    datecode = TARGET_DATE.replace("-", "")
    url = ("https://noaa-nbm-grib2-pds.s3.amazonaws.com/"
           f"blend.{datecode}/01/text/blend_nbptx.t01z")
    response = requests.get(url, timeout=120)
    response.raise_for_status()
    lines = response.text.splitlines()
    start = next((i for i, line in enumerate(lines)
                  if re.match(r"\s*KNYC\s+NBM V5\.0 NBP GUIDANCE", line)), None)
    if start is None:
        raise RuntimeError("KNYC bulletin was absent from the NBM NBP text file")
    end = next((i for i in range(start + 1, len(lines)) if not lines[i].strip()), len(lines))
    bulletin = lines[start:end]
    (ROOT / "nbm_knyc_nbp_bulletin.txt").write_text("\n".join(bulletin) + "\n", encoding="utf-8")
    fields = {}
    for line in bulletin:
        parts = line.split()
        if parts and parts[0] in {"TXNMN", "TXNSD", "TXNP1", "TXNP2", "TXNP5", "TXNP7", "TXNP9"}:
            values = re.findall(r"-?\d+", line.split(maxsplit=1)[1])
            if values:
                fields[parts[0]] = int(values[0])
    needed = {"TXNMN", "TXNSD", "TXNP1", "TXNP2", "TXNP5", "TXNP7", "TXNP9"}
    if not needed.issubset(fields):
        raise RuntimeError(f"Incomplete KNYC NBM bulletin fields: {fields}")
    snapshot = {"fetched_at_utc": datetime.now(timezone.utc).isoformat(),
                "url": url, "station": "KNYC", "cycle_utc": "2026-10-28 01:00",
                "target_valid_time_utc": "2026-10-29 00:00",
                "forecast_window_note": "NBM TXNMN/TXNSD are 18-hour maximum/minimum guidance; this max is valid at 00Z.",
                "fields_first_valid_column_f": fields}
    save_json(ROOT / "nbm_knyc_nbp_summary.json", snapshot)
    return snapshot


def rounded_f(value):
    # Contract ranges use whole Fahrenheit degrees. Use conventional half-up rounding.
    return math.floor(value + 0.5)


def analyze_ensembles(data):
    hourly = data["hourly"]
    target_idxs = [i for i, t in enumerate(hourly["time"]) if t[:10] == TARGET_DATE]
    if not target_idxs:
        raise RuntimeError(f"No hourly forecast values for {TARGET_DATE}")
    member_keys = [k for k in hourly if k.startswith("temperature_2m_member")]
    groups = {}
    for key in member_keys:
        # Member suffixes differ by model; normalize by matching the documented
        # model identifiers present in the Open-Meteo response key.
        full_key = key
        model = next((name for name in MODEL_NAMES if full_key.endswith(name)), None)
        if model is None:
            raise RuntimeError(f"Unrecognized ensemble member key: {key}")
        groups.setdefault(model, []).append(key)
    member_rows = []
    summaries = []
    for model, keys in sorted(groups.items()):
        maxima = []
        for key in keys:
            values = [hourly[key][i] for i in target_idxs if hourly[key][i] is not None]
            if values:
                maximum = max(values)
                maxima.append(maximum)
                member_rows.append({"model": MODEL_NAMES[model], "model_key": model,
                                    "member": key, "daily_max_f": maximum,
                                    "rounded_daily_max_f": rounded_f(maximum),
                                    "target_60_61": int(60 <= rounded_f(maximum) <= 61)})
        max_values = sorted(maxima)
        target_n = sum(60 <= rounded_f(v) <= 61 for v in maxima)
        if max_values:
            summaries.append({"model": MODEL_NAMES[model], "model_key": model,
                              "n_members": len(max_values),
                              "mean_member_daily_max_f": sum(max_values) / len(max_values),
                              "median_member_daily_max_f": max_values[len(max_values)//2],
                              "p10_daily_max_f": max_values[max(0, math.ceil(.10*len(max_values))-1)],
                              "p90_daily_max_f": max_values[max(0, math.ceil(.90*len(max_values))-1)],
                              "p_60_to_61_rounded": target_n / len(max_values),
                              "n_60_to_61_rounded": target_n})
    with (ROOT / "ensemble_member_daily_maxima.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(member_rows[0]))
        writer.writeheader(); writer.writerows(member_rows)
    with (ROOT / "ensemble_model_summary.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(summaries[0]))
        writer.writeheader(); writer.writerows(summaries)
    return summaries


def model_market_probabilities(ensemble, markets):
    hourly = ensemble["hourly"]
    idxs = [i for i, t in enumerate(hourly["time"]) if t[:10] == TARGET_DATE]
    member_keys = [k for k in hourly if k.startswith("temperature_2m_member")]
    by_model = {}
    for key in member_keys:
        model_key = next((name for name in MODEL_NAMES if key.endswith(name)), None)
        if model_key is None:
            continue
        vals = [hourly[key][i] for i in idxs if hourly[key][i] is not None]
        if not vals:
            continue
        by_model.setdefault(model_key, []).append(rounded_f(max(vals)))
    rows = []
    for model_key, maxima in sorted(by_model.items()):
        for m in markets:
            kind = m.get("strike_type")
            if kind == "between":
                hits = sum(m["floor_strike"] <= t <= m["cap_strike"] for t in maxima)
            elif kind == "less":
                hits = sum(t < m["cap_strike"] for t in maxima)
            elif kind == "greater":
                hits = sum(t > m["floor_strike"] for t in maxima)
            else:
                raise RuntimeError(f"Unknown strike type {kind}: {m['ticker']}")
            p_yes = hits / len(maxima)
            yes_bid = float(m["yes_bid_dollars"])
            yes_ask = float(m["yes_ask_dollars"])
            rows.append({"model": MODEL_NAMES[model_key], "model_key": model_key,
                         "market_ticker": m["ticker"], "range": m["yes_sub_title"],
                         "n_members": len(maxima), "n_yes_members": hits,
                         "p_yes_member_frequency": p_yes,
                         "yes_bid": yes_bid, "yes_ask": yes_ask,
                         "yes_mid": (yes_bid + yes_ask) / 2,
                         "yes_edge_at_ask_before_fees": p_yes - yes_ask,
                         "no_ask_from_yes_bid": 1 - yes_bid,
                         "p_no_member_frequency": 1 - p_yes,
                         "no_edge_at_ask_before_fees": (1 - p_yes) - (1 - yes_bid)})
    with (ROOT / "model_market_probabilities.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    return rows


def write_consolidated_table(markets, member_rows, nbm_rows):
    model_columns = {
        "ecmwf_ifs025_ensemble": "ecmwf_p_yes",
        "icon_seamless_eps": "icon_p_yes",
        "ncep_gefs_seamless": "gefs_p_yes",
    }
    by_ticker_model = {(r["market_ticker"], r["model_key"]): r for r in member_rows}
    by_ticker_nbm = {r["market_ticker"]: r for r in nbm_rows}
    rows = []
    for market in markets:
        ticker = market["ticker"]
        components = {key: by_ticker_model[(ticker, key)]["p_yes_member_frequency"]
                      for key in model_columns}
        global_avg = sum(components.values()) / len(components)
        yes_bid, yes_ask = float(market["yes_bid_dollars"]), float(market["yes_ask_dollars"])
        no_ask = float(market["no_ask_dollars"])
        nbm = by_ticker_nbm.get(ticker, {}).get("nbm_gaussian_rounded_probability")
        row = {"market_ticker": ticker, "range": market["yes_sub_title"],
               "yes_bid": yes_bid, "yes_ask": yes_ask, "yes_mid_implied_probability": (yes_bid + yes_ask) / 2,
               **components, "global_ensemble_equal_weight_avg": global_avg,
               "global_avg_yes_edge_at_ask_before_fees": global_avg - yes_ask,
               "no_ask": no_ask, "global_avg_no_probability": 1 - global_avg,
               "global_avg_no_edge_at_ask_before_fees": (1 - global_avg) - no_ask,
               "nbm_gaussian_rounded_probability": nbm,
               "nbm_yes_edge_at_ask_before_fees": (nbm - yes_ask) if nbm is not None else None,
               "nbm_no_edge_at_ask_before_fees": (1 - nbm - no_ask) if nbm is not None else None}
        rows.append(row)
    with (ROOT / "market_model_comparison.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0]))
        writer.writeheader(); writer.writerows(rows)
    return rows


def nws_high(forecast):
    periods = forecast.get("properties", {}).get("periods", [])
    target = [p for p in periods if p.get("startTime", "")[:10] == TARGET_DATE]
    return max((p["temperature"] for p in target if p.get("temperatureUnit") == "F"), default=None), target


def main():
    markets, market_snap = market_data()
    ensemble = ensemble_data()
    nws = nws_data()
    nbm = nbm_data()
    summaries = analyze_ensembles(ensemble)
    nws_max, nws_periods = nws_high(nws)
    nbm_fields = nbm["fields_first_valid_column_f"]
    mu, sigma = nbm_fields["TXNMN"], nbm_fields["TXNSD"]
    # Approximate probability that the integer-reported maximum rounds to 60°
    # or 61°F: Gaussian mass on [59.5, 61.5), using NBM's reported mean/SD.
    cdf = lambda x: 0.5 * (1 + math.erf(x / math.sqrt(2)))
    nbm_rows = []
    for m in markets:
        kind = m.get("strike_type")
        lower, upper = None, None
        if kind == "between":
            lower, upper = float(m["floor_strike"]) - 0.5, float(m["cap_strike"]) + 0.5
        elif kind == "less":
            upper = float(m["cap_strike"]) - 0.5
        elif kind == "greater":
            lower = float(m["floor_strike"]) + 0.5
        else:
            raise RuntimeError(f"Unknown strike type {kind}: {m['ticker']}")
        if lower is None:
            p_yes = cdf((upper - mu) / sigma)
        elif upper is None:
            p_yes = 1 - cdf((lower - mu) / sigma)
        else:
            p_yes = cdf((upper - mu) / sigma) - cdf((lower - mu) / sigma)
        yes_bid, yes_ask = float(m["yes_bid_dollars"]), float(m["yes_ask_dollars"])
        no_ask = float(m["no_ask_dollars"])
        nbm_rows.append({"market_ticker": m["ticker"], "range": m["yes_sub_title"],
                         "nbm_gaussian_rounded_probability": p_yes,
                         "yes_bid": yes_bid, "yes_ask": yes_ask,
                         "yes_edge_at_ask_before_fees": p_yes - yes_ask,
                         "no_ask_from_yes_bid": no_ask,
                         "no_edge_at_ask_before_fees": (1 - p_yes) - no_ask})
    with (ROOT / "nbm_market_probability_approx.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(nbm_rows[0]))
        writer.writeheader(); writer.writerows(nbm_rows)
    member_rows = model_market_probabilities(ensemble, markets)
    write_consolidated_table(markets, member_rows, nbm_rows)
    nbm_p_60_61 = next(r["nbm_gaussian_rounded_probability"] for r in nbm_rows
                       if r["range"] == "60° to 61°")
    (ROOT / "nws_target_day_periods.json").write_text(
        json.dumps(nws_periods, indent=2) + "\n", encoding="utf-8")
    quote_fields = ["ticker", "yes_sub_title", "yes_bid_dollars", "yes_ask_dollars",
                    "no_bid_dollars", "no_ask_dollars",
                    "last_price_dollars", "yes_ask_size_fp", "volume_24h_fp",
                    "open_interest_fp", "rules_primary"]
    with (ROOT / "kalshi_market_rows.csv").open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=quote_fields)
        writer.writeheader()
        for m in markets:
            writer.writerow({k: m.get(k, "") for k in quote_fields})
    print(json.dumps({"market_count": len(markets), "market_snapshot_at": market_snap["fetched_at_utc"],
                      "ensemble_grid": {"latitude": ensemble.get("latitude"),
                                        "longitude": ensemble.get("longitude"),
                                        "elevation_m": ensemble.get("elevation")},
                      "model_summaries": summaries, "nws_hourly_high_f": nws_max,
                      "nws_periods": len(nws_periods),
                      "nbm_fields_first_valid_column_f": nbm_fields,
                      "nbm_gaussian_rounded_60_61_approx": nbm_p_60_61}, indent=2))


if __name__ == "__main__":
    main()
