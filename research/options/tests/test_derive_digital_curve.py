import json
import unittest
from pathlib import Path

from research.options.align_inputs import align_inputs
from research.options.derive_digital_curve import derive_digital_curve


ALIGNMENT_FIXTURE = Path(__file__).parents[1] / "fixtures" / "alignment_v1.json"


class DeriveDigitalCurveTests(unittest.TestCase):
    def setUp(self):
        self.aligned = align_inputs(json.loads(ALIGNMENT_FIXTURE.read_text(encoding="utf-8")))

    def test_aligned_fixture_produces_ordered_event_price_curve(self):
        result = derive_digital_curve(self.aligned)
        self.assertEqual([p["threshold"] for p in result["points"]], [80, 90, 100, 110, 120])
        self.assertEqual(result["price_basis"], "undiscounted_event_price")
        self.assertIn("not unbiased forecasts", result["interpretation_warning"])
        self.assertEqual(result["curve_diagnostics"]["usable_points"], 3)
        self.assertFalse(result["curve_diagnostics"]["sparse_coverage_warning"])

    def test_yes_greater_than_event_uses_yes_book(self):
        result = derive_digital_curve(self.aligned)
        point = next(p for p in result["points"] if p["threshold"] == 80)
        self.assertEqual(point["side_used"], "YES")
        self.assertAlmostEqual(point["bid"], 0.70)
        self.assertAlmostEqual(point["ask"], 0.72)

    def test_yes_less_than_or_equal_uses_no_book_for_strict_greater_tail(self):
        row = self.aligned["rows"][0]
        row["pm"]["event_relation"] = "<="
        result = derive_digital_curve({
            **self.aligned,
            "rows": [row, {**self.aligned["rows"][1], "pm": {
                **self.aligned["rows"][1]["pm"], "event_relation": "<="
            }}],
        })
        point = result["points"][0]
        self.assertEqual(point["side_used"], "NO")
        self.assertAlmostEqual(point["bid"], 0.28)
        self.assertAlmostEqual(point["ask"], 0.30)
        self.assertTrue(point["complement_check"]["intervals_overlap"])
        self.assertEqual(point["quote_status"], "usable")

    def test_inclusive_and_less_than_rules_are_flagged_for_equality_ambiguity(self):
        row = self.aligned["rows"][0]
        row["pm"]["event_relation"] = ">="
        result = derive_digital_curve({**self.aligned, "rows": [row]})
        point = result["points"][0]
        self.assertIn("equality_mass_ambiguity", point["quality_flags"])
        self.assertEqual(point["quote_status"], "excluded")

    def test_nonoverlapping_yes_no_intervals_are_visible_and_excluded(self):
        row = self.aligned["rows"][0]
        row["pm"]["no_bid"], row["pm"]["no_ask"] = 0.10, 0.15
        result = derive_digital_curve({**self.aligned, "rows": [row]})
        point = result["points"][0]
        self.assertFalse(point["complement_check"]["intervals_overlap"])
        self.assertIn("yes_no_complement_nonoverlap", point["quality_flags"])
        self.assertEqual(point["quote_status"], "excluded")

    def test_nonmonotone_curve_is_reported_without_smoothing(self):
        rows = []
        for threshold, bid, ask in [(80, .25, .30), (100, .55, .60), (120, .15, .20)]:
            pm = {
                "contract_id": f"SYN-{threshold}", "threshold": threshold,
                "payout": 1, "yes_bid": bid, "yes_ask": ask,
                "no_bid": 1-ask, "no_ask": 1-bid, "event_relation": ">",
                "underlying": "SYNTH", "expiry": "T",
                "settlement_reference": "CLOSE", "observation_time": "16:00",
                "quote_timestamp": "2026-11-25T16:00:00Z",
            }
            rows.append({"alignment_status": "matched", "pm_quality_flags": [],
                         "listed_chain_quality_flags": [], "pm": pm})
        result = derive_digital_curve({"schema_version":"options.aligned_inputs.v1",
            "fixture_status":"synthetic","snapshot_time":"2026-11-25T16:00:00Z","rows":rows})
        self.assertFalse(result["curve_diagnostics"]["bid_curve_nonincreasing"])
        self.assertFalse(result["curve_diagnostics"]["curve_suitable_for_option_transformation"])
        self.assertEqual([p["bid"] for p in result["points"]], [.25,.55,.15])

    def test_rights_blocker_is_propagated_without_points(self):
        result = derive_digital_curve({"schema_version":"options.aligned_inputs.v1",
            "fixture_status":"real","status":"blocked_source_rights","real_data_enabled":False,"rows":[]})
        self.assertEqual(result["status"], "blocked_source_rights")
        self.assertEqual(result["points"], [])

    def test_curve_can_feed_synthetic_call_integrator(self):
        from research.options.reconstruct_calls import reconstruct_calls
        digital = derive_digital_curve(self.aligned)
        digital["points"] = [p for p in digital["points"] if p["quote_status"] == "usable"]
        digital["tail"] = {"cap": 130, "scenarios": [{"name":"zero","remaining_fraction":0}]}
        result = reconstruct_calls(digital)
        self.assertEqual(result["fixture_status"], "synthetic")
        self.assertEqual(len(result["results"]), 3)


if __name__ == "__main__":
    unittest.main()
