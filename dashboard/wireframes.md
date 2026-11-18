# Dashboard low-fidelity wireframes

**Status:** draft for product review  
**Revision date:** 2026-11-18  
**Data note:** these are layout examples only. They contain no market observations. Any later sample values must be marked synthetic; current data remains unavailable until source rights, capture, and hosting are approved.

The wireframes use the proposed sector → study → optional contract hierarchy in [information-architecture.md](information-architecture.md). Cross-venue is a study collection, not a market sector. Options placement and detailed contract routing remain open for Adele's product decision.

## Desktop: sector overview (approx. 1440 px)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Prediction Markets, Explained     Home   Sectors ▾   About the evidence       │
├──────────────────────────────────────────────────────────────────────────────┤
│ WEATHER                                                        Scope: pilots  │
│ How markets price weather outcomes                                        │
│ Contract rules differ by station, date, and measurement source.             │
│ [How weather contracts resolve]  [What the price means]                     │
├──────────────────────────────────────────────────────────────────────────────┤
│ Available research                                                          │
│ ┌──────────────────┐ ┌──────────────────┐ ┌──────────────────┐             │
│ │ Daily temperature│ │ Cross-venue      │ │ Options threshold│             │
│ │ Pilot study      │ │ Pilot collection │ │ Feasibility pilot│             │
│ │ Question         │ │ Question         │ │ Question         │             │
│ │ Sample / period  │ │ Pair coverage    │ │ Underlying/expiry│             │
│ │ Evidence status  │ │ Evidence status  │ │ Evidence status  │             │
│ │ Data state/time  │ │ Data state/time  │ │ Data state/time  │             │
│ │ [Open study]     │ │ [Open study]     │ │ [Open study]     │             │
│ └──────────────────┘ └──────────────────┘ └──────────────────┘             │
├──────────────────────────────────────────────────────────────────────────────┤
│ Sector conventions                                                         │
│ Resolution source · station · local date · threshold/bucket · rule changes  │
│ Data availability: No licensed live feed configured.                       │
└──────────────────────────────────────────────────────────────────────────────┘
```

Each card carries a small, explicit scope line and evidence category. The overview does not rank sectors or report one shared “edge” score. Only show the studies that actually belong to a sector; Cross-venue can instead be reached from a clearly labeled cross-cutting study collection.

## Narrow/mobile: sector overview (approx. 390 px)

```text
┌─────────────────────────┐
│ ☰  Prediction Markets   │
│    Home / Sectors       │
├─────────────────────────┤
│ WEATHER                 │
│ How markets price       │
│ weather outcomes        │
│ [Resolution basics]     │
│                         │
│ Scope: pilot studies    │
│ No licensed live feed   │
│ configured              │
├─────────────────────────┤
│ Daily temperature      │
│ Pilot study             │
│ Question · sample       │
│ Evidence status         │
│ Frozen / unavailable    │
│ [Open study]            │
├─────────────────────────┤
│ Sector conventions      │
│ Station and settlement  │
│ source · local date ·   │
│ bucket boundaries       │
├─────────────────────────┤
│ Cross-cutting studies   │
│ Cross-venue · Options   │
└─────────────────────────┘
```

The mobile order keeps scope, data state, and resolution basics ahead of study cards and charts. Cross-cutting studies are visibly separate from sector membership.

## Desktop: reusable study detail (approx. 1440 px)

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│ Home / Weather / Daily temperature pilot              Study status: PILOT   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Research question · selected market/date scope · method · update timestamp   │
│ Data state: FROZEN SNAPSHOT / SYNTHETIC EXAMPLE / UNAVAILABLE                 │
│ Evidence: [descriptive | model_estimate | validated_forecast | ...]           │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ What does the contract resolve on?    │ What is the market quoting?          │
│ Exact outcome · venue · rule version  │ Implied probability + quote basis    │
│ Resolution source · station · window  │ Bid / ask / midpoint · quote time    │
│ Timezone · local event date           │ Spread / displayed size / freshness │
│ [source and rules link]               │ No licensed current quote available │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ What is compared with the market?                                           │
│ External forecast/model · provider · issued-at · assumptions · uncertainty   │
├──────────────────────────────────────────────────────────────────────────────┤
│ Study-specific chart/table                                                 │
│ Axes, units, sample, quote side, timestamp, source, and evidence label       │
│ Weather: market vs forecast by lead time / calibration when validated       │
│ Cross-venue: matched quotes with settlement equivalence and spread          │
│ Options: threshold curve / implied-volatility transform with assumptions    │
├───────────────────────────────────────┬──────────────────────────────────────┤
│ Interpretation                        │ Limitations and uncertainty          │
│ Observed price ≠ external estimate     │ Sample coverage · missingness       │
│ Difference ≠ validated opportunity     │ Rule/source mismatches · costs      │
│ Finding wording tied to evidence label │ What this study does not establish  │
├───────────────────────────────────────┴──────────────────────────────────────┤
│ Sources and provenance · collection/update time · data rights · code version │
│ [permitted source] [method] [reproducibility] [permitted data manifest]       │
└──────────────────────────────────────────────────────────────────────────────┘
```

