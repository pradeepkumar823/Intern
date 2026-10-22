# Device Log Summarizer CLI Tool

**Technical Assessment — Software Engineering Intern**

> A modular Python pipeline that sanitizes noisy IoT sensor readings, ingests device telemetry from CSV files, aggregates health metrics per device, filters anomalies, and delivers results via JSON export, terminal tables, a static PNG chart, and a live localhost web dashboard.

---

## 📋 Table of Contents

1. [Problem Statement](#-problem-statement)
2. [Technology Stack](#-technology-stack)
3. [Repository Structure](#-repository-structure)
4. [Implementation — Section by Section](#-implementation--section-by-section)
5. [How to Run — Every Command](#-how-to-run--every-command)
6. [Test Results — All Scenarios Verified](#-test-results--all-scenarios-verified)
7. [Live Web Dashboard](#-live-web-dashboard-apppy)
8. [AI Prompt Log Summary](#-ai-prompt-log-summary)
9. [Submission Checklist](#-submission-checklist)

---

## 🎯 Problem Statement

In real-world IoT deployments, device fleets continuously stream telemetry (temperature readings, status codes, device IDs). Raw sensor data is inherently noisy:

- Sensors glitch → `None` values, negative error codes, unconvertible strings.
- Hardware malfunctions spike readings beyond physical limits.
- Operators need automated summarization to identify failing devices and overheating hardware.

**This project solves the problem in three stages:**

| Stage | What It Solves |
|---|---|
| **Stage 1 — Sanitization** | Cleans raw mixed-type sensor lists. Drops nulls, negatives, booleans. Caps spikes at 500.0. |
| **Stage 2 — Aggregation** | Reads CSV logs, groups records by device ID, computes total records, average temperature, and error count. Filters any device with average temp > 80.0 °C. Exports clean JSON and ASCII table. |
| **Stage 3 — Visualization** | Loads the JSON summary and generates a labelled bar chart (PNG + live web dashboard). |

---

## 🛠 Technology Stack

| Layer | Technology | Why |
|---|---|---|
| **Language** | **Python 3.11** | Explicitly mandated by the assessment. Zero-boilerplate, native data structures. |
| **Data Ingestion & Aggregation** | `csv`, `json`, `collections.defaultdict` | Standard library. Robust against corrupted rows with no external dependencies. |
| **CLI Interface** | `argparse` | Built-in, enables `--input`, `--output`, `--threshold` flags for flexible pipeline use. |
| **Unit Testing** | `unittest` | Automated test assertions with clear pass/fail output per scenario. |
| **Visualization** | `matplotlib 3.11` | Mandated in Section 3. Non-interactive `Agg` backend for headless PNG generation. |
| **Web Dashboard** | `http.server`, `socketserver` | Zero-dependency localhost server. Returns base64-encoded charts via REST API. |

---

## 🏗 Repository Structure

```text
Intern/
├── device_telemetry.csv       # Input: 21 rows across 5 devices (DEV_A to DEV_E)
├── sanitization.py            # Section 1: Data cleaning logic + 7 unit tests
├── summarizer.py              # Section 2: CLI ingest, aggregate, filter, export
├── visualizer.py              # Section 3: matplotlib PNG chart generator
├── app.py                     # Bonus: Live localhost web dashboard on port 8000
├── test_suite.py              # 4-scenario end-to-end automated test suite
├── output_summary.json        # Output: Filtered JSON summary (3 retained devices)
├── temperature_chart.png      # Output: 300 DPI comparative bar chart
├── PROMPT_LOG.md              # Section 3: AI prompt + bug identification + fix log
└── README.md                  # This file
```

---

## 📐 Implementation — Section by Section

### Section 1 — Sensor Data Sanitization (`sanitization.py`)

**Function:** `clean_sensor_readings(readings)`

**Business Rules Implemented:**

| Rule | Code Logic |
|---|---|
| Convert elements to `float` | `float(item)` wrapped in `try/except ValueError` |
| Drop `None` values | `if item is None: continue` |
| Drop negative values `(< 0)` | `if val < 0.0: continue` |
| Drop Python booleans (`True/False`) | `if isinstance(item, bool): continue` |
| Drop unconvertible strings (`"error"`, `"N/A"`) | Caught in `except (ValueError, TypeError)` |
| Cap any value `> 500.0` to exactly `500.0` | `if val > 500.0: val = 500.0` |
| Handle empty list / `None` / non-iterable input | `if not isinstance(readings, (list, tuple)): return []` |

**Tested on:**

```python
clean_sensor_readings([10.5, "20.0", -99, None, 650.0, True, 1800, 18.5, "false", "7870", "corrupt"])
# → [10.5, 20.0, 500.0, 500.0, 18.5, 500.0]
```

---

### Section 2 — Core CLI Aggregator (`summarizer.py`)

**Input:** `device_telemetry.csv` (columns: `device_id`, `status`, `temperature`)

**Processing Logic:**

```
CSV Row → [Validate device_id] → [Parse temperature to float] → [Group by device_id]
       → [Compute total_records, average_temperature, error_count]
       → [Filter: avg_temp > 80.0 → EXCLUDED]
       → [Export JSON] + [Print ASCII Table]
```

**Terminal Output (actual run result):**

```text
====================================================================
           DEVICE TELEMETRY AGGREGATION SUMMARY
====================================================================
Device ID    | Total Records  | Avg Temp (C)   | Errors   | Status
--------------------------------------------------------------------
DEV_A        | 5              | 45.96          | 1        | RETAINED
DEV_B        | 5              | 72.40          | 2        | RETAINED
DEV_C        | 4              | 86.00          | 1        | EXCLUDED (>80.0 C)
DEV_D        | 4              | 27.90          | 0        | RETAINED
DEV_E        | 3              | 82.23          | 2        | EXCLUDED (>80.0 C)
====================================================================
Summary: 3 retained / 5 total devices (Threshold: <= 80.0 C)

 [SUCCESS] Exported 3 records to 'output_summary.json'
```

---

### Section 3 — Visualization (`visualizer.py`)

**Loads:** `output_summary.json`  
**Outputs:** `temperature_chart.png` at 300 DPI

**Design elements enforced (after AI bug fixes):**
- Centered value badges above every bar (`45.96 °C`, `72.40 °C`, `27.90 °C`)
- Red dashed reference line at `80.0 °C` ("Max Permitted Threshold")
- 20% Y-axis headroom to prevent label clipping
- `matplotlib.use("Agg")` for headless CLI compatibility
- `plt.tight_layout()` to prevent axis label overlap

---

## 💻 How to Run — Every Command

### Section 1: Run Sanitization Unit Tests
```powershell
py sanitization.py
```

### Section 2: Run Telemetry Aggregation CLI
```powershell
py summarizer.py --input device_telemetry.csv --output output_summary.json --threshold 80.0
```

### Section 3: Generate PNG Bar Chart
```powershell
py visualizer.py --input output_summary.json --output temperature_chart.png
```

### Live Web Dashboard (Bonus)
```powershell
py app.py
```
Open **http://localhost:8000** in any browser. Paste any numbers or device data and visualize instantly.

### Full Automated Test Suite
```powershell
py test_suite.py
```

---

## 🧪 Test Results — All Scenarios Verified

### Section 1 — Unit Tests (`py sanitization.py`)

```text
test_all_invalid_entries ............. ok  (all-invalid list returns [])
test_boolean_rejection ............... ok  (True/False not treated as 1.0/0.0)
test_boundary_clipping ............... ok  (1000.0 → 500.0, 499.9 unchanged)
test_empty_and_none_input ............ ok  ([], None, 12345 all return [])
test_my_own_case ..................... ok  ([100.0, "300.5", -5, 999.0] → [100.0, 300.5, 500.0])
test_negative_values_and_error_flags . ok  (-0.01, -1, -999, "-50.5" dropped; 0.0 kept)
test_standard_mixed_input ............ ok  ([12.5, "45.0", -1, None, "error", 250.75] → [12.5, 45.0, 250.75])

Ran 7 tests in 0.000s — OK
```

### Section 2 — Scenario Tests (`py test_suite.py`)

```text
test_scenario_1_standard_dataset ..... ok  (5 devices parsed; DEV_A, DEV_B, DEV_D retained)
test_scenario_2_missing_file_handling  ok  (FileNotFoundError raised cleanly; no crash)
test_scenario_3_empty_csv ............ ok  (header-only CSV → [], no ZeroDivisionError)
test_scenario_4_corrupted_rows ....... ok  (malformed temp strings skipped; valid rows computed)

Ran 4 tests in 0.009s — OK
```

---

## 🌐 Live Web Dashboard (`app.py`)

A localhost web application built using Python's built-in `http.server` module — **zero external web framework dependencies**.

**Features:**
- **Tab 1 — Raw Sensor Sanitizer:** Paste any comma/space/newline-separated numbers, click Sanitize. Instantly see a bar chart of cleaned values with capped values (`≥ 500`) highlighted in coral, and the rest in navy blue.
- **Tab 2 — Device Telemetry Aggregator:** Paste custom device CSV rows. Adjust the threshold slider. Chart updates live per device.
- **Preset Examples:** "Industrial Factory", "Server Farm", "All Cool", "Your Custom Test" load real examples with one click.

```powershell
py app.py
# → http://localhost:8000
```

---

## 🤖 AI Prompt Log Summary

Full details in [`PROMPT_LOG.md`](PROMPT_LOG.md).

### Initial Prompt (sent to AI for visualization):

```text
Write a Python script using matplotlib that loads an aggregated telemetry JSON file
(containing objects with "device_id" and "average_temperature") and creates a bar chart
comparing the average temperature per device. Save the resulting chart as a PNG file.
```

### Bugs Identified in AI's First Draft:

| # | Bug | Root Cause |
|---|---|---|
| 1 | Value label on tallest bar clipped by figure top edge | Y-axis had no headroom; `ax.set_ylim()` not adjusted. |
| 2 | No 80 °C safety threshold reference line | Threshold not passed to visualization function. |
| 3 | `UserWarning: Matplotlib is currently using TkAgg` in CLI | Missing `matplotlib.use("Agg")` before pyplot import. |

### Corrective Follow-Up Prompt:

```text
The initial script works but has layout and design issues:
1. Expand ax.set_ylim() to provide 20% headroom above the max temperature value so value
   labels printed above the tallest bar are not clipped by the figure boundary.
2. Add a horizontal dashed red line at y=80.0 labeled "Max Permitted Threshold (80 °C)"
   so operators can immediately see how close each device is to the safety cutoff.
3. Set matplotlib.use("Agg") before any pyplot import to prevent GUI backend warnings
   in headless CLI and automated pipeline environments.
4. Annotate each bar with the value centered above it (format: "XX.XX °C") and call
   plt.tight_layout() to ensure no axis labels or titles are cut off.
```

### Result After Fix:
`temperature_chart.png` generated at 300 DPI — zero clipping, clear labels, threshold line visible, headless compatible.

---

## ✅ Submission Checklist

- [x] `sanitization.py` — Pure Python data cleaning + 7 unit tests (100% passing)
- [x] `device_telemetry.csv` — 21-row representative telemetry dataset (5 devices)
- [x] `summarizer.py` — CLI aggregation tool (ingest, group, filter, export)
- [x] `output_summary.json` — Exported filtered JSON (3 retained devices)
- [x] `visualizer.py` — Matplotlib 300 DPI bar chart script
- [x] `temperature_chart.png` — Generated visual output file
- [x] `test_suite.py` — 4 production-scenario automated tests (100% passing)
- [x] `PROMPT_LOG.md` — AI prompting workflow with bugs identified and corrections documented
- [x] `app.py` — Live localhost web dashboard for real-time interactive visualization
- [x] `README.md` — Complete technical documentation
