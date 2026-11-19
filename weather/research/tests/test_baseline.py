import unittest

from weather.research.baseline import compare_models


def market(**overrides):
    value = {
        "family": "temperature",
        "cohort_id": "synthetic-cohort-v1",
        "quote_at": "2026-01-01T11:59:00Z",
        "quote_type": "top_of_book",
        "yes_bid": 0.42,
        "yes_ask": 0.48,
        "no_bid": 0.51,
        "no_ask": 0.57,
        "mapping_status": "verified",
        "bucket_ladder_complete": False,
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-market-approval-v1",
    }
    value.update(overrides)
    return value


def forecasts():
    return [
        {"model": "synthetic-model-a", "run_id": "run-a", "probability": 0.62, "alignment_eligible": True,
         "source_use_status": "approved", "source_use_evidence_ref": "synthetic-model-approval-v1"},
        {"model": "synthetic-model-b", "run_id": "run-b", "probability": 0.46, "alignment_eligible": True,
         "source_use_status": "approved", "source_use_evidence_ref": "synthetic-model-approval-v1"},
    ]


class BaselineTests(unittest.TestCase):
    def test_keeps_models_separate_and_quote_sides_distinct(self):
        rows = compare_models(market(), forecasts(), decision_at="2026-01-01T12:00:00Z", max_quote_age_seconds=120)
        self.assertEqual(2, len(rows))
        self.assertEqual((0.42, 0.48), (rows[0]["yes_bid"], rows[0]["yes_ask"]))
        self.assertAlmostEqual(0.45, rows[0]["midpoint"])
        self.assertAlmostEqual(0.06, rows[0]["spread"])
        self.assertAlmostEqual(0.14, rows[0]["buy_yes_gross_edge"])
        self.assertEqual("synthetic-model-b", rows[1]["model"])
        self.assertTrue(rows[0]["incomplete_bucket_ladder"])
        self.assertEqual("candidate_gap_for_validation_only", rows[0]["interpretation"])

    def test_stale_or_misaligned_quotes_have_no_executable_edges(self):
        rows = compare_models(market(), [forecasts()[0] | {"alignment_eligible": False}],
                              decision_at="2026-01-01T12:10:00Z", max_quote_age_seconds=30)
        self.assertTrue(rows[0]["stale_quote"])
        self.assertFalse(rows[0]["executable_quote_context"])
        self.assertIsNone(rows[0]["buy_yes_gross_edge"])

    def test_midpoint_only_quote_does_not_become_executable(self):
        row = compare_models(market(quote_type="midpoint_only"), [forecasts()[0]],
                             decision_at="2026-01-01T12:00:00Z", max_quote_age_seconds=120)[0]
        self.assertIsNotNone(row["midpoint"])
        self.assertFalse(row["executable_quote_context"])
        self.assertIsNone(row["buy_yes_net_edge"])

    def test_incoherent_quote_and_invalid_probability_are_flagged_or_rejected(self):
        row = compare_models(market(yes_bid=0.6, yes_ask=0.5), forecasts(), decision_at="2026-01-01T12:00:00Z", max_quote_age_seconds=120)[0]
        self.assertFalse(row["quote_coherent"])
        self.assertIsNone(row["midpoint"])
        with self.assertRaises(ValueError):
            compare_models(market(), [forecasts()[0] | {"probability": 1.1}], decision_at="2026-01-01T12:00:00Z", max_quote_age_seconds=120)

    def test_unapproved_source_cannot_enter_comparison(self):
        with self.assertRaises(PermissionError):
            compare_models(market(source_use_status="unresolved"), forecasts(), decision_at="2026-01-01T12:00:00Z", max_quote_age_seconds=120)


if __name__ == "__main__":
    unittest.main()
