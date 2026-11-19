import unittest

from weather.research.settlement import outcome_join_eligible, validate_mapping


def synthetic_mapping(**overrides):
    value = {
        "event_key": "synthetic-event-1",
        "family": "temperature",
        "variable": "daily_high",
        "unit": "C",
        "spatial_support_type": "station",
        "spatial_support_ref": "synthetic-station-1",
        "timezone": "America/New_York",
        "valid_start": "2026-01-01T00:00:00-05:00",
        "valid_end": "2026-01-02T00:00:00-05:00",
        "resolution_authority": "synthetic-authority",
        "resolution_source": "synthetic-observation",
        "settlement_rule": "synthetic inclusive threshold",
        "rule_version": "fixture-v1",
        "mapping_status": "verified",
        "source_use_status": "approved",
        "source_use_evidence_ref": "synthetic-approval-v1",
        "reviewer_ref": "synthetic-reviewer-1",
        "evidence_ref": "synthetic-rule-v1",
    }
    value.update(overrides)
    return value


class SettlementMappingTests(unittest.TestCase):
    def test_complete_synthetic_mapping_is_valid_and_joinable(self):
        value = synthetic_mapping()
        self.assertEqual([], validate_mapping(value))
        self.assertTrue(outcome_join_eligible(value))

    def test_missing_unit_and_rule_version_are_rejected(self):
        value = synthetic_mapping(unit="", rule_version="")
        errors = validate_mapping(value)
        self.assertIn("missing required field: unit", errors)
        self.assertIn("missing required field: rule_version", errors)

    def test_invalid_timezone_and_reversed_window_are_rejected(self):
        value = synthetic_mapping(
            timezone="Mars/Olympus",
            valid_start="2026-01-02T00:00:00Z",
            valid_end="2026-01-01T00:00:00Z",
        )
        errors = validate_mapping(value)
        self.assertIn("timezone must be a valid IANA timezone", errors)
        self.assertIn("valid_end must be later than valid_start", errors)

    def test_ambiguous_mapping_needs_reason_and_cannot_join(self):
        value = synthetic_mapping(mapping_status="ambiguous")
        self.assertIn("ambiguous mappings require ambiguity_reason", validate_mapping(value))
        self.assertFalse(outcome_join_eligible(value))

    def test_verified_mapping_needs_second_person_and_evidence(self):
        value = synthetic_mapping(reviewer_ref="", evidence_ref="")
        errors = validate_mapping(value)
        self.assertIn("verified mappings require reviewer_ref", errors)
        self.assertIn("verified mappings require evidence_ref", errors)

    def test_unapproved_source_cannot_join_even_when_mapping_is_valid(self):
        value = synthetic_mapping(source_use_status="unresolved", source_use_evidence_ref="")
        self.assertEqual([], validate_mapping(value))
        self.assertFalse(outcome_join_eligible(value))


if __name__ == "__main__":
    unittest.main()
