#!/usr/bin/env python3
import time, json, os
from datetime import datetime

ROOT = "/Users/zero/Projects/kiro-v3.1"
LOG_FILE = f"{ROOT}/logs/resonant_state.log"
TELEMETRY_FILE = f"{ROOT}/logs/telemetry_report.json"

def safe_parse(line):
    try:
        entry = json.loads(line.strip())
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        return entry
    except Exception:
        return None

def calculate_metrics(entries):
    timestamps = [datetime.strptime(e["timestamp"], "%Y-%m-%d %H:%M:%S") for e in entries]
    cycles = [(timestamps[i] - timestamps[i-1]).total_seconds() for i in range(1, len(timestamps))]
    avg_cycle = sum(cycles)/len(cycles) if cycles else 0
    coherence = 0.5 + 0.5 * (1 if len(entries) > 5 else 0)
    stability = min(1.0, coherence * (len(entries)/50))
    return {
        "avg_cycle_time_sec": round(avg_cycle, 3),
        "coherence_ratio": round(coherence, 2),
        "stability_index": round(stability, 2),
        "last_update": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }

def main():
    print("📡 Resonant Analyzer started (monitoring resonant_state.log)")
    entries = []
    last_size = 0
    while True:
        try:
            size = os.path.getsize(LOG_FILE)
            if size != last_size:
                with open(LOG_FILE, "r") as f:
                    lines = f.readlines()
                for line in lines[len(entries):]:
                    e = safe_parse(line)
                    if e:
                        entries.append(e)
                entries.sort(key=lambda e: e["timestamp"])
                metrics = calculate_metrics(entries)
                with open(TELEMETRY_FILE, "w") as f:
                    json.dump(metrics, f, indent=2)
                print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] 🧠 Telemetry updated: "
                      f"R-Index={metrics['stability_index']}, "
                      f"Cycle={metrics['avg_cycle_time_sec']}s, "
                      f"Coherence={metrics['coherence_ratio']}")
                last_size = size
            time.sleep(10)
        except Exception as e:
            print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] ⚠️ Analyzer Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()