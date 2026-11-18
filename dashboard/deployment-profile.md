# Dashboard deployment profile

**Reviewed:** 2026-11-18  
**Status:** local preview documented; persistent staging host not confirmed  
**Scope:** static dashboard shell and synthetic-only smoke check. This is not production approval.

## Current deployment facts

| Concern | Current record | Status |
|---|---|---|
| Artifact | Plain HTML, CSS, and JavaScript in `dashboard/app`; no package manager, build step, database, or server-side route rewrites. | Confirmed from repository |
| Local preview | From repository root: `python3 -m http.server 8000 --bind 127.0.0.1 --directory dashboard/app`; open `http://127.0.0.1:8000/`; stop with Ctrl-C. | Confirmed; local only, HTTP only |
| Persistent host and hosting owner | No host or owner is configured in this repository. Whether the team has a separately administered host is unknown. | Carlos to confirm |
| Access path and stable HTTPS URL/domain | None recorded. The local preview has no HTTPS or authentication and must not be exposed as a shared/public service. | Carlos to confirm staging option |
| Persistence and backups | No deployment persistence, backup target, restore procedure, or responsible owner is documented. | Carlos/host owner to confirm |
| Access controls | Local preview binds to loopback. Staging authentication and authorization are not configured. | Local confirmed; staging unknown |
| Secrets | Static app requires no credentials. Do not place tokens or API keys in browser assets. | Confirmed for current prototype |
| Update/restart procedure | Local: update the checked-out repository, rerun the command above, and stop the server with Ctrl-C. Staging deploy/restart procedure is host-specific and unknown. | Local confirmed; staging unknown |
| Monitoring | No staging health checks, logs, or alerting are configured. | Host owner to confirm |
| Cost | Local preview has no hosting charge beyond the machine running it. Staging cost is unknown. | Staging owner to confirm |
| Data | Normal dashboard routes show unavailable states. Browser tests use only synthetic values in a clearly labeled fixture. | Confirmed; no real market data |

## Smoke check

Run from the repository root:

```sh
python3 -m unittest dashboard.test_app_shell -v
```

The suite starts a local static HTTP server, checks the dashboard routes, verifies that normal study pages remain unavailable, and renders synthetic chart/table values only inside a test fixture. It makes no external requests. There is no production build step; the static `dashboard/app` directory is the portable artifact.

## Decision needed

Carlos: confirm whether a persistent staging/VPS/static host already exists. If it does, record its operational owner, access path, stable HTTPS URL/domain, persistence and backups, access controls, secrets handling, update/restart procedure, monitoring, and cost. If no host exists, record that decision and retain loopback local preview as the fallback. Until this is answered, hosting availability is unknown and the harness is not a deployment target.

No release, live data ingestion, or external display of venue/source data is authorized by this profile. Source rights and study handoffs remain separate gates.
