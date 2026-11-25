import json
import unittest
from pathlib import Path

from research.options.align_inputs import _rights_clear, align_inputs


FIXTURE = Path(__file__).parents[1] / "fixtures" / "alignment_v1.json"


class AlignInputsTests(unittest.TestCase):
    def setUp(self):
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_exact_terms_and_quote_timestamps_align(self):
        result = align_inputs(self.document)
        self.assertEqual(result["counts"], {
            "pm_contracts": 5, "matched": 4, "usable_for_curve": 3,
            "unmatched": 1, "unique_usable_listed_quotes": 2,
        })
        self.assertFalse(result["real_data_enabled"])
        first = next(row for row in result["rows"] if row["contract_id"] == "SYN-PM-080")
        self.assertEqual(first["alignment_status"], "matched")
        listed = next(row for row in first["listed_option_chain"] if row["option_id"] == "SYN-OPT-080")
        self.assertAlmostEqual(listed["quote_time_delta_seconds"], 5)

    def test_wide_stale_and_missing_option_rows_are_flagged(self):
        result = align_inputs(self.document)
        rows = {row["contract_id"]: row for row in result["rows"]}
        self.assertIn("stale_pm_quote", rows["SYN-PM-110"]["quality_flags"])
        self.assertIn("wide_listed_spread", rows["SYN-PM-120"]["listed_chain_quality_flags"])
        self.assertFalse(rows["SYN-PM-110"]["usable_for_curve"])
        self.assertEqual(rows["SYN-PM-090"]["alignment_status"], "unmatched_terms")

    def test_settlement_mismatch_does_not_match(self):
        self.document["pm_contracts"][0]["settlement_reference"] = "OTHER_CLOSE"
        result = align_inputs(self.document)
        row = next(r for r in result["rows"] if r["contract_id"] == "SYN-PM-080")
        self.assertEqual(row["alignment_status"], "unmatched_terms")

    def test_unapproved_real_source_returns_blocker_without_rows(self):
        self.document["fixture_status"] = "real"
        result = align_inputs(self.document)
        self.assertEqual(result["status"], "blocked_source_rights")
        self.assertEqual(result["rows"], [])
        self.assertFalse(result["real_data_enabled"])

    def test_all_required_rights_are_checked_without_processing_source_rows(self):
        self.document["source_use_status"] = {
            use: "approved" for use in (
                "collection", "raw_storage", "derivation", "team_sharing", "dashboard_display"
            )
        }
        self.assertTrue(_rights_clear(self.document))
        self.document["source_use_status"]["dashboard_display"] = "unresolved"
        self.assertFalse(_rights_clear(self.document))

    def test_run_is_deterministic(self):
        self.assertEqual(align_inputs(self.document), align_inputs(self.document))


if __name__ == "__main__":
    unittest.main()
