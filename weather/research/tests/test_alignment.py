import unittest

from weather.research.alignment import align_forecast, align_forecasts


def pair(**forecast_overrides):
    forecast = {
        "run_id": "synthetic-run-1",
        "model": "synthetic-model",
        "issued_at": "2026-01-01T12:00:00Z",
        "valid_start": "2026-01-02T00:00:00Z",
        "valid_end": "2026-01-03T00:00:00Z",
        "variable": "daily_high",
        "unit": "C",
        "timezone": "America/New_York",
        "location_ref": "synthetic-station-1",
    }
    forecast.update(forecast_overrides)
    contract = {
        "decision_at": "2026-01-01T18:00:00-05:00",
        "valid_start": "2026-01-02T00:00:00Z",
        "valid_end": "2026-01-03T00:00:00Z",
        "variable": "daily_high",
        "unit": "C",
        "timezone": "America/New_York",
        "location_ref": "synthetic-station-1",
    }
    return forecast, contract


class AlignmentTests(unittest.TestCase):
    def test_accepts_forecast_issued_before_decision_and_converts_dst_offsets(self):
        forecast, contract = pair()
        result = align_forecast(forecast, contract)
        self.assertTrue(result["eligible"])
        self.assertEqual(11.0, result["lead_hours"])

    def test_rejects_lookahead_unit_location_timezone_and_window(self):
        forecast, contract = pair(
            issued_at="2026-01-02T00:00:00Z", unit="F", location_ref="other",
            timezone="UTC", valid_end="2026-01-02T12:00:00Z",
        )
        result = align_forecast(forecast, contract)
        self.assertFalse(result["eligible"])
        self.assertEqual({"forecast_issued_after_decision", "unit_mismatch", "spatial_support_mismatch",
                          "timezone_mismatch", "valid_window_not_covered"}, set(result["reasons"]))

    def test_joint_location_sets_must_match(self):
        forecast, contract = pair(location_ref=None, location_refs=["loc-a", "loc-b"])
        contract.pop("location_ref")
        contract["location_refs"] = ["loc-b", "loc-a"]
        self.assertTrue(align_forecast(forecast, contract)["eligible"])
        contract["location_refs"] = ["loc-a"]
        self.assertIn("spatial_support_mismatch", align_forecast(forecast, contract)["reasons"])

    def test_alignment_report_counts_reasons_and_requires_paired_inputs(self):
        forecast, contract = pair()
        late, _ = pair(issued_at="2026-01-02T00:00:00Z")
        report = align_forecasts([forecast, late], [contract, contract])
        self.assertEqual((1, 1), (report["accepted_count"], report["rejected_count"]))
        self.assertEqual(1, report["rejection_counts"]["forecast_issued_after_decision"])
        with self.assertRaises(ValueError):
            align_forecasts([forecast], [])


if __name__ == "__main__":
    unittest.main()
