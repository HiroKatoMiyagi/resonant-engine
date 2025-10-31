#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resonant Trace Bridge v1.1
GitHub Webhook Receiver + Trace Linker Auto Trigger
---------------------------------------------------
GitHub からの push イベントを受信し、
webhook_log.jsonl に記録した後、
trace_linker.py を自動実行して思想と行動を連結する。
"""

from flask import Flask, request
from datetime import datetime
from pathlib import Path
import json
import subprocess

app = Flask(__name__)

# === パス設定 ===
BASE_DIR = Path("/Users/zero/Projects/resonant-engine")
LOG_DIR = BASE_DIR / "logs"
WEBHOOK_LOG = LOG_DIR / "webhook_log.jsonl"
TRACE_MAP = LOG_DIR / "trace_map.jsonl"
TRACE_LINKER = BASE_DIR / "utils" / "trace_linker.py"

# === ユーティリティ ===
def write_log(path: Path, data: dict):
    """JSONL 形式でログを書き込む"""
    path.parent.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = datetime.now().isoformat()
    with open(path, "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

# === Webhook 受信 ===
@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    payload = request.get_json(silent=True)

    print(f"[Webhook] Event={event_type}, Delivery={delivery_id}")

    # 受信データをログに保存
    if payload:
        write_log(WEBHOOK_LOG, {
            "event": event_type,
            "payload": payload,
            "tag": "[ACTION]"
        })
    else:
        write_log(WEBHOOK_LOG, {
            "event": event_type,
            "payload": None,
            "tag": "[EMPTY]"
        })

    # === push イベントの処理 ===
    if event_type == "push":
        print("[Trigger] push event detected → trace_linker 実行中...")
        try:
            result = subprocess.run(
                ["python3", str(TRACE_LINKER)],
                capture_output=True, text=True, cwd=str(BASE_DIR)
            )
            print(result.stdout)
            if result.stderr.strip():
                print("[TraceLinker STDERR]:", result.stderr.strip())
            print(f"[TraceMap Updated] Exists={TRACE_MAP.exists()}")
        except Exception as e:
            print(f"[Error] Trace Linker 実行失敗: {e}")

    return "OK", 200


# === サーバ起動 ===
if __name__ == "__main__":
    print("[Resonant Trace Bridge] Listening on port 5001 ...")
    app.run(host="0.0.0.0", port=5001)