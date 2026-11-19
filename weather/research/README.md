# Source-neutral weather research helpers

This package contains validation and analysis utilities for the staged weather
study. The helpers operate on caller-provided records; they do not fetch market,
settlement, or forecast data.

## Settlement mappings

`settlement.validate_mapping` checks a family-aware mapping record for the event,
weather variable and unit, spatial support, timezone, validity window, resolution
authority and source, settlement rule/version, mapping status, and source-use
status. Verified mappings also need independent reviewer and evidence references;
ambiguous mappings need an explanation.

`settlement.outcome_join_eligible` is stricter: the mapping must be verified,
source use must be approved, and an approval evidence reference must be present.
Synthetic fixtures can exercise this path. Real mappings and outcome joins remain
blocked until the source-specific use and retention terms are recorded by the
authorized owner.

Run the package's synthetic checks with:

```sh
python3 -m unittest discover -s weather/research/tests -p 'test_*.py'
```
