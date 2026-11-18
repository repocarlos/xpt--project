# Dashboard shell prototype

This is a portable static prototype with no package manager, external API, or build step. It uses HTML, CSS, and a small hash router so sector/study links work on any static host without server-side route rewrites.

## Run locally

From the repository root:

```sh
python3 -m http.server 8000 --directory dashboard/app
```

Open `http://127.0.0.1:8000/`.

## Routes

* `#/` — study overview
* `#/sectors/weather` — Weather sector overview
* `#/studies/weather` — daily-temperature pilot
* `#/studies/cross-venue` — Polymarket–Kalshi pilot
* `#/studies/options` — options feasibility pilot

Add a study route in `app.js` and link it with a hash URL. Keep sector routes separate from cross-cutting study collections.

## Data and hosting status

This prototype deliberately renders no market observations, estimates, charts, or source links. It marks the data unavailable while source-use rights and study inputs are pending. Replace the static unavailable states only when the approved study record, manifest/rights state, and freshness rules are available. Do not put API secrets or credentials in this browser bundle.

The shell is portable, but no persistent staging host, domain, HTTPS configuration, access controls, monitoring, backups, or operational owner is configured here. GRO-69 tracks that separate hosting decision. The harness working directory is not a production host.

## Browser checks

From the repository root, run:

```sh
python3 -m unittest dashboard.test_app_shell -v
```

The check uses the installed Playwright/Chromium environment and a local static HTTP server.
