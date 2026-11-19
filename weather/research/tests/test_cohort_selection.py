import unittest

from weather.research.cohort_selection import ready_to_select, validate_selection


def ready_candidate(**overrides):
    row = {
        "cohort_id": "synthetic-wind-cohort-v1",
        "family": "wind_severe",
        "status": "selected",
        "venue": "synthetic-venue",
        "geography": "synthetic-grid",
        "event_horizon": "synthetic-short-range",
        "settlement_observable": "synthetic-gust-threshold",
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-rights-v1",
        "settlement_status": "verified",
        "settlement_evidence_ref": "synthetic-rule-v1",
        "coverage_status": "verified",
        "coverage_evidence_ref": "synthetic-coverage-v1",
        "forecast_match_status": "verified",
        "forecast_evidence_ref": "synthetic-forecast-v1",
        "volume_status": "verified",
        "volume_evidence_ref": "synthetic-volume-v1",
        "volume_assumptions": "Synthetic fixture dimensions only",
        "second_reviewer_qualified": True,
        "second_reviewer_ref": "synthetic-weather-reviewer-v1",
    }
    row.update(overrides)
    return row


class CohortSelectionTests(unittest.TestCase):
    def test_non_city_family_can_be_selected_when_every_gate_passes(self):
        register = {"selection_decision": "select", "cohorts": [ready_candidate()]}
        self.assertEqual([], validate_selection(register))
        self.assertTrue(ready_to_select(register))

    def test_unresolved_permissions_block_candidate_selection(self):
        register = {"selection_decision": "select", "cohorts": [ready_candidate(
            source_use_status="blocked", source_use_evidence_ref="") ]}
        errors = validate_selection(register)
        self.assertTrue(any("approved source use" in error for error in errors))
        self.assertFalse(ready_to_select(register))

    def test_deferred_cohort_requires_reason_and_pending_can_have_no_selected_family(self):
        pending = {"selection_decision": "pending", "cohorts": [
            {"cohort_id": "temperature-candidate-1", "family": "temperature", "status": "candidate"},
            {"cohort_id": "climate-candidate-1", "family": "climate_seasonal", "status": "deferred", "decision_reason": "Needs long-horizon vintage coverage"},
        ]}
        self.assertEqual([], validate_selection(pending))
        bad = {"selection_decision": "pending", "cohorts": [{"cohort_id": "flood-1", "family": "flood", "status": "deferred"}]}
        self.assertTrue(any("decision_reason" in error for error in validate_selection(bad)))

    def test_selected_row_needs_coverage_forecast_volume_and_reviewer(self):
        register = {"selection_decision": "select", "cohorts": [ready_candidate(
            coverage_status="unknown", forecast_evidence_ref="", volume_assumptions="",
            second_reviewer_qualified=False)]}
        errors = validate_selection(register)
        self.assertTrue(any("coverage" in error for error in errors))
        self.assertTrue(any("forecast match" in error for error in errors))
        self.assertTrue(any("volume estimate" in error for error in errors))
        self.assertTrue(any("second reviewer" in error for error in errors))

    def test_no_go_requires_evidence_and_duplicate_family_rows_fail(self):
        register = {"selection_decision": "no_go", "cohorts": [
            {"cohort_id": "precip-1", "family": "precipitation", "status": "candidate"},
            {"cohort_id": "precip-1", "family": "precipitation", "status": "candidate"},
        ]}
        errors = validate_selection(register)
        self.assertTrue(any("decision_evidence_ref" in error for error in errors))
        self.assertTrue(any("duplicate cohort_id" in error for error in errors))


if __name__ == "__main__":
    unittest.main()
