import unittest

from weather.research.calibration import chronological_event_split, evaluate_chronological_holdout, score_probabilities


def row(event_id, day, probability, outcome):
    return {
        "event_id": event_id,
        "decision_at": f"2026-01-{day:02d}T12:00:00Z",
        "probability": probability,
        "outcome": outcome,
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-approval-v1",
    }


class CalibrationTests(unittest.TestCase):
    def test_chronological_split_keeps_all_event_rows_together(self):
        records = [row("event-a", 1, 0.1, 0), row("event-b", 2, 0.8, 1),
                   row("event-b", 3, 0.7, 1), row("event-c", 4, 0.2, 0), row("event-d", 5, 0.9, 1)]
        split = chronological_event_split(records, holdout_fraction=0.5)
        self.assertEqual({"event-a", "event-b"}, set(split["train_event_ids"]))
        self.assertEqual({"event-c", "event-d"}, set(split["holdout_event_ids"]))
        self.assertEqual(2, sum(x["event_id"] == "event-b" for x in split["train"]))

    def test_metrics_match_hand_calculated_example_and_include_reliability_counts(self):
        records = [row("a", 1, 0.0, 0), row("b", 2, 1.0, 1), row("c", 3, 0.5, 1)]
        result = score_probabilities(records, bins=2, min_events_per_bin=2)
        self.assertAlmostEqual((0 + 0 + 0.25) / 3, result["brier_score"])
        self.assertAlmostEqual(-__import__("math").log(0.5) / 3, result["log_loss"])
        self.assertEqual([1, 2], [item["count"] for item in result["reliability_bins"]])
        self.assertTrue(result["reliability_bins"][0]["sparse"])
        self.assertIsNotNone(result["reliability_bins"][1]["observed_rate_wilson_95"])

    def test_log_loss_clips_extreme_probability(self):
        result = score_probabilities([row("a", 1, 0.0, 1)])
        self.assertAlmostEqual(-__import__("math").log(1e-15), result["log_loss"])

    def test_holdout_marks_sparse_family_sample_and_is_not_profitability(self):
        records = [row(f"event-{i}", i + 1, 0.5, i % 2) for i in range(1, 6)]
        result = evaluate_chronological_holdout(records, holdout_fraction=0.4, bins=2,
                                                min_events_per_bin=2, min_holdout_events=3)
        self.assertTrue(result["sparse_holdout"])
        self.assertEqual(2, result["event_count"])
        self.assertIn("not_profitability", result["interpretation"])

    def test_rejects_invalid_probability_outcome_and_unapproved_input(self):
        with self.assertRaises(ValueError):
            score_probabilities([row("a", 1, 1.1, 1)])
        with self.assertRaises(ValueError):
            score_probabilities([row("a", 1, 0.5, 2)])
        with self.assertRaises(PermissionError):
            score_probabilities([row("a", 1, 0.5, 1) | {"source_use_status": "unresolved"}])

    def test_single_event_cannot_be_split(self):
        with self.assertRaises(ValueError):
            chronological_event_split([row("only", 1, 0.2, 0)])


if __name__ == "__main__":
    unittest.main()