For an individual contract example, place the exact resolution rule and source beside the quote. Label the quote as a displayed observation and identify bid, ask, or midpoint. Put an external estimate in its own panel with method/provider and timestamp. A comparison may be called a **candidate gap** only when outcomes are matched and timestamps align; it remains unvalidated unless the study's evidence supports more.

## Narrow/mobile: reusable study detail (approx. 390 px)

```text
┌─────────────────────────┐
│ Home / Weather          │
│ Daily temperature pilot │
│ PILOT · descriptive     │
│ Frozen / unavailable    │
│ Updated: [timestamp]    │
├─────────────────────────┤
│ Research question       │
│ Scope · sample · method │
├─────────────────────────┤
│ What does it resolve on?│
│ Outcome · source · rule │
│ Station · date · window │
│ [View resolution rules] │
├─────────────────────────┤
│ What is the market      │
│ quoting?                │
│ Implied probability     │
│ Bid / ask / midpoint    │
│ Spread · as-of time     │
│ No licensed live quote  │
├─────────────────────────┤
│ External estimate       │
│ Provider · issued-at    │
│ Method · uncertainty   │
├─────────────────────────┤
│ Comparison chart/table  │
│ [chart or unavailable]  │
│ Units · source · sample │
├─────────────────────────┤
│ What it suggests        │
│ Evidence label + plain  │
│ language summary        │
├─────────────────────────┤
│ Limits and uncertainty  │
│ What this cannot show   │
├─────────────────────────┤
│ Sources · freshness     │
│ Rights · code version   │
└─────────────────────────┘
```

At narrow widths, resolution, quote interpretation, evidence label, and limitations stay in the first vertical flow; no tab or collapsed disclosure is required to understand the main claim. Source and reproducibility details may expand lower on the page.

## Content states and wording

| State | Label and display behavior |
|---|---|
| Current, approved data | Show provider/source, quote side, timestamp/timezone, spread, and permitted rights notice next to values. |
| Frozen study snapshot | “Frozen analysis — as of [timestamp]”; do not describe it as the current market price. |
| Synthetic example | Persistent “Synthetic example — not a market observation” label; no real venue logo or market ID. |
| Rights blocked | “Data unavailable while source-use permission is reviewed”; show no quote, chart point, or derived value. |
| Stale | Show last update and stale threshold; suppress “current” language and visually flag the value. |
| Validated forecast/finding | State sample, evaluation design, baseline, and uncertainty near the claim. Forecast validation does not imply profitability. |
| Candidate discrepancy | “Candidate price difference observed”; include match basis, timestamp alignment, and spread. Do not say “mispricing,” “arbitrage,” or “opportunity.” |

No common score is shown across weather calibration, venue price gaps, and options-derived risk-neutral values. Each chart has its own measure, units, and caveats.

## Review questions for Adele

1. Confirm whether Cross-venue should be a separate cross-cutting collection and where Options belongs in the sector catalog.
2. Choose inline expansion or a separate route for an individual contract example.
3. Confirm the scope/status badges and whether the mobile flow's source details can expand below the interpretation.
4. Confirm the frozen/unavailable/rights-blocked wording before implementation.

Carlos and Alay should confirm that Weather, Cross-venue, and Options labels and domain-specific chart regions match their study outputs. This draft does not approve any data source or settle the open taxonomy decisions.
