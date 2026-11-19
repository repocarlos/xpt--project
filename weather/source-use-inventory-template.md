# Weather source-use inventory

**Version:** 2
**Status:** Template only. No source is approved by this document; no provider rows were inspected.

Create one row per candidate source × weather family × intended use. Keep access, internal analysis, raw retention, normalized retention, derivation, sharing, and retail display as separate use records. An approval applies only to that exact source and family; never carry it across families. Use only `approved`, `limited`, `blocked`, or `no_go`; unresolved permission stays `blocked` with the missing evidence described.

| Field | Entry |
|---|---|
| Candidate source reference and venue/source type | Pending authorized inventory |
| Weather family and geography | Include station, grid, basin, polygon, or location-set level |
| Data tier and history horizon | Metadata/outcome, candles, trades, top-of-book, full depth, forecast archive |
| Intended use | One use per row from the list above |
| Use status and exact terms | Approved / limited / blocked / no-go; restrictions and conditions |
| Approval/license evidence reference | Required for approved use |
| Coverage status | Verified / claimed / unknown |
| Coverage date range, cadence, denominator | Keep verified, claimed, and unknown separate |
| Coverage evidence and as-of date | Required for verified or claimed coverage |
| Estimated volume and assumptions | Rows/bytes, cadence, retention; measured only from permitted evidence |
| Retention until and deletion conditions | Required for approved raw or normalized retention; enter an ISO-8601 timestamp with timezone that is still in the future, plus deletion conditions |
| Sharing/display conditions | Record separately; never infer from internal analysis permission |
| Reviewer and second weather-qualified reviewer | Include qualification evidence before raw market inspection |
| Open questions / stop condition | State what remains blocked and who can resolve it |

## Initial status

All candidate provider-specific terms, coverage, volume, and reviewer identity remain **blocked or unknown** pending authorized documentation. This template does not grant rights or identify a preferred source. Static history and prospective capture require separate use, retention, and coverage records.
