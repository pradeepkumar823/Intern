"""
Section 1: Coding Logic & Sanitization
Module for cleaning and normalizing noisy IoT sensor readings.
"""

from typing import Any, List
import unittest


def clean_sensor_readings(readings: Any) -> List[float]:
    """
    Cleans and normalizes a list of mixed-type sensor readings.

    Processing Steps:
    1. Type Conversion & Filtering:
       - Converts elements to float where possible.
       - Rejects booleans (since bool is a subclass of int in Python).
       - Drops values that cannot be converted, are None, or are negative (< 0).
    2. Clipping:
       - If any valid float exceeds 500.0, limits it to 500.0.
    3. Edge Case Handling:
       - Handles None input, empty lists, or lists containing only invalid values gracefully.

    Args:
        readings (list): Raw list of mixed sensor readings.

    Returns:
        List[float]: Cleaned, filtered, and clipped float values.
    """
    if not isinstance(readings, (list, tuple)):
        return []

    cleaned: List[float] = []

    for item in readings:
        # Ignore None and booleans (e.g. True/False which cast to 1.0/0.0 in Python)
        if item is None or isinstance(item, bool):
            continue

        try:
            val = float(item)
        except (ValueError, TypeError):
            # Element cannot be converted to float
            continue

        # Drop negative error flags (< 0)
        if val < 0.0:
            continue

        # Clipping: cap at 500.0 if value exceeds 500.0
        if val > 500.0:
            val = 500.0

        cleaned.append(val)

    return cleaned


class TestCleanSensorReadings(unittest.TestCase):
    """Unit test suite verifying all edge cases and rules for clean_sensor_readings."""

    def test_standard_mixed_input(self):
        """Test with typical mixed input containing valid numbers, strings, negatives, and None."""
        raw_input = [12.5, "45.0", -1, None, "error", 250.75]
        expected = [12.5, 45.0, 250.75]
        self.assertEqual(clean_sensor_readings(raw_input), expected)

    def test_boundary_clipping(self):
        """Test that values > 500.0 are capped at 500.0, and 500.0 itself is preserved."""
        raw_input = [500.0, 500.1, 1000.0, "999.99", 499.9]
        expected = [500.0, 500.0, 500.0, 500.0, 499.9]
        self.assertEqual(clean_sensor_readings(raw_input), expected)

    def test_negative_values_and_error_flags(self):
        """Test that negative numbers (hardware error codes like -1, -999) are dropped."""
        raw_input = [-0.01, -1, -999, "-50.5", 0.0]
        expected = [0.0]  # 0.0 is not negative (< 0), so it is kept
        self.assertEqual(clean_sensor_readings(raw_input), expected)

    def test_empty_and_none_input(self):
        """Test graceful handling of empty list, None, and non-iterable input."""
        self.assertEqual(clean_sensor_readings([]), [])
        self.assertEqual(clean_sensor_readings(None), [])
        self.assertEqual(clean_sensor_readings(12345), [])

    def test_all_invalid_entries(self):
        """Test list containing only invalid types (strings, None, booleans, negatives)."""
        raw_input = ["corrupt", None, -5, True, False, "N/A", object()]
        self.assertEqual(clean_sensor_readings(raw_input), [])

    def test_boolean_rejection(self):
        """Ensure Python booleans True/False are not converted to 1.0/0.0."""
        raw_input = [True, False, 15.0]
        self.assertEqual(clean_sensor_readings(raw_input), [15.0])

    def test_my_own_case(self):
        sample = [100.0, "300.5", -5, 999.0]
        result = clean_sensor_readings(sample)
        self.assertEqual(result, [100.0, 300.5, 500.0])



if __name__ == "__main__":
    unittest.main(verbosity=2)
