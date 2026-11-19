import unittest

from weather.research.source_registry import can_inspect_raw_rows, validate_source_register


def row(use, **overrides):
    value = {
        "candidate_ref": "synthetic-source-1",
        "family": "temperature",
        "venue_or_source_type": "synthetic-market-source",
        "geography": "synthetic-location",
        "data_tier": "0_metadata",
        "intended_use": use,
        "use_status": "approved",
        "approval_evidence_ref": "synthetic-approval-v1",
        "coverage_status": "unknown",
    }
    if use == "raw_retention":
        value["retention_until"] = "2027-01-01T00:00:00Z"
    value.update(overrides)
    return value


class SourceRegistryTests(unittest.TestCase):
    def test_inventory_accepts_synthetic_per_use_records(self):
        register = {"source_uses": [row("access"), row("internal_analysis"), row("raw_retention")],
                    "raw_inspection_allowed": False, "second_reviewer": {}}
        self.assertEqual([], validate_source_register(register))
        self.assertFalse(can_inspect_raw_rows(register))

    def test_approved_use_requires_evidence_and_retention_expiry(self):
        errors = validate_source_register({"source_uses": [
            row("access", approval_evidence_ref=""),
            row("normalized_retention", retention_until=""),
        ]})
        self.assertTrue(any("approval_evidence_ref" in error for error in errors))
        self.assertTrue(any("retention_until" in error for error in errors))

    def test_coverage_claim_requires_provenance_and_estimate_assumptions(self):
        errors = validate_source_register({"source_uses": [row("access", coverage_status="claimed",
                                                               estimated_bytes=100)]})
        self.assertTrue(any("coverage requires evidence" in error for error in errors))
        self.assertTrue(any("volume estimate" in error for error in errors))

    def test_raw_inspection_needs_all_use_approvals_and_second_reviewer(self):
        register = {"source_uses": [row("access"), row("internal_analysis"), row("raw_retention")],
                    "raw_inspection_allowed": True,
                    "second_reviewer": {"weather_qualified": True, "reviewer_ref": "synthetic-reviewer",
                                        "qualification_evidence_ref": "synthetic-qualification"}}
        self.assertTrue(can_inspect_raw_rows(register))
        register["source_uses"].pop()
        self.assertFalse(can_inspect_raw_rows(register))

    def test_duplicate_rows_and_unqualified_reviewer_block_inspection(self):
        register = {"source_uses": [row("access"), row("access")], "raw_inspection_allowed": True,
                    "second_reviewer": {"weather_qualified": False}}
        errors = validate_source_register(register)
        self.assertTrue(any("duplicates" in error for error in errors))
        self.assertFalse(can_inspect_raw_rows(register))


if __name__ == "__main__":
    unittest.main()
