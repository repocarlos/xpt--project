import json
import unittest
from pathlib import Path

from research.options.stress_test_surface import render_handoff, run_sensitivity


FIXTURE = Path(__file__).parents[1] / "fixtures" / "sensitivity_v1.json"


class SurfaceStressTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_full_named_scenario_grid_is_generated(self):
        result = run_sensitivity(self.document)
        self.assertEqual(result["scenario_count"], 144)
        self.assertTrue(all(s["expiry"] for s in result["scenarios"]))

    def test_quote_interpolation_and_tail_assumptions_change_call_values(self):
        result = run_sensitivity(self.document)
        def find(quote, interpolation, tail):
            return next(s for s in result["scenarios"]
                if s["expiry"] == "2027-03-19"
                and s["assumptions"]["quote_side"] == quote
                and s["assumptions"]["interpolation_method"] == interpolation
                and s["assumptions"]["tail_scenario"] == tail
                and s["assumptions"]["discount_mode"] == "apply_discount_factor")
        base = find("mid", "piecewise_linear", "zero_at_cap")["synthetic_calls"][0]["total_lower"]
        other = find("ask", "right_step", "held_to_cap")["synthetic_calls"][0]["total_lower"]
        self.assertNotAlmostEqual(base, other)

    def test_omitting_discount_factor_blocks_iv_comparison(self):
        result = run_sensitivity(self.document)
        scenario = next(s for s in result["scenarios"]
            if s["assumptions"]["discount_mode"] == "no_discount_factor")
        self.assertTrue(all(r["status"] == "invalid_pm_input" for r in scenario["comparison_rows"]))
        self.assertEqual(scenario["synthetic_calls"][0]["price_basis"], "undiscounted_event_price")

    def test_handoff_separates_synthetic_results_from_empirical_evidence(self):
        result = run_sensitivity(self.document)
        report = render_handoff(result, "python3 stress_test_surface.py input.json")
        self.assertIn("synthetic fixture only", report)
        self.assertIn("stop empirical publication", report)
        self.assertIn("candidate dislocation only", report)
        self.assertIn("No observed PM prices", report)
        self.assertNotIn("proven edge", report.lower())

    def test_real_data_input_is_rejected(self):
        self.document["fixture_status"] = "real"
        with self.assertRaisesRegex(ValueError, "synthetic"):
            run_sensitivity(self.document)


if __name__ == "__main__":
    unittest.main()
