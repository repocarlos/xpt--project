from __future__ import annotations

import copy
import json
import tempfile
import unittest
from pathlib import Path

import duckdb

from research.options.record_fixture import main, validate_fixture, verify_manifest, write_fixture


FIXTURE = Path(__file__).parents[1] / "fixtures" / "recorder_fixture_v1.json"


class FixtureRecorderTests(unittest.TestCase):
    def setUp(self) -> None:
        self.document = json.loads(FIXTURE.read_text(encoding="utf-8"))
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.output_root = Path(self.temp.name) / "out"

    def test_writes_queryable_parquet_and_manifest_checksums(self) -> None:
        dataset_dir, manifest = write_fixture(self.document, self.output_root)
        self.assertEqual(manifest["record_count"], 2)
        self.assertEqual(manifest["duplicates_removed"], 1)
        self.assertTrue(verify_manifest(dataset_dir))
        self.assertTrue(all("venue=" in entry["path"] and "date=" in entry["path"] and "market=" in entry["path"]
                            for entry in manifest["files"]))
        glob = (dataset_dir / "**" / "*.parquet").as_posix()
        count = duckdb.connect().execute("SELECT count(*) FROM read_parquet(?)", [glob]).fetchone()[0]
        self.assertEqual(count, 2)
        self.assertEqual(manifest["source_rights"]["live_collection"], "blocked_unresolved_source_approval")

    def test_rerun_replaces_synthetic_dataset_without_appending(self) -> None:
        first_dir, first = write_fixture(self.document, self.output_root)
        second_dir, second = write_fixture(self.document, self.output_root)
        self.assertEqual(first_dir, second_dir)
        self.assertEqual(first["dataset_id"], second["dataset_id"])
        self.assertEqual(first["logical_records_sha256"], second["logical_records_sha256"])
        self.assertEqual(second["record_count"], 2)
        self.assertTrue(verify_manifest(second_dir))

    def test_observed_input_rejected_before_output_is_created(self) -> None:
        observed = copy.deepcopy(self.document)
        observed["fixture_status"] = "observed"
        with self.assertRaisesRegex(ValueError, "observed data is blocked"):
            write_fixture(observed, self.output_root)
        self.assertFalse(self.output_root.exists())

    def test_live_mode_refused_without_creating_output(self) -> None:
        result = main(["--live", "--output-root", str(self.output_root)])
        self.assertEqual(result, 2)
        self.assertFalse(self.output_root.exists())

    def test_conflicting_record_id_is_rejected(self) -> None:
        conflict = copy.deepcopy(self.document)
        conflict["records"][2]["ask"] = 0.49
        with self.assertRaisesRegex(ValueError, "reused for conflicting records"):
            validate_fixture(conflict)

    def test_bid_above_ask_is_rejected(self) -> None:
        invalid = copy.deepcopy(self.document)
        invalid["records"][0]["bid"] = 0.50
        with self.assertRaisesRegex(ValueError, "0 <= bid <= ask"):
            validate_fixture(invalid)


if __name__ == "__main__":
    unittest.main()
