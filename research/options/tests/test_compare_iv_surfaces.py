import json
import math
import tempfile
import unittest
from pathlib import Path

from research.options.compare_iv_surfaces import (
    bs_call_price,
    compare_surfaces,
    implied_volatility,
    plot_comparison,
)


FIXTURE = Path(__file__).parents[1] / "fixtures" / "surface_comparison_v1.json"


class CompareIVSurfacesTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_black_scholes_price_inverts_back_to_volatility(self):
        for sigma in (0.12, 0.2, 0.55):
            price = bs_call_price(100, 105, 0.4, 0.03, 0.01, sigma)
            result = implied_volatility(price, 100, 105, 0.4, 0.03, 0.01)
            self.assertTrue(result["valid"])
            self.assertAlmostEqual(result["iv"], sigma, places=9)

    def test_price_outside_european_bounds_is_flagged(self):
        result = implied_volatility(120, 100, 100, 0.5, 0.03, 0.01)
        self.assertFalse(result["valid"])
        self.assertEqual(result["reason"], "outside_european_call_bounds")

    def test_surface_matches_exact_contract_keys_and_reports_iv_range(self):
        result = compare_surfaces(self.document)
        self.assertEqual(result["summary"]["matched_rows"], 6)
        for row in result["rows"]:
            self.assertEqual(row["status"], "candidate_dislocation_only")
            self.assertGreater(row["pm_iv"]["lower"], row["listed_iv"]["upper"])
            self.assertLessEqual(row["pm_iv"]["lower"], row["pm_iv"]["upper"])
            self.assertIsNotNone(row["delta_iv"]["lower_percentage_points"])
        self.assertIn("not a listed IV quote", result["interpretation"])
        self.assertIn("does not establish", result["candidate_gap_warning"])

    def test_unmatched_timestamp_is_not_filled_or_interpolated(self):
        self.document["listed_calls"][0]["snapshot_time"] = "2026-11-25T16:01:00Z"
        result = compare_surfaces(self.document)
        unmatched = [row for row in result["rows"] if row["strike"] == 85.0 and row["expiry"] == "2027-03-19"][0]
        self.assertEqual(unmatched["status"], "unmatched_listed_quote")
        self.assertEqual(unmatched["pm_iv"]["lower_valid"], True)

    def test_valuation_input_mismatch_is_flagged(self):
        self.document["listed_calls"][0]["rate"] += 0.001
        result = compare_surfaces(self.document)
        row = [r for r in result["rows"] if r["strike"] == 85.0 and r["expiry"] == "2027-03-19"][0]
        self.assertEqual(row["status"], "valuation_input_mismatch")

    def test_non_present_value_pm_input_is_rejected_per_cell(self):
        self.document["pm_calls"][0]["price_basis"] = "undiscounted_event_price"
        result = compare_surfaces(self.document)
        row = result["rows"][0]
        self.assertEqual(row["status"], "invalid_pm_input")
        self.assertIn("present-value equivalent", row["reason"])

    def test_chart_labels_are_written_for_synthetic_fixture(self):
        result = compare_surfaces(self.document)
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "surface.png"
            plot_comparison(result, output)
            self.assertTrue(output.exists())
            self.assertGreater(output.stat().st_size, 1000)


if __name__ == "__main__":
    unittest.main()
