import unittest

from weather.research.handoff import validate_handoff


def handoff(**overrides):
    value = {
        "question": "Synthetic template check",
        "period": "pending",
        "family_scopes": [{"family": "temperature", "status": "selected"}],
        "settlement": {"status": "pending"},
        "coverage": {"status": "pending"},
        "comparisons": [{"evidence_class": "candidate_gap", "claim_status": "synthetic",
                         "source_use_status": "unresolved"}],
        "uncertainty": {"status": "pending"},
        "costs": {"status": "pending"},
        "storage": {"status": "pending"},
        "limitations": ["No source approval or empirical data"],
        "deferred_families": [{"family": "tropical_cyclone", "evidence_needed": "approved archive and settlement mapping"}],
        "reproducibility_refs": ["synthetic-fixture-v1"],
        "recommendation": "revise",
        "source_use_status": "unresolved",
    }
    value.update(overrides)
    return value


class HandoffTests(unittest.TestCase):
    def test_pending_synthetic_handoff_is_valid(self):
        self.assertEqual([], validate_handoff(handoff()))

    def test_rejects_validated_claim_without_evidence_or_approval(self):
        errors = validate_handoff(handoff(comparisons=[{"evidence_class": "held_out_result",
                                                       "claim_status": "validated",
                                                       "source_use_status": "unresolved"}]))
        self.assertTrue(any("validation_evidence_ref" in error for error in errors))
        self.assertTrue(any("source approval" in error for error in errors))

    def test_deferred_family_must_state_evidence_to_add(self):
        errors = validate_handoff(handoff(deferred_families=[{"family": "wind"}]))
        self.assertTrue(any("evidence_needed" in error for error in errors))

    def test_weather_metrics_cannot_be_forced_into_cross_sector_score(self):
        errors = validate_handoff(handoff(cross_sector_score=0.73))
        self.assertIn("Weather handoff must not force metrics into a cross-sector score", errors)


if __name__ == "__main__":
    unittest.main()
