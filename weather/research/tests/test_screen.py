import unittest

from weather.research.screen import screen_candidate, summarize_screen


def policy(**overrides):
    value = {
        "minimum_calibration_events": 20,
        "maximum_log_loss": 0.8,
        "maximum_quote_age_seconds": 120,
        "maximum_spread": 0.1,
        "minimum_net_edge": 0.02,
        "fill_assumption": "displayed top-of-book size only; no queue priority",
    }
    value.update(overrides)
    return value


def candidate(**overrides):
    value = {
        "event_id": "synthetic-event-1",
        "family": "temperature",
        "settlement_rule_ref": "synthetic-rule-v1",
        "model": "synthetic-model",
        "run_id": "synthetic-run-v1",
        "side": "buy_yes",
        "model_yes_probability": 0.72,
        "yes_ask": 0.55,
        "yes_ask_size": 10,
        "no_ask": 0.50,
        "no_ask_size": 10,
        "quote_type": "top_of_book",
        "quote_at": "2026-01-01T11:59:00Z",
        "decision_at": "2026-01-01T12:00:00Z",
        "spread": 0.04,
        "fee_per_unit": 0.01,
        "mapping_status": "verified",
        "alignment_eligible": True,
        "calibration_status": "validated",
        "chronological_holdout": True,
        "calibration_event_count": 30,
        "holdout_log_loss": 0.65,
        "calibration_evidence_ref": "synthetic-calibration-v1",
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-source-approval-v1",
        "held_out_outcome": 1,
    }
    value.update(overrides)
    return value


class PaperScreenTests(unittest.TestCase):
    def test_passes_paper_candidate_with_costs_and_simulated_outcome(self):
        result = screen_candidate(candidate(), policy())
        self.assertTrue(result["eligible_for_paper_review"])
        self.assertEqual("paper_candidate", result["classification"])
        self.assertAlmostEqual(0.16, result["net_edge_per_unit"])
        self.assertAlmostEqual(0.44, result["simulated_pnl_per_unit"])
        self.assertFalse(result["live_execution"])

    def test_no_ask_size_freshness_or_source_gate_blocks_candidate(self):
        result = screen_candidate(candidate(yes_ask_size=0, quote_at="2026-01-01T11:00:00Z",
                                           source_use_status="unresolved"), policy())
        self.assertFalse(result["eligible_for_paper_review"])
        self.assertIn("displayed_ask_size_missing", result["reasons"])
        self.assertIn("quote_stale_or_time_invalid", result["reasons"])
        self.assertIn("source_use_unapproved", result["reasons"])

    def test_rejects_missing_calibration_costs_and_bad_settlement_evidence(self):
        result = screen_candidate(candidate(calibration_event_count=None, fee_per_unit=None,
                                            settlement_rule_ref="", chronological_holdout=False), policy())
        self.assertIn("insufficient_calibration_events", result["reasons"])
        self.assertIn("fee_missing", result["reasons"])
        self.assertIn("settlement_rule_reference_missing", result["reasons"])
        self.assertIn("held_out_calibration_not_validated", result["reasons"])

    def test_buy_no_uses_no_price_and_binary_outcome(self):
        result = screen_candidate(candidate(side="buy_no", model_yes_probability=0.2,
                                            held_out_outcome=0), policy())
        self.assertAlmostEqual(0.8 - 0.5 - 0.01, result["net_edge_per_unit"])
        self.assertAlmostEqual(1 - 0.5 - 0.01, result["simulated_pnl_per_unit"])

    def test_summary_counts_candidates_and_outcomes_without_live_execution_claim(self):
        rows = [screen_candidate(candidate(), policy()),
                screen_candidate(candidate(event_id="synthetic-event-2", holdout_log_loss=1.2), policy())]
        result = summarize_screen(rows)
        self.assertEqual((2, 1, 1, 1), (result["candidate_count"], result["eligible_candidate_count"],
                                         result["eligible_event_count"], result["simulated_outcome_count"]))
        self.assertEqual("paper_research_only_no_live_execution", result["interpretation"])


if __name__ == "__main__":
    unittest.main()
