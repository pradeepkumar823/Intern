"""
Comprehensive End-to-End Test Suite for Device Log Summarizer.
Tests 4 distinct scenarios:
1. Standard telemetry processing & filtering (> 80.0 C).
2. Missing file error handling.
3. Empty CSV and zero-division protection.
4. Corrupted CSV rows (malformed floats, missing columns, empty fields).
"""

import os
import tempfile
import unittest
from sanitization import clean_sensor_readings
from summarizer import process_telemetry, export_json


class TestDeviceLogSummarizer(unittest.TestCase):

    def test_scenario_1_standard_dataset(self):
        """Scenario 1: Normal dataset with mixed statuses and temperatures."""
        filtered, all_stats = process_telemetry("device_telemetry.csv", temp_threshold=80.0)

        # Check all 5 devices were parsed
        self.assertEqual(len(all_stats), 5)
        self.assertIn("DEV_A", all_stats)
        self.assertIn("DEV_B", all_stats)
        self.assertIn("DEV_C", all_stats)
        self.assertIn("DEV_D", all_stats)
        self.assertIn("DEV_E", all_stats)

        # Check filtering: DEV_C (86.0) and DEV_E (82.23) exceed 80.0
        retained_ids = [d["device_id"] for d in filtered]
        self.assertEqual(retained_ids, ["DEV_A", "DEV_B", "DEV_D"])

        # Check error count for DEV_B (2 errors in dataset)
        self.assertEqual(all_stats["DEV_B"]["error_count"], 2)

    def test_scenario_2_missing_file_handling(self):
        """Scenario 2: System must gracefully raise FileNotFoundError if CSV is missing."""
        with self.assertRaises(FileNotFoundError):
            process_telemetry("non_existent_file_xyz.csv")

    def test_scenario_3_empty_csv(self):
        """Scenario 3: Header-only CSV must not trigger ZeroDivisionError."""
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp.write("device_id,status,temperature\n")
            tmp_path = tmp.name

        try:
            filtered, all_stats = process_telemetry(tmp_path)
            self.assertEqual(filtered, [])
            self.assertEqual(all_stats, {})
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_scenario_4_corrupted_rows(self):
        """Scenario 4: CSV with malformed rows, invalid strings, and missing IDs."""
        csv_content = (
            "device_id,status,temperature\n"
            "DEV_VALID,ACTIVE,50.0\n"
            ",ACTIVE,60.0\n"               # Missing device_id
            "DEV_VALID,ERROR,bad_temp\n"    # Invalid float temperature
            "DEV_VALID,ERROR,55.0\n"        # Valid row
            "DEV_OVERHEAT,ACTIVE,95.0\n"    # Above threshold
        )
        with tempfile.NamedTemporaryFile("w+", delete=False, suffix=".csv") as tmp:
            tmp.write(csv_content)
            tmp_path = tmp.name

        try:
            filtered, all_stats = process_telemetry(tmp_path, temp_threshold=80.0)

            # DEV_VALID has 2 valid rows (50.0, 55.0) -> avg: 52.5, errors: 1
            self.assertIn("DEV_VALID", all_stats)
            self.assertEqual(all_stats["DEV_VALID"]["total_records"], 2)
            self.assertEqual(all_stats["DEV_VALID"]["average_temperature"], 52.5)
            self.assertEqual(all_stats["DEV_VALID"]["error_count"], 1)

            # DEV_OVERHEAT has avg: 95.0, so it must be excluded
            self.assertEqual(len(filtered), 1)
            self.assertEqual(filtered[0]["device_id"], "DEV_VALID")
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main(verbosity=2)
