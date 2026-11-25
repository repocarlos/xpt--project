import json
import unittest
from pathlib import Path

from research.options.reconstruct_calls import reconstruct_calls


FIXTURE = Path(__file__).parents[1] / "fixtures" / "digital_curve_v1.json"


class ReconstructCallsTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_linear_curve_integrates_exactly(self):
        doc = {
            "schema_version": "options.digital_curve.v1",
            "fixture_status": "synthetic",
            "underlying": "SYNTH",
            "expiry": "T",
            "event_relation": ">",
            "price_basis": "present_value_per_unit_payout",
            "price_convention": "PV per unit payout",
            "payout": 1,
            "points": [
                {"threshold": 0, "bid": 0.8, "ask": 0.8},
                {"threshold": 10, "bid": 0.4, "ask": 0.4},
                {"threshold": 20, "bid": 0.0, "ask": 0.0}
            ],
            "requested_strikes": [0, 5, 20]
        }
        result = reconstruct_calls(doc)
        self.assertAlmostEqual(result["results"][0]["observed_range_call"]["lower"], 8.0)
        self.assertAlmostEqual(result["results"][1]["observed_range_call"]["lower"], 4.5)
        self.assertAlmostEqual(result["results"][2]["observed_range_call"]["lower"], 0.0)

    def test_quote_bounds_propagate(self):
        result = reconstruct_calls(self.document)
        point = result["results"][0]["observed_range_call"]
        self.assertLess(point["lower"], point["upper"])
        self.assertEqual(point["value_kind"], "synthetic_call_present_value_equivalent")

    def test_requested_strike_outside_coverage_is_flagged(self):
        self.document["requested_strikes"] = [70, 130]
        result = reconstruct_calls(self.document)
        for point in result["results"]:
            self.assertTrue(point["outside_observed_coverage"])
            self.assertIsNone(point["observed_range_call"])

    def test_tail_scenarios_are_explicit_and_ordered(self):
        result = reconstruct_calls(self.document)
        point = result["results"][0]
        tails = point["tail_scenarios"]
        self.assertEqual([row["name"] for row in tails], ["zero_at_cap", "half_at_cap", "held_to_cap"])
        self.assertLess(tails[0]["total_lower"], tails[1]["total_lower"])
        self.assertLess(tails[1]["total_lower"], tails[2]["total_lower"])
        self.assertFalse(point["tail_unknown"])

    def test_nonmonotone_quotes_are_flagged_without_smoothing(self):
        doc = {
            "schema_version": "options.digital_curve.v1",
            "fixture_status": "synthetic",
            "underlying": "SYNTH",
            "expiry": "T",
            "event_relation": ">",
            "price_basis": "present_value_per_unit_payout",
            "price_convention": "PV per unit payout",
            "payout": 1,
            "points": [
                {"threshold": 10, "bid": 0.3, "ask": 0.4},
                {"threshold": 20, "bid": 0.5, "ask": 0.6},
                {"threshold": 30, "bid": 0.1, "ask": 0.2}
            ],
            "requested_strikes": [10]
        }
        point = reconstruct_calls(doc)["results"][0]
        self.assertFalse(point["curve_monotone"])
        self.assertFalse(point["eligible_for_model_use"])

    def test_excluded_quotes_are_reported(self):
        self.document["points"][2]["quote_status"] = "stale"
        point = reconstruct_calls(self.document)["results"][0]
        self.assertTrue(point["quote_status_warning"])
        self.assertIn("SYN-100", point["excluded_contract_ids"])
        self.assertFalse(point["eligible_for_model_use"])

    def test_non_synthetic_input_is_rejected(self):
        self.document["fixture_status"] = "real"
        with self.assertRaisesRegex(ValueError, "explicitly synthetic"):
            reconstruct_calls(self.document)

    def test_discount_factor_only_applies_to_undiscounted_basis(self):
        result = reconstruct_calls(self.document)
        self.assertEqual(result["results"][0]["observed_range_call"]["value_kind"],
                         "synthetic_call_present_value_equivalent")
        undiscounted = dict(self.document)
        undiscounted.pop("discount_factor")
        result = reconstruct_calls(undiscounted)
        self.assertEqual(result["results"][0]["observed_range_call"]["value_kind"],
                         "undiscounted_event_price_integral")

    def test_curve_without_tail_is_not_complete_for_model_use(self):
        self.document.pop("tail")
        point = reconstruct_calls(self.document)["results"][0]
        self.assertTrue(point["tail_unknown"])
        self.assertFalse(point["eligible_for_model_use"])

    def test_pre_discounted_quotes_reject_a_second_discount_factor(self):
        self.document["price_basis"] = "present_value_per_unit_payout"
        with self.assertRaisesRegex(ValueError, "already-present-value"):
            reconstruct_calls(self.document)

    def test_step_interpolation_scenarios_are_explicit(self):
        doc = {
            "schema_version": "options.digital_curve.v1",
            "fixture_status": "synthetic",
            "underlying": "SYNTH",
            "expiry": "T",
            "event_relation": ">",
            "price_basis": "present_value_per_unit_payout",
            "price_convention": "PV per unit payout",
            "payout": 1,
            "points": [
                {"threshold": 0, "bid": 0.8, "ask": 0.8},
                {"threshold": 10, "bid": 0.4, "ask": 0.4},
                {"threshold": 20, "bid": 0.0, "ask": 0.0}
            ],
            "requested_strikes": [0],
        }
        linear = reconstruct_calls(doc)["results"][0]["observed_range_call"]
        doc["interpolation_method"] = "left_step"
        left = reconstruct_calls(doc)["results"][0]["observed_range_call"]
        doc["interpolation_method"] = "right_step"
        right = reconstruct_calls(doc)["results"][0]["observed_range_call"]
        self.assertEqual(linear["lower"], 8.0)
        self.assertEqual(left["lower"], 12.0)
        self.assertEqual(right["lower"], 4.0)


if __name__ == "__main__":
    unittest.main()
