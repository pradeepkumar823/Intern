"""
Interactive Localhost Web Dashboard for Device Log Summarizer.
Runs a zero-dependency local web server on http://localhost:8000.
Users can input any numbers or device telemetry and visualize the results dynamically in real-time.
"""

import base64
import http.server
import io
import json
import re
import socketserver
import urllib.parse
from typing import Any, Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from sanitization import clean_sensor_readings
from summarizer import process_telemetry

PORT = 8000

HTML_PAGE = """<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Device Telemetry & Sensor Visualizer</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600&display=swap" rel="stylesheet">
  <style>
    :root {
      --bg: #0b132b;
      --card-bg: rgba(28, 37, 65, 0.75);
      --card-border: rgba(255, 255, 255, 0.12);
      --accent: #48bfe3;
      --accent-glow: rgba(72, 191, 227, 0.25);
      --accent-warm: #f77f00;
      --danger: #e63946;
      --success: #06d6a0;
      --text-main: #f8f9fa;
      --text-muted: #8d99ae;
      --input-bg: rgba(11, 19, 43, 0.85);
    }

    * {
      box-sizing: border-box;
      margin: 0;
      padding: 0;
    }

    body {
      font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
      background: radial-gradient(circle at top right, #1c2541, #0b132b 75%);
      color: var(--text-main);
      min-height: 100vh;
      padding: 24px 20px;
    }

    .container {
      max-width: 1150px;
      margin: 0 auto;
    }

    header {
      margin-bottom: 24px;
      text-align: center;
    }

    .badge {
      display: inline-block;
      padding: 6px 14px;
      background: var(--accent-glow);
      border: 1px solid var(--accent);
      color: var(--accent);
      border-radius: 20px;
      font-size: 0.78rem;
      font-weight: 700;
      letter-spacing: 0.8px;
      text-transform: uppercase;
      margin-bottom: 10px;
    }

    h1 {
      font-size: 2.1rem;
      font-weight: 800;
      letter-spacing: -0.5px;
      background: linear-gradient(135deg, #ffffff 40%, #48bfe3);
      -webkit-background-clip: text;
      -webkit-text-fill-color: transparent;
      margin-bottom: 6px;
    }

    p.subtitle {
      color: var(--text-muted);
      font-size: 0.95rem;
    }

    /* Tabs */
    .tabs {
      display: flex;
      gap: 12px;
      margin-bottom: 22px;
      justify-content: center;
    }

    .tab-btn {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      padding: 10px 22px;
      border-radius: 10px;
      font-weight: 600;
      cursor: pointer;
      transition: all 0.2s ease;
      font-size: 0.95rem;
    }

    .tab-btn.active, .tab-btn:hover {
      color: #fff;
      background: rgba(72, 191, 227, 0.15);
      border-color: var(--accent);
      box-shadow: 0 0 15px var(--accent-glow);
    }

    /* Grid Layout */
    .grid {
      display: grid;
      grid-template-columns: 1fr 1.35fr;
      gap: 22px;
    }

    @media (max-width: 860px) {
      .grid {
        grid-template-columns: 1fr;
      }
    }

    .card {
      background: var(--card-bg);
      border: 1px solid var(--card-border);
      backdrop-filter: blur(12px);
      border-radius: 16px;
      padding: 22px;
      box-shadow: 0 10px 30px rgba(0, 0, 0, 0.4);
    }

    .card-title {
      font-size: 1.12rem;
      font-weight: 700;
      margin-bottom: 14px;
      display: flex;
      align-items: center;
      gap: 8px;
      color: #fff;
    }

    label {
      display: block;
      font-size: 0.8rem;
      font-weight: 600;
      color: var(--text-muted);
      margin-bottom: 6px;
      text-transform: uppercase;
      letter-spacing: 0.5px;
    }

    textarea, input[type="text"], input[type="number"] {
      width: 100%;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 12px 14px;
      color: #fff;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.9rem;
      outline: none;
      transition: border 0.2s;
    }

    textarea:focus, input:focus {
      border-color: var(--accent);
      box-shadow: 0 0 10px var(--accent-glow);
    }

    textarea {
      resize: vertical;
      min-height: 125px;
      line-height: 1.5;
    }

    .row {
      display: flex;
      gap: 12px;
      margin-top: 14px;
      align-items: center;
    }

    .btn {
      width: 100%;
      margin-top: 16px;
      padding: 13px 20px;
      background: linear-gradient(135deg, #48bfe3, #5390d9);
      color: #0b132b;
      font-weight: 700;
      font-size: 0.95rem;
      border: none;
      border-radius: 10px;
      cursor: pointer;
      transition: all 0.25s ease;
      letter-spacing: 0.3px;
    }

    .btn:hover {
      transform: translateY(-2px);
      box-shadow: 0 8px 20px rgba(72, 191, 227, 0.4);
    }

    .btn:active {
      transform: translateY(0);
    }

    /* Output Section */
    .chart-container {
      width: 100%;
      min-height: 330px;
      display: flex;
      align-items: center;
      justify-content: center;
      background: rgba(11, 19, 43, 0.6);
      border: 1px solid var(--card-border);
      border-radius: 12px;
      overflow: hidden;
      padding: 6px;
    }

    .chart-container img {
      width: 100%;
      height: auto;
      display: block;
      border-radius: 8px;
    }

    .stats-row {
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(105px, 1fr));
      gap: 10px;
      margin-top: 14px;
    }

    .stat-pill {
      background: rgba(255, 255, 255, 0.04);
      border: 1px solid var(--card-border);
      border-radius: 10px;
      padding: 10px 8px;
      text-align: center;
    }

    .stat-num {
      font-size: 1.25rem;
      font-weight: 800;
      color: var(--accent);
      font-family: 'JetBrains Mono', monospace;
    }

    .stat-label {
      font-size: 0.7rem;
      color: var(--text-muted);
      text-transform: uppercase;
      font-weight: 600;
      margin-top: 2px;
    }

    .output-box {
      margin-top: 14px;
      background: var(--input-bg);
      border: 1px solid var(--card-border);
      border-radius: 8px;
      padding: 12px;
      font-family: 'JetBrains Mono', monospace;
      font-size: 0.85rem;
      color: #90e0ef;
      max-height: 130px;
      overflow-y: auto;
      word-break: break-all;
    }

    .preset-btns {
      display: flex;
      gap: 8px;
      margin-top: 10px;
      flex-wrap: wrap;
    }

    .preset-btn {
      font-size: 0.74rem;
      padding: 5px 10px;
      background: rgba(255, 255, 255, 0.05);
      border: 1px solid var(--card-border);
      color: var(--text-muted);
      border-radius: 6px;
      cursor: pointer;
      font-weight: 500;
    }
    .preset-btn:hover {
      color: #fff;
      border-color: var(--accent);
    }
  </style>
</head>
<body>
  <div class="container">
    <header>
      <div class="badge">Live Localhost Pipeline</div>
      <h1>Device Log Summarizer & Visualizer</h1>
      <p class="subtitle">Input any numbers or device telemetry to sanitize, aggregate, and visualize live.</p>
    </header>

    <div class="tabs">
      <button class="tab-btn active" id="tabSanitizeBtn" onclick="switchTab('sanitize')">🧹 Raw Sensor Number Sanitizer</button>
      <button class="tab-btn" id="tabTelemetryBtn" onclick="switchTab('telemetry')">📊 Device Telemetry Aggregator</button>
    </div>

    <!-- TAB 1: RAW SENSOR NUMBERS -->
    <div id="viewSanitize" class="grid">
      <div class="card">
        <div class="card-title">🧹 Input Sensor Readings</div>
        <label for="rawInput">Enter any numbers (separated by comma, space, or newline)</label>
        <textarea id="rawInput" rows="7">12.5, "45.0", -1, None, "error", 250.75, 620.0, -999, 500.1, 78.4, True, "bad_data"</textarea>

        <div class="preset-btns">
          <span style="font-size: 0.75rem; color: var(--text-muted); align-self: center;">Try Presets:</span>
          <button class="preset-btn" onclick="loadNumberPreset('your_example')">Your Custom Test</button>
          <button class="preset-btn" onclick="loadNumberPreset('extreme')">Spikes (>500)</button>
          <button class="preset-btn" onclick="loadNumberPreset('dirty')">Negatives & Nulls</button>
        </div>

        <button class="btn" onclick="submitSanitization()">✨ Sanitize & Plot Live</button>
      </div>

      <div class="card">
        <div class="card-title">📊 Sanitized Cleaned Chart</div>
        <div class="chart-container" id="sanitizeChartBox">
          <span style="color: var(--text-muted); font-size: 0.9rem;">Loading visualization...</span>
        </div>

        <div class="stats-row">
          <div class="stat-pill">
            <div class="stat-num" id="statRawCount">-</div>
            <div class="stat-label">Raw Items</div>
          </div>
          <div class="stat-pill">
            <div class="stat-num" id="statValidCount" style="color: var(--success);">-</div>
            <div class="stat-label">Valid Cleaned</div>
          </div>
          <div class="stat-pill">
            <div class="stat-num" id="statDroppedCount" style="color: var(--danger);">-</div>
            <div class="stat-label">Dropped (Null/Neg)</div>
          </div>
        </div>

        <label style="margin-top: 14px;">Cleaned Float Output List</label>
        <div class="output-box" id="cleanedOutput">Ready...</div>
      </div>
    </div>

    <!-- TAB 2: DEVICE TELEMETRY -->
    <div id="viewTelemetry" class="grid" style="display: none;">
      <div class="card">
        <div class="card-title">📝 Input Telemetry CSV</div>
        <label for="csvInput">device_id, status, temperature</label>
        <textarea id="csvInput" rows="10">DEV_A,ACTIVE,42.5
DEV_A,ACTIVE,45.0
DEV_A,WARNING,50.2
DEV_A,ERROR,48.0
DEV_B,ACTIVE,68.0
DEV_B,WARNING,72.5
DEV_B,ERROR,76.0
DEV_C,ACTIVE,82.0
DEV_C,ERROR,91.0
DEV_D,ACTIVE,26.4
DEV_D,ACTIVE,28.1
DEV_E,ACTIVE,81.0
DEV_E,ERROR,83.5</textarea>

        <div class="preset-btns">
          <span style="font-size: 0.75rem; color: var(--text-muted); align-self: center;">Presets:</span>
          <button class="preset-btn" onclick="loadTelemetryPreset('factory')">Industrial Factory</button>
          <button class="preset-btn" onclick="loadTelemetryPreset('server')">Server Farm</button>
          <button class="preset-btn" onclick="loadTelemetryPreset('all_pass')">All Cool</button>
        </div>

        <div class="row" style="margin-top: 16px;">
          <div style="flex: 1;">
            <label for="thresholdInput">Filter Threshold (°C)</label>
            <input type="number" id="thresholdInput" value="80.0" step="5" min="10" max="200" onchange="submitTelemetry()">
          </div>
        </div>

        <button class="btn" onclick="submitTelemetry()">🚀 Aggregate & Visualize</button>
      </div>

      <div class="card">
        <div class="card-title">📈 Telemetry Comparison Chart</div>
        <div class="chart-container" id="telemetryChartBox">
          <span style="color: var(--text-muted); font-size: 0.9rem;">Click "Aggregate & Visualize" to generate</span>
        </div>

        <div class="stats-row" id="telemetryStats">
          <div class="stat-pill">
            <div class="stat-num" id="statTotalDevices">-</div>
            <div class="stat-label">Total Devices</div>
          </div>
          <div class="stat-pill">
            <div class="stat-num" id="statRetainedDevices" style="color: var(--success);">-</div>
            <div class="stat-label">Retained</div>
          </div>
          <div class="stat-pill">
            <div class="stat-num" id="statExcludedDevices" style="color: var(--danger);">-</div>
            <div class="stat-label">Excluded</div>
          </div>
        </div>

        <label style="margin-top: 14px;">Exported JSON Summary</label>
        <div class="output-box" id="jsonOutput">Ready to process...</div>
      </div>
    </div>
  </div>

  <script>
    function switchTab(tab) {
      if (tab === 'telemetry') {
        document.getElementById('viewTelemetry').style.display = 'grid';
        document.getElementById('viewSanitize').style.display = 'none';
        document.getElementById('tabTelemetryBtn').classList.add('active');
        document.getElementById('tabSanitizeBtn').classList.remove('active');
        submitTelemetry();
      } else {
        document.getElementById('viewTelemetry').style.display = 'none';
        document.getElementById('viewSanitize').style.display = 'grid';
        document.getElementById('tabSanitizeBtn').classList.add('active');
        document.getElementById('tabTelemetryBtn').classList.remove('active');
        submitSanitization();
      }
    }

    async function submitSanitization() {
      const rawText = document.getElementById('rawInput').value;
      
      const res = await fetch('/api/sanitize', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ raw_text: rawText })
      });
      const data = await res.json();

      document.getElementById('sanitizeChartBox').innerHTML = `<img src="data:image/png;base64,${data.image_base64}" alt="Sanitized Chart">`;
      document.getElementById('statRawCount').textContent = data.raw_count;
      document.getElementById('statValidCount').textContent = data.valid_count;
      document.getElementById('statDroppedCount').textContent = data.dropped_count;
      document.getElementById('cleanedOutput').textContent = JSON.stringify(data.cleaned_numbers, null, 2);
    }

    async function submitTelemetry() {
      const csv = document.getElementById('csvInput').value;
      const threshold = parseFloat(document.getElementById('thresholdInput').value) || 80.0;
      
      const res = await fetch('/api/telemetry', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ csv_text: csv, threshold: threshold })
      });
      const data = await res.json();
      
      if (data.error) {
        alert('Error: ' + data.error);
        return;
      }

      document.getElementById('telemetryChartBox').innerHTML = `<img src="data:image/png;base64,${data.image_base64}" alt="Telemetry Chart">`;
      document.getElementById('statTotalDevices').textContent = data.total_devices;
      document.getElementById('statRetainedDevices').textContent = data.retained_devices;
      document.getElementById('statExcludedDevices').textContent = data.excluded_devices;
      document.getElementById('jsonOutput').textContent = JSON.stringify(data.filtered_summary, null, 2);
    }

    function loadNumberPreset(type) {
      if (type === 'your_example') {
        document.getElementById('rawInput').value = "10.5, '20.0', -99, None, 650.0, True, 1800, 18.5, 'false', '7870', 'corrupt'";
      } else if (type === 'extreme') {
        document.getElementById('rawInput').value = "450.0, 520.0, 800.0, 1500, 499.9, '600.5', 500.0";
      } else if (type === 'dirty') {
        document.getElementById('rawInput').value = "-0.5, -999, 'N/A', 15.0, 32.5, null, 500.0, 720.0";
      }
      submitSanitization();
    }

    function loadTelemetryPreset(type) {
      if (type === 'factory') {
        document.getElementById('csvInput').value = "PUMP_01,ACTIVE,34.5\\nPUMP_01,ACTIVE,36.0\\nMOTOR_X,ACTIVE,62.0\\nMOTOR_X,WARNING,65.5\\nTURBINE_A,ACTIVE,18.2\\nBOILER_01,ERROR,76.5\\nBOILER_01,WARNING,79.0\\nOVERHEAT_UNIT,ERROR,89.5";
      } else if (type === 'server') {
        document.getElementById('csvInput').value = "NODE_01,ACTIVE,28.5\\nNODE_01,ACTIVE,29.1\\nNODE_02,ACTIVE,42.0\\nNODE_03,ERROR,74.5\\nNODE_04_GPU,WARNING,86.0\\nNODE_04_GPU,ERROR,92.5";
      } else if (type === 'all_pass') {
        document.getElementById('csvInput').value = "DEV_01,ACTIVE,25.0\\nDEV_02,ACTIVE,30.0\\nDEV_03,ACTIVE,35.0\\nDEV_04,ACTIVE,40.0";
      }
      submitTelemetry();
    }

    // Auto-load on page open
    window.onload = function() {
      submitSanitization();
    };
  </script>
</body>
</html>
"""


