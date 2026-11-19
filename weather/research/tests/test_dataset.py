import tempfile
import unittest
from pathlib import Path

import pyarrow.parquet as pq

from weather.research.dataset import build_manifest, normalize_batch, write_parquet_partition


def synthetic_approval(**overrides):
    value = {
        "status": "approved",
        "approval_ref": "synthetic-approval-v1",
        "permitted_uses": ["internal_analysis", "retain_normalized"],
    }
    value.update(overrides)
    return value


def synthetic_row(**overrides):
    row = {
        "record_key": "synthetic-event-1",
        "record_type": "event",
        "family": "temperature",
        "event_key": "synthetic-event-1",
        "observed_at_utc": "2026-01-01T12:00:00-05:00",
        "source_use_status": "approved",
        "source_record_id": "source-secret-id",
    }
    row.update(overrides)
    return row


class DatasetTests(unittest.TestCase):
    def test_unapproved_source_fails_before_lazy_input_is_touched(self):
        def unopened():
            raise AssertionError("input iterator touched before approval")
            yield {}

        with self.assertRaises(PermissionError):
            normalize_batch(unopened(), approval=synthetic_approval(status="unresolved"), manifest_id="m1")

    def test_normalization_is_stable_and_drops_unpermitted_source_id(self):
        rows = normalize_batch(
            [synthetic_row(), synthetic_row()],
            approval=synthetic_approval(),
            manifest_id="manifest-1",
        )
        self.assertEqual(1, len(rows))
        self.assertEqual("2026-01-01T17:00:00Z", rows[0]["observed_at_utc"])
        self.assertNotIn("source_record_id", rows[0])
        self.assertEqual("manifest-1", rows[0]["manifest_id"])

    def test_conflicting_duplicate_and_record_permission_are_rejected(self):
        with self.assertRaises(ValueError):
            normalize_batch(
                [synthetic_row(), synthetic_row(family="wind")],
                approval=synthetic_approval(), manifest_id="m1",
            )
        with self.assertRaises(PermissionError):
            normalize_batch([synthetic_row(source_use_status="unresolved")], approval=synthetic_approval(), manifest_id="m1")

    def test_manifest_and_parquet_roundtrip_are_reproducible(self):
        approval = synthetic_approval()
        rows = normalize_batch([synthetic_row()], approval=approval, manifest_id="manifest-1")
        manifest = build_manifest(
            rows, approval=approval, manifest_id="manifest-1",
            retrieved_at_utc="2026-01-02T00:00:00Z", retention_until="2027-01-02T00:00:00Z",
        )
        self.assertEqual(1, manifest["row_count"])
        self.assertFalse(manifest["payload_included"])
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "source=synthetic/family=temperature/year=2026/part-000.parquet"
            partition = write_parquet_partition(rows, path, approval)
            restored = pq.read_table(path).to_pylist()
            self.assertEqual(partition["row_count"], len(restored))
            self.assertEqual(rows[0]["record_key"], restored[0]["record_key"])
            self.assertGreater(partition["byte_count"], 0)


if __name__ == "__main__":
    unittest.main()
