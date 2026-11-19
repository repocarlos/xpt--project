import unittest

from weather.research.coverage import build_coverage_report


def synthetic_summary(**overrides):
    row = {
        "family": "rain_snow",
        "data_tier": "1_candles",
        "expected_count": 10,
        "observed_count": 8,
        "coverage_start": "2024-01-01",
        "coverage_end": "2025-12-31",
        "forecast_vintage_count": 6,
        "outcome_count": 8,
        "quote_count": 8,
        "estimated_bytes": 2048,
        "capture_mode": "backfill",
        "retention_days": 90,
        "source_use_status": "approved",
        "approval_evidence_ref": "synthetic-approval-v1",
        "evidence_ref": "synthetic-manifest-v1",
    }
    row.update(overrides)
    return row


class CoverageTests(unittest.TestCase):
    def test_groups_by_family_and_tier_and_uses_explicit_denominators(self):
        rows = build_coverage_report([
            synthetic_summary(),
            synthetic_summary(expected_count=5, observed_count=5, capture_mode="prospective"),
            synthetic_summary(family="wind", data_tier="0_metadata"),
        ])
        self.assertEqual(2, len(rows))
        rain = rows[0]
        self.assertEqual(15, rain["expected_count"])
        self.assertEqual(13, rain["observed_count"])
        self.assertAlmostEqual(13 / 15, rain["coverage_fraction"])
        self.assertEqual(1, rain["backfill_summary_count"])
        self.assertEqual(1, rain["prospective_summary_count"])

    def test_missing_denominator_is_unknown_not_zero(self):
        report = build_coverage_report([synthetic_summary(expected_count=None)])
        self.assertIsNone(report[0]["expected_count"])
        self.assertIsNone(report[0]["coverage_fraction"])
        self.assertEqual("limited", report[0]["status"])

    def test_unresolved_rights_block_even_complete_coverage(self):
        report = build_coverage_report([synthetic_summary(
            expected_count=8,
            source_use_status="unresolved",
            approval_evidence_ref="",
        )])
        self.assertEqual("blocked_on_rights", report[0]["status"])

    def test_rejects_observed_count_above_denominator(self):
        with self.assertRaises(ValueError):
            build_coverage_report([synthetic_summary(expected_count=4, observed_count=5)])


if __name__ == "__main__":
    unittest.main()