def render_sanitization_chart(cleaned_numbers: List[float]) -> str:
    """
    Renders an individual bar chart for every cleaned sensor reading.
    Ensures zero label clipping, distinct colors for capped values (500.0),
    and ample margins so every single sample is visible.
    """
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)

    if not cleaned_numbers:
        ax.text(0.5, 0.5, "No valid cleaned readings", ha="center", va="center", color="#888888", fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        labels = [f"#{i+1}" for i in range(len(cleaned_numbers))]
        
        # Color: Coral for capped at 500.0, Navy/Blue for standard readings
        colors = ["#e07a5f" if val >= 500.0 else "#2b5c8f" for val in cleaned_numbers]

        bars = ax.bar(labels, cleaned_numbers, color=colors, width=0.55, edgecolor="#1e3d59", linewidth=1.2, zorder=3)

        # Place value directly above each bar
        for bar in bars:
            height = bar.get_height()
            label_text = f"{height:.1f}" if height < 500.0 else "500.0 (Cap)"
            ax.annotate(
                label_text,
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold",
                color="#111111"
            )

        # Draw red dashed clipping limit
        ax.axhline(y=500.0, color="#d62828", linestyle="--", linewidth=1.2, label="Clipping Ceiling (500.0)", zorder=2)

        # Upper headroom: 25% above max
        max_val = max(cleaned_numbers) if cleaned_numbers else 500.0
        ax.set_ylim(0, max(max_val * 1.25, 580.0))
        ax.legend(loc="upper right", fontsize=8.5, frameon=True)

    ax.set_title("Cleaned & Normalized Sensor Values per Sample", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Sample Number", fontsize=10, fontweight="bold")
    ax.set_ylabel("Cleaned Float Value", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.5, zorder=1)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


def render_telemetry_chart(filtered_summary: List[Dict[str, Any]], threshold: float) -> str:
    """Renders bar chart comparing average temperatures per device."""
    fig, ax = plt.subplots(figsize=(7.5, 4.4), dpi=150)

    if not filtered_summary:
        ax.text(0.5, 0.5, "No devices within threshold", ha="center", va="center", color="#888888", fontsize=12)
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
    else:
        device_ids = [d["device_id"] for d in filtered_summary]
        temps = [d["average_temperature"] for d in filtered_summary]

        colors = ["#2b5c8f" if t < 50.0 else "#e07a5f" if t > 70.0 else "#3d85c6" for t in temps]
        bars = ax.bar(device_ids, temps, color=colors, width=0.5, edgecolor="#1e3d59", linewidth=1.2, zorder=3)

        for bar in bars:
            height = bar.get_height()
            ax.annotate(
                f"{height:.2f} °C",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 5),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

        ax.axhline(y=threshold, color="#d62828", linestyle="--", linewidth=1.2, label=f"Threshold ({threshold:.1f} °C)", zorder=2)
        max_val = max(temps) if temps else threshold
        ax.set_ylim(0, max(max_val * 1.25, threshold + 12))
        ax.legend(loc="upper right", fontsize=8.5)

        if len(device_ids) > 4:
            plt.xticks(rotation=25, ha="right")

    ax.set_title("Average Temperature per Retained Device", fontsize=12, fontweight="bold", pad=12)
    ax.set_xlabel("Device ID", fontsize=10, fontweight="bold")
    ax.set_ylabel("Average Temperature (°C)", fontsize=10, fontweight="bold")
    ax.grid(axis="y", linestyle=":", alpha=0.5, zorder=1)
    plt.tight_layout()

    buf = io.BytesIO()
    plt.savefig(buf, format="png", dpi=150)
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")


class RequestHandler(http.server.SimpleHTTPRequestHandler):

    def do_GET(self):
        if self.path in ("/", "/index.html"):
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif self.path == "/favicon.ico" or self.path.startswith("/static/"):
            self.send_response(204)
            self.end_headers()
        else:
            self.send_error(404, "Page not found")

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        post_data = self.rfile.read(content_length)

        try:
            req_json = json.loads(post_data.decode("utf-8"))
        except Exception:
            self.send_error(400, "Invalid JSON payload")
            return

        if self.path == "/api/sanitize":
            raw_text = req_json.get("raw_text", "")
            
            # Robust token extraction: split by comma, space, newline, or tab
            tokens = [t.strip().strip("'\"") for t in re.split(r'[, \n\t]+', raw_text) if t.strip()]

            cleaned = clean_sensor_readings(tokens)
            img_b64 = render_sanitization_chart(cleaned)

            response = {
                "raw_count": len(tokens),
                "valid_count": len(cleaned),
                "dropped_count": len(tokens) - len(cleaned),
                "cleaned_numbers": cleaned,
                "image_base64": img_b64
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))

        elif self.path == "/api/telemetry":
            csv_text = req_json.get("csv_text", "")
            threshold = float(req_json.get("threshold", 80.0))

            lines = [ln.strip() for ln in csv_text.strip().splitlines() if ln.strip()]
            from collections import defaultdict
            telemetry_data = defaultdict(lambda: {"temperatures": [], "error_count": 0, "total_records": 0})

            start_idx = 0
            if lines and "device_id" in lines[0].lower():
                start_idx = 1

            for line in lines[start_idx:]:
                parts = [p.strip() for p in line.split(",")]
                if len(parts) < 3:
                    continue
                dev_id, status, temp_str = parts[0], parts[1].upper(), parts[2]
                if not dev_id:
                    continue
                try:
                    temp_val = float(temp_str)
                except ValueError:
                    continue

                telemetry_data[dev_id]["total_records"] += 1
                telemetry_data[dev_id]["temperatures"].append(temp_val)
                if status == "ERROR":
                    telemetry_data[dev_id]["error_count"] += 1

            all_stats = {}
            filtered_summary = []
            for dev_id, st in sorted(telemetry_data.items()):
                tot = st["total_records"]
                avg = round(sum(st["temperatures"]) / tot, 2) if tot > 0 else 0.0
                item = {
                    "device_id": dev_id,
                    "total_records": tot,
                    "average_temperature": avg,
                    "error_count": st["error_count"]
                }
                all_stats[dev_id] = item
                if avg <= threshold:
                    filtered_summary.append(item)

            img_b64 = render_telemetry_chart(filtered_summary, threshold)

            response = {
                "filtered_summary": filtered_summary,
                "total_devices": len(all_stats),
                "retained_devices": len(filtered_summary),
                "excluded_devices": len(all_stats) - len(filtered_summary),
                "image_base64": img_b64
            }

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(json.dumps(response).encode("utf-8"))
        else:
            self.send_error(404, "Endpoint not found")


def start_server():
    server_address = ("", PORT)
    with socketserver.TCPServer(server_address, RequestHandler) as httpd:
        print(f"\n=======================================================")
        print(f"🚀 Live Telemetry Web Visualizer running on localhost!")
        print(f"👉 Open in your browser: http://localhost:{PORT}")
        print(f"=======================================================\n")
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\nShutting down server.")


if __name__ == "__main__":
    start_server()
