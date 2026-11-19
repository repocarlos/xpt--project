"""Event-level chronological validation and probability calibration metrics."""

from __future__ import annotations

from datetime import datetime, timezone
import math
from typing import Any, Mapping


def chronological_event_split(
    records: list[Mapping[str, Any]], *, holdout_fraction: float = 0.2,
) -> dict[str, Any]:
    """Split on event chronology so records/contracts for an event cannot leak."""
    if not 0 < holdout_fraction < 1:
        raise ValueError("holdout_fraction must be between 0 and 1")
    event_times: dict[str, datetime] = {}
    for row in records:
        event_id = row.get("event_id")
        if not isinstance(event_id, str) or not event_id:
            raise ValueError("every record needs event_id")
        decision = _timestamp(row.get("decision_at"))
        event_times[event_id] = max(event_times.get(event_id, decision), decision)
    events = sorted(event_times, key=lambda key: (event_times[key], key))
    if len(events) < 2:
        raise ValueError("at least two distinct events are required")
    holdout_count = max(1, math.ceil(len(events) * holdout_fraction))
    if holdout_count >= len(events):
        raise ValueError("holdout would leave no training events")
    holdout_ids = set(events[-holdout_count:])
    train = [dict(row) for row in records if row["event_id"] not in holdout_ids]
    holdout = [dict(row) for row in records if row["event_id"] in holdout_ids]
    return {
        "train": train,
        "holdout": holdout,
        "train_event_ids": sorted({row["event_id"] for row in train}),
        "holdout_event_ids": sorted(holdout_ids),
        "cutoff_at": event_times[events[-holdout_count]].isoformat().replace("+00:00", "Z"),
        "holdout_fraction_requested": holdout_fraction,
    }


def score_probabilities(
    records: list[Mapping[str, Any]], *, bins: int = 10, min_events_per_bin: int = 1,
    clip_epsilon: float = 1e-15,
) -> dict[str, Any]:
    """Compute Brier, clipped log loss, reliability bins, and sparse-bin flags."""
    if not records:
        raise ValueError("at least one observation is required")
    if bins < 1 or min_events_per_bin < 1 or not 0 < clip_epsilon < 0.5:
        raise ValueError("invalid reliability or clipping configuration")
    probabilities, outcomes = [], []
    for row in records:
        if row.get("source_use_status") != "approved" or not _text(row.get("source_use_evidence_ref")):
            raise PermissionError("calibration requires approved source use and evidence")
        probability = row.get("probability")
        outcome = row.get("outcome")
        if isinstance(probability, bool) or not isinstance(probability, (int, float)) or not math.isfinite(probability) or not 0 <= probability <= 1:
            raise ValueError("probability must be finite and in [0, 1]")
        if outcome not in (0, 1) or isinstance(outcome, bool):
            raise ValueError("outcome must be binary 0 or 1")
        probabilities.append(float(probability))
        outcomes.append(int(outcome))
    count = len(records)
    brier = sum((p - y) ** 2 for p, y in zip(probabilities, outcomes)) / count
    log_loss = -sum(y * math.log(max(clip_epsilon, p)) + (1-y) * math.log(max(clip_epsilon, 1-p))
                    for p, y in zip(probabilities, outcomes)) / count
    reliability = []
    for index in range(bins):
        members = [(p, y) for p, y in zip(probabilities, outcomes)
                   if min(bins - 1, int(p * bins)) == index]
        n = len(members)
        if n:
            avg_probability = sum(p for p, _ in members) / n
            observed_rate = sum(y for _, y in members) / n
            low, high = _wilson_interval(sum(y for _, y in members), n)
        else:
            avg_probability = observed_rate = low = high = None
        reliability.append({
            "bin_index": index,
            "lower_bound": index / bins,
            "upper_bound": (index + 1) / bins,
            "count": n,
            "average_probability": avg_probability,
            "observed_rate": observed_rate,
            "observed_rate_wilson_95": [low, high] if n else None,
            "sparse": n < min_events_per_bin,
        })
    return {
        "observation_count": count,
        "event_count": len({row.get("event_id") for row in records}),
        "brier_score": brier,
        "log_loss": log_loss,
        "log_loss_clip_epsilon": clip_epsilon,
        "reliability_bins": reliability,
        "min_events_per_bin": min_events_per_bin,
        "interpretation": "calibration_quality_only_not_profitability",
    }


def evaluate_chronological_holdout(
    records: list[Mapping[str, Any]], *, holdout_fraction: float = 0.2,
    bins: int = 10, min_events_per_bin: int = 1, min_holdout_events: int,
) -> dict[str, Any]:
    split = chronological_event_split(records, holdout_fraction=holdout_fraction)
    scored = score_probabilities(split["holdout"], bins=bins, min_events_per_bin=min_events_per_bin)
    scored.update({
        "train_event_ids": split["train_event_ids"],
        "holdout_event_ids": split["holdout_event_ids"],
        "cutoff_at": split["cutoff_at"],
        "holdout_fraction_requested": holdout_fraction,
        "sparse_holdout": scored["event_count"] < min_holdout_events,
        "minimum_holdout_events": min_holdout_events,
    })
    return scored


def _timestamp(value: Any) -> datetime:
    if not isinstance(value, str):
        raise ValueError("decision_at must be an ISO-8601 timestamp")
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValueError("decision_at must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError("decision_at must include a timezone")
    return parsed.astimezone(timezone.utc)


def _wilson_interval(successes: int, n: int, z: float = 1.959963984540054) -> tuple[float, float]:
    rate = successes / n
    denom = 1 + z * z / n
    center = (rate + z * z / (2 * n)) / denom
    margin = z * math.sqrt(rate * (1-rate) / n + z*z / (4*n*n)) / denom
    return max(0.0, center - margin), min(1.0, center + margin)


def _text(value: Any) -> bool:
    return isinstance(value, str) and bool(value.strip())
