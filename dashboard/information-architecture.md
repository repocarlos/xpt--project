# Prediction-market analytics dashboard: information architecture

**Status:** proposed MVP structure; product-lead review pending.
**Audience:** retail investors who want to understand what prediction markets are pricing and how to interpret the evidence.

## Reader questions

1. What kind of market or sector am I looking at?
2. What does a market in this sector resolve on, and which source/rule determines the outcome?
3. What does the quoted price mean, and how fresh/liquid is that quote?
4. What independent evidence or model is being compared with the market?
5. How strong is the evidence, what is uncertain, and what does this study not establish?

## Hierarchy and navigation

```text
Home / Study catalog
└── Sector overview
    └── Named study (clearly scoped pilot)
        └── Contract example or market detail (optional)
            └── Methods, sources, and reproducibility details
```

The home page lists sectors and available studies; it does not rank sectors by an unsupported common performance score. A sector overview explains the sector's contract conventions and links to one or more studies. A study is the unit of research, and a contract example is an illustration within its stated sample. Do not present one study or contract as representative of every market in a sector.

## MVP navigation labels and study scope

| Navigation label | First-release entry | Scope label shown in UI |
|---|---|---|
| **Weather** | Daily temperature-bucket markets and the weather probability comparison | “Pilot study: selected daily temperature markets, stations, and dates.” |
| **Cross-venue** | Polymarket–Kalshi matched-contract comparison | “Pilot study: selected pairs with reviewed settlement equivalence.” This is a cross-cutting study, not a market sector. |
| **Options** | Prediction-market threshold estimates compared with listed-options evidence | “Feasibility pilot: selected underlying, threshold, expiry, and option quotes.” This study is not a general options-market survey. |

The data sources and rights for all market tabs remain subject to approval. A navigation entry must not imply that a source is live or authorized when the study uses a frozen, synthetic, or unavailable dataset.

## Page content by level

### Home / study catalog

- Describe the platform's purpose in plain language.
- List sectors and the studies currently available in each.
- Show study status (for example, feasibility, descriptive, out-of-sample evaluated, or validated) using the shared evidence registry.
- Show last update and whether the entry is a live view, frozen analysis, or illustrative example.

### Sector overview

- Explain the sector and its common market/resolution conventions in plain language.
- State what the sector page includes and what it does not cover.
- Link to each study with its question, sample, period, evidence status, and update time.
- Surface sector-specific cautions, such as station/observation rules for weather or quote conventions for financial contracts.

### Study page

- State the research question, pilot universe, sample dates, source coverage, and method.
- Keep observed prices separate from model estimates and comparisons; label units and quote side/basis.
- Show study-specific charts and tables, uncertainty, data freshness, limitations, and evidence status.
- Link to the study's sources, settlement rules, code revision, and permitted underlying artifacts.
- Avoid one cross-study “edge” score: weather calibration, venue price gaps, and options-derived risk-neutral quantities measure different things.

### Optional contract example

Only include when it makes the study easier to understand. State venue, exact market/event identifier, outcome orientation, settlement rule and source, relevant timestamp/timezone, displayed price basis, and liquidity/freshness context. Show raw fields only when the relevant rights permit display.

## Open product decisions

- **Sector taxonomy:** keep Cross-venue as a study collection or file studies only under their underlying sectors? Proposed MVP: a separate Cross-venue study entry, explicitly tagged with participating sectors.
- **Options placement:** create an “Options” sector or treat options as a cross-cutting benchmark study? Product lead to decide; either way, label the current study as a selected feasibility pilot.
- **Market detail:** decide whether a study page needs individual contract pages or whether contract examples remain embedded in each study.
- **Scope of price display:** decide whether the MVP presents current market prices or frozen study snapshots. Rights, data freshness, and the lack of a collector currently favor frozen, timestamped study snapshots.

## Review

This is a product structure, not a claim that the research is validated. Adele should confirm the reader questions, hierarchy, and sector taxonomy; Carlos and Alay should confirm the Weather, Cross-venue, and Options labels match their study scopes.
