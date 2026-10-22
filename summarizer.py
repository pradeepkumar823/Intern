"""
Section 2: Core Data Processing Task
Device Log Summarizer CLI tool for reading telemetry logs, grouping statistics,
filtering anomalies, and exporting structured JSON and terminal tables.
"""

import argparse
import csv
import json
import os
import sys
from collections import defaultdict
from typing import Any, Dict, List, Optional, Tuple


def process_telemetry(
    file_path: str,
    temp_threshold: float = 80.0
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Ingests and processes device telemetry CSV records.

    Args:
        file_path (str): Path to the telemetry CSV file.
        temp_threshold (float): Maximum allowed average temperature (default: 80.0).

    Returns:
        Tuple[List[Dict[str, Any]], Dict[str, Any]]:
            - filtered_results: List of device summary dictionaries that pass the threshold.
            - all_device_stats: Complete computed stats for all devices before filtering.

    Raises:
        FileNotFoundError: If the CSV file does not exist.
        ValueError: If the file is completely empty or missing required columns.
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Telemetry file not found: '{file_path}'")

    # Tracking metrics per device_id: list of temperatures and count of ERROR statuses
    telemetry_data = defaultdict(lambda: {"temperatures": [], "error_count": 0, "total_records": 0})

    with open(file_path, mode="r", encoding="utf-8", newline="") as csvfile:
        reader = csv.DictReader(csvfile)

        # Validate headers
        if reader.fieldnames is None:
            raise ValueError(f"File '{file_path}' is empty.")

        required_columns = {"device_id", "status", "temperature"}
        actual_columns = {col.strip() for col in reader.fieldnames if col}
        if not required_columns.issubset(actual_columns):
            missing = required_columns - actual_columns
            raise ValueError(f"CSV missing required columns: {', '.join(missing)}")

        line_num = 1
        for row in reader:
            line_num += 1
            device_id = row.get("device_id", "").strip()
            status = row.get("status", "").strip().upper()
            raw_temp = row.get("temperature", "").strip()

            # Robustness: Skip empty or corrupt device IDs
            if not device_id:
                continue

            # Robustness: Try converting temperature to float
            try:
                temp_val = float(raw_temp)
            except (ValueError, TypeError):
                # Malformed temperature row, skipped to ensure robustness
                continue

            entry = telemetry_data[device_id]
            entry["total_records"] += 1
            entry["temperatures"].append(temp_val)
            if status == "ERROR":
                entry["error_count"] += 1

    all_stats: Dict[str, Any] = {}
    filtered_results: List[Dict[str, Any]] = []

    for device_id, stats in sorted(telemetry_data.items()):
        total = stats["total_records"]
        temps = stats["temperatures"]
        avg_temp = round(sum(temps) / total, 2) if total > 0 else 0.0
        errors = stats["error_count"]

        device_summary = {
            "device_id": device_id,
            "total_records": total,
            "average_temperature": avg_temp,
            "error_count": errors
        }

        all_stats[device_id] = device_summary

        # Requirement 3: Filter out any devices where average temperature > 80.0
        if avg_temp <= temp_threshold:
            filtered_results.append(device_summary)

    return filtered_results, all_stats


def export_json(data: List[Dict[str, Any]], output_path: str) -> None:
    """Exports structured data to a clean, formatted JSON file."""
    with open(output_path, mode="w", encoding="utf-8") as jsonfile:
        json.dump(data, jsonfile, indent=4)


def print_summary_table(
    filtered_data: List[Dict[str, Any]],
    all_data: Dict[str, Any],
    threshold: float
) -> None:
    """Prints a clean ASCII summary table to the terminal."""
    print("\n" + "=" * 68)
    print("           DEVICE TELEMETRY AGGREGATION SUMMARY")
    print("=" * 68)
    print(f"{'Device ID':<12} | {'Total Records':<14} | {'Avg Temp (C)':<14} | {'Errors':<8} | {'Status':<10}")
    print("-" * 68)

    for device_id, stats in all_data.items():
        avg = stats["average_temperature"]
        is_retained = avg <= threshold
        status_label = "RETAINED" if is_retained else f"EXCLUDED (>{threshold} C)"

        print(
            f"{device_id:<12} | "
            f"{stats['total_records']:<14} | "
            f"{avg:<14.2f} | "
            f"{stats['error_count']:<8} | "
            f"{status_label:<10}"
        )

    print("=" * 68)
    print(f"Summary: {len(filtered_data)} retained / {len(all_data)} total devices (Threshold: <= {threshold} C)\n")


def main() -> None:
    """CLI entry point for Device Log Summarizer."""
    parser = argparse.ArgumentParser(
        description="Device Log Summarizer CLI: Ingests telemetry CSV, aggregates stats, and exports JSON."
    )
    parser.add_argument(
        "--input", "-i",
        default="device_telemetry.csv",
        help="Path to input CSV file (default: device_telemetry.csv)"
    )
    parser.add_argument(
        "--output", "-o",
        default="output_summary.json",
        help="Path to output JSON file (default: output_summary.json)"
    )
    parser.add_argument(
        "--threshold", "-t",
        type=float,
        default=80.0,
        help="Maximum average temperature threshold for filtering (default: 80.0)"
    )

    args = parser.parse_args()

    try:
        filtered_results, all_stats = process_telemetry(args.input, args.threshold)
        export_json(filtered_results, args.output)
        print_summary_table(filtered_results, all_stats, args.threshold)
        print(f" [SUCCESS] Exported {len(filtered_results)} records to '{args.output}'")
    except Exception as exc:
        print(f" [ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
