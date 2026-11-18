"""Regression tests for manifest structure and source-use gates."""

import copy
import json
import unittest
from pathlib import Path

from validate_manifest import ManifestError, validate


FIXTURE = Path(__file__).with_name("manifest.example.json")


class ManifestValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.example = json.loads(FIXTURE.read_text(encoding="utf-8"))

    def test_synthetic_example_passes(self):
        validate(copy.deepcopy(self.example))

    def test_bad_utc_timestamp_rejected(self):
        value = copy.deepcopy(self.example)
        value["collected_at_utc"] = "2026-11-18T00:00:00-05:00"
        with self.assertRaisesRegex(ManifestError, "ending in Z"):
            validate(value)

    def test_bad_checksum_rejected(self):
        value = copy.deepcopy(self.example)
        value["artifact"]["sha256"] = "not-a-checksum"
        with self.assertRaisesRegex(ManifestError, "64 lowercase hexadecimal"):
            validate(value)

    def test_real_source_with_unapproved_rights_rejected(self):
        value = copy.deepcopy(self.example)
        value["synthetic_fixture"] = False
        value["source"]["provider"] = "example-venue"
        value["rights"]["raw_storage"] = "blocked"
        with self.assertRaisesRegex(ManifestError, "all required rights must be approved"):
            validate(value)

    def test_event_coverage_order_rejected(self):
        value = copy.deepcopy(self.example)
        value["event_time_start_utc"] = "2026-11-19T00:00:00Z"
        with self.assertRaisesRegex(ManifestError, "ends before it starts"):
            validate(value)


if __name__ == "__main__":
    unittest.main()
