import copy
import json
import unittest
from pathlib import Path

from validate_options_study import validate_snapshot


HERE = Path(__file__).parent


class OptionsStudyContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.fixture = json.loads((HERE / "examples/options-study.synthetic.json").read_text(encoding="utf-8"))

    def test_synthetic_fixture_has_all_record_layers_and_passes_gate(self):
        self.assertTrue(validate_snapshot(self.fixture, ["raw_storage", "derived_data"]))
        self.assertEqual(
            {record["record_type"] for record in self.fixture["records"]},
            {"pm_threshold_quote", "listed_option_quote", "normalized_match", "derived_estimate"},
        )

    def test_observed_data_with_unresolved_storage_is_rejected(self):
        sample = copy.deepcopy(self.fixture)
        sample["synthetic_fixture"] = False
        sample["manifest"]["synthetic_fixture"] = False
        record = sample["records"][0]
        record["data_status"] = "observed"
        record["source"]["rights"]["access"] = "approved"
        record["source"]["rights"]["raw_storage"] = "unresolved"
        with self.assertRaisesRegex(ValueError, "raw_storage is not approved"):
            validate_snapshot(sample, ["raw_storage"])

    def test_missing_contract_expiry_is_rejected(self):
        sample = copy.deepcopy(self.fixture)
        del sample["records"][0]["expiry"]
        with self.assertRaisesRegex(ValueError, "missing required fields: expiry"):
            validate_snapshot(sample)


if __name__ == "__main__":
    unittest.main()
