# Dashboard shell prototype

This is a portable static prototype with no package manager, external API, or build step. It uses HTML, CSS, and a small hash router so sector/study links work on any static host without server-side route rewrites.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --directory dashboard/app
```

Open `http://127.0.0.1:8000/`.

## Routes

* `#/` — sector-first catalog
* `#/sectors` — reviewed sector directory
* `#/sectors/weather` — Weather sector overview
* `#/collections/research` — cross-cutting venue and options studies
* `#/studies/weather` — daily-temperature pilot
* `#/studies/cross-venue` — Polymarket–Kalshi pilot
* `#/studies/options` — options feasibility pilot

The Weather pilot is reached through the Weather sector. Polymarket–Kalshi and options are reached through the separately labeled cross-cutting collection; the options placement is a proposed MVP choice pending product review. These routes represent individual research pilots, not exhaustive sector catalogs. Add reviewed sectors or studies only after the information architecture and content have been approved.

## Shared study page

The study routes use one shared field order: question and evidence status; contract scope and settlement; market-price context; data period and coverage; method and benchmark; a domain-specific module; findings and measures; uncertainty; limitations; study update/freshness; sources and reproducibility. Domain modules remain separate so weather calibration, venue discrepancies, and options-derived quantities are not merged into a common score.

The chart component accepts a study-specific DOM visualization, caption, and datapoint table. It displays source attribution, study update time, quote freshness, coverage gaps, uncertainty, and explicit quote-quality flags separately. Missing data is labeled unavailable/not assessed. A study must supply stale or wide-quote flags; the shell does not invent thresholds.

This prototype has no study records or authorized market data. Missing values are shown as unavailable or not supplied, never as zero. Study update time is distinct from quote time. The current schema/content mapping is still under review; do not replace the empty states with real observations until source rights, provenance, and a reviewed study handoff are available.

## Data and hosting status

This prototype deliberately renders no market observations, estimates, charts, or source links. It marks the data unavailable while source-use rights and study inputs are pending. Replace the static unavailable states only when the approved study record, manifest/rights state, and freshness rules are available. Do not put API secrets or credentials in this browser bundle.

The shell is portable, but no persistent staging host, domain, HTTPS configuration, access controls, monitoring, backups, or operational owner is configured here. GRO-69 tracks that separate hosting decision. The harness working directory is not a production host.

## Browser checks

From the repository root, run:

```sh
python3 -m unittest dashboard.test_app_shell -v
```

The check uses the installed Playwright/Chromium environment and a local static HTTP server.
