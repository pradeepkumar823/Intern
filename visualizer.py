"""
Section 3: AI Prompting & Charting Challenge
Script to load aggregated telemetry JSON data and render a bar chart
comparing the average temperature per device using matplotlib.
"""

import argparse
import json
import os
import sys
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend suitable for headless scripts/CLI
import matplotlib.pyplot as plt


def generate_temperature_chart(json_path: str, output_image_path: str) -> None:
    """
    Loads JSON telemetry output and generates a bar chart comparing
    average device temperatures.

    Args:
        json_path (str): Path to the input JSON file.
        output_image_path (str): Destination path for the generated chart image.
    """
    if not os.path.exists(json_path):
        raise FileNotFoundError(f"Input JSON file not found: '{json_path}'")

    with open(json_path, mode="r", encoding="utf-8") as f:
        data = json.load(f)

    if not data:
        print("[WARNING] Input JSON is empty. Generating empty chart placeholder.")
        device_ids = []
        avg_temps = []
    else:
        device_ids = [item["device_id"] for item in data]
        avg_temps = [item["average_temperature"] for item in data]

    # Chart Configuration & Aesthetics
    fig, ax = plt.subplots(figsize=(8, 5), dpi=300)

    # Color palette based on temperature level
    colors = ["#2b5c8f" if temp < 50.0 else "#e07a5f" if temp > 70.0 else "#3d85c6" for temp in avg_temps]

    bars = ax.bar(device_ids, avg_temps, color=colors, width=0.5, edgecolor="#1e3d59", linewidth=1.2, zorder=3)

    # Adding values directly above bars for clear readability
    for bar in bars:
        height = bar.get_height()
        ax.annotate(
            f"{height:.2f} °C",
            xy=(bar.get_x() + bar.get_width() / 2, height),
            xytext=(0, 5),  # 5 points vertical offset
            textcoords="offset points",
            ha="center",
            va="bottom",
            fontsize=10,
            fontweight="bold",
            color="#222222"
        )

    # Safety Threshold Line
    ax.axhline(y=80.0, color="#d62828", linestyle="--", linewidth=1.2, label="Max Permitted Threshold (80 °C)", zorder=2)

    # Labels and Titles
    ax.set_title("Average Operating Temperature per Retained Device", fontsize=14, fontweight="bold", pad=15)
    ax.set_xlabel("Device ID", fontsize=11, fontweight="bold", labelpad=8)
    ax.set_ylabel("Average Temperature (°C)", fontsize=11, fontweight="bold", labelpad=8)

    # Y-axis scaling to accommodate labels without clipping
    max_val = max(avg_temps) if avg_temps else 100.0
    ax.set_ylim(0, max(max_val * 1.2, 90.0))

    # Grid and Styling
    ax.grid(axis="y", linestyle=":", alpha=0.6, zorder=1)
    ax.set_axisbelow(True)
    ax.legend(loc="upper right", frameon=True, facecolor="#f8f9fa", edgecolor="#cccccc")

    # Layout Optimization
    plt.tight_layout()

    # Save to file
    plt.savefig(output_image_path, dpi=300)
    plt.close()
    print(f" [SUCCESS] Chart saved successfully to '{output_image_path}'")


def main() -> None:
    """CLI entry point for visualization script."""
    parser = argparse.ArgumentParser(
        description="Visualizer CLI: Generates bar chart from telemetry JSON output using matplotlib."
    )
    parser.add_argument(
        "--input", "-i",
        default="output_summary.json",
        help="Path to input summary JSON file (default: output_summary.json)"
    )
    parser.add_argument(
        "--output", "-o",
        default="temperature_chart.png",
        help="Path to output image file (default: temperature_chart.png)"
    )

    args = parser.parse_args()

    try:
        generate_temperature_chart(args.input, args.output)
    except Exception as exc:
        print(f" [ERROR] {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
