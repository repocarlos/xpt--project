import unittest

from weather.research.study import run_weather_study


def calibration_rows(prefix):
    rows = []
    for i in range(1, 11):
        rows.append({
            "event_id": f"{prefix}-{i}",
            "decision_at": f"2026-01-{i:02d}T12:00:00Z",
            "probability": 0.8 if i % 2 else 0.2,
            "outcome": 1 if i % 2 else 0,
            "source_use_status": "approved",
            "source_use_evidence_ref": "synthetic-approval-v1",
        })
    return rows


def package(family, cohort_id):
    market = {
        "family": family,
        "cohort_id": cohort_id,
        "quote_at": "2026-01-01T11:59:00Z",
        "quote_type": "top_of_book",
        "yes_bid": 0.4,
        "yes_ask": 0.5,
        "no_bid": 0.49,
        "no_ask": 0.6,
        "mapping_status": "verified",
        "bucket_ladder_complete": False,
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-market-approval-v1",
    }
    forecasts = [{"model": f"{family}-model", "run_id": f"{cohort_id}-run", "probability": 0.7,
                  "alignment_eligible": True, "source_use_status": "approved",
                  "source_use_evidence_ref": "synthetic-model-approval-v1"}]
    return {
        "family": family,
        "cohort_id": cohort_id,
        "cohort_status": "selected",
        "source_use_status": "approved",
        "settlement_status": "verified",
        "coverage_status": "verified",
        "fixture_status": "synthetic",
        "source_use_evidence_ref": "synthetic-rights-v1",
        "selection_evidence_ref": "synthetic-selection-v1",
        "settlement_evidence_ref": "synthetic-settlement-v1",
        "coverage_evidence_ref": "synthetic-coverage-v1",
        "second_reviewer_ref": "synthetic-reviewer-v1",
        "second_reviewer_qualified": True,
        "market_pairs": [{"market": market, "forecasts": forecasts,
                          "decision_at": "2026-01-01T12:00:00Z", "max_quote_age_seconds": 120}],
        "calibration_records": calibration_rows(cohort_id),
    }


class StudyCoordinatorTests(unittest.TestCase):
    def test_keeps_families_separate_and_retains_models(self):
        result = run_weather_study([package("temperature", "temp-1"), package("wind", "wind-1")],
                                   holdout_fraction=0.2,
                                   min_holdout_events_by_family={"temperature": 2, "wind": 2})
        self.assertEqual(2, result["family_count"])
        self.assertEqual("none_family_stratified", result["pooling"])
        self.assertEqual(["temperature", "wind"], [row["family"] for row in result["families"]])
        self.assertEqual("temperature-model", result["families"][0]["comparisons"][0]["model"])
        self.assertEqual("ready_for_review", result["families"][0]["status"])
        self.assertEqual("synthetic", result["families"][0]["claim_status"])
        self.assertEqual("synthetic", result["claim_status"])

    def test_blocked_package_is_rejected_before_market_records_are_iterated(self):
        blocked = package("temperature", "blocked-1")
        blocked["source_use_status"] = "blocked"
        blocked.pop("fixture_status")
        def unopened():
            raise AssertionError("market pairs were touched before source gate")
            yield {}
        blocked["market_pairs"] = unopened()
        result = run_weather_study([blocked], holdout_fraction=0.2,
                                   min_holdout_events_by_family={"temperature": 2})
        self.assertEqual("blocked", result["families"][0]["status"])
        self.assertIn("source_use_unapproved", result["families"][0]["reasons"])
        self.assertEqual("pending", result["claim_status"])

    def test_empty_study_has_pending_claim_status(self):
        result = run_weather_study([], holdout_fraction=0.2,
                                   min_holdout_events_by_family={})
        self.assertEqual("pending", result["claim_status"])

    def test_sparse_family_is_not_reported_as_ready_or_pooled(self):
        data = package("climate_seasonal", "climate-1")
        data["calibration_records"] = calibration_rows("climate-1")[:2]
        result = run_weather_study([data], holdout_fraction=0.5,
                                   min_holdout_events_by_family={"climate_seasonal": 5})["families"][0]
        self.assertEqual("sparse", result["calibration_status"])
        self.assertEqual("insufficient", result["status"])
        self.assertEqual("held_out_result", result["evidence_class"])

    def test_duplicate_cohorts_and_missing_policy_fail_closed(self):
        data = package("temperature", "temp-1")
        duplicate = run_weather_study([data, data], holdout_fraction=0.2,
                                      min_holdout_events_by_family={"temperature": 2})
        self.assertEqual("blocked", duplicate["families"][1]["status"])
        self.assertIn("duplicate_cohort_id", duplicate["families"][1]["reasons"])
        with self.assertRaises(ValueError):
            run_weather_study([package("temperature", "temp-2")], holdout_fraction=0.2,
                              min_holdout_events_by_family={})


if __name__ == "__main__":
    unittest.main()
