#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Resonant Trace Bridge v1.2
GitHub Webhook Receiver + Trace Linker Auto Trigger
---------------------------------------------------
GitHub からの push イベントを受信し、
webhook_log.jsonl に記録した後、
trace_linker.py を自動実行して思想と行動を連結する。

v1.2: 統一イベントストリーム統合
"""

from flask import Flask, request, abort
from datetime import datetime
from pathlib import Path
import json
import subprocess
import os
import sys
import hmac
import hashlib

# utils/ からの import を可能にする
sys.path.append(str(Path(__file__).parent))
from resonant_event_stream import get_stream

app = Flask(__name__)

# === パス設定 ===
BASE_DIR = Path(os.environ.get("RESONANT_ENGINE_BASE_DIR", "/Users/zero/Projects/resonant-engine"))
LOG_DIR = BASE_DIR / "logs"
WEBHOOK_LOG = LOG_DIR / "webhook_log.jsonl"
TRACE_MAP = LOG_DIR / "trace_map.jsonl"
TRACE_LINKER = BASE_DIR / "utils" / "trace_linker.py"
DELIVERY_CACHE_PATH = LOG_DIR / "delivery_cache.json"

# === 環境変数読み込み ===
GITHUB_WEBHOOK_SECRET = os.environ.get("GITHUB_WEBHOOK_SECRET", "").encode()

# === ユーティリティ ===
def write_log(path: Path, data: dict):
    """JSONL 形式でログを書き込む"""
    path.parent.mkdir(parents=True, exist_ok=True)
    data["timestamp"] = datetime.now().isoformat()
    with open(path, "a") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")

def load_delivery_cache() -> set:
    """delivery_cache.json から既に処理済みの Delivery ID を読み込む"""
    if not DELIVERY_CACHE_PATH.exists():
        return set()
    try:
        with open(DELIVERY_CACHE_PATH, "r") as f:
            data = json.load(f)
            if isinstance(data, list):
                return set(data)
            else:
                return set()
    except Exception:
        return set()

def save_delivery_cache(delivery_ids: set):
    """delivery_cache.json に処理済みの Delivery ID を保存する"""
    DELIVERY_CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(DELIVERY_CACHE_PATH, "w") as f:
        json.dump(list(delivery_ids), f, ensure_ascii=False, indent=2)

def verify_signature(secret: bytes, payload: bytes, signature_header: str) -> bool:
    """X-Hub-Signature-256 ヘッダーの署名検証を行う"""
    if not signature_header:
        return False
    try:
        sha_name, signature = signature_header.split('=')
    except ValueError:
        return False
    if sha_name != "sha256":
        return False
    mac = hmac.new(secret, msg=payload, digestmod=hashlib.sha256)
    expected_signature = mac.hexdigest()
    return hmac.compare_digest(signature, expected_signature)

# === Webhook 受信 ===
@app.route("/github-webhook", methods=["POST"])
def github_webhook():
    event_type = request.headers.get("X-GitHub-Event")
    delivery_id = request.headers.get("X-GitHub-Delivery")
    signature_header = request.headers.get("X-Hub-Signature-256")
    payload_bytes = request.data
    try:
        payload = request.get_json(silent=True)
    except Exception:
        payload = None

    print(f"[Webhook] Event={event_type}, Delivery={delivery_id}")

    # 署名検証
    if not GITHUB_WEBHOOK_SECRET:
        print("[Warning] GITHUB_WEBHOOK_SECRET is not set. Skipping signature verification.")
    else:
        if not verify_signature(GITHUB_WEBHOOK_SECRET, payload_bytes, signature_header):
            print("[Error] Signature verification failed.")
            abort(400, "Invalid signature")

    # 重複検証
    delivery_cache = load_delivery_cache()
    if delivery_id in delivery_cache:
        print(f"[Info] Duplicate delivery ID {delivery_id} detected. Ignoring.")
        return "Duplicate delivery", 200

    # --- イベントストリーム: Webhook受信イベント記録 ---
    stream = get_stream()
    webhook_event_id = stream.emit(
        event_type="action",
        source="github_webhook",
        data={
            "event": event_type,
            "delivery_id": delivery_id,
            "has_payload": payload is not None,
            "commits": payload.get("commits", []) if payload else []
        },
        tags=["github", "webhook", event_type]
    )
    
    # 受信データをログに保存
    if payload:
        write_log(WEBHOOK_LOG, {
            "event": event_type,
            "payload": payload,
            "tag": "[ACTION]",
            "event_stream_id": webhook_event_id
        })
    else:
        write_log(WEBHOOK_LOG, {
            "event": event_type,
            "payload": None,
            "tag": "[EMPTY]",
            "event_stream_id": webhook_event_id
        })

    # 重複処理済みとして登録
    if delivery_id:
        delivery_cache.add(delivery_id)
        save_delivery_cache(delivery_cache)

    # === push イベントの処理 ===
    if event_type == "push":
        print("[Trigger] push event detected → trace_linker 実行中...")
        
        # --- イベントストリーム: trace_linker実行 ---
        trace_action_id = stream.emit(
            event_type="action",
            source="trace_linker",
            data={
                "action": "execute",
                "trigger": "github_push"
            },
            parent_event_id=webhook_event_id,
            tags=["trace", "linker"]
        )
        
        try:
            result = subprocess.run(
                ["python3", str(TRACE_LINKER)],
                capture_output=True, text=True, cwd=str(BASE_DIR)
            )
            print(result.stdout)
            if result.stderr.strip():
                print("[TraceLinker STDERR]:", result.stderr.strip())
            print(f"[TraceMap Updated] Exists={TRACE_MAP.exists()}")
            
            # --- イベントストリーム: 実行結果 ---
            stream.emit(
                event_type="result",
                source="trace_linker",
                data={
                    "status": "success",
                    "trace_map_exists": TRACE_MAP.exists(),
                    "stdout_lines": len(result.stdout.splitlines())
                },
                parent_event_id=trace_action_id,
                tags=["success"]
            )
        except Exception as e:
            print(f"[Error] Trace Linker 実行失敗: {e}")
            
            # --- イベントストリーム: エラー記録 ---
            stream.emit(
                event_type="result",
                source="trace_linker",
                data={
                    "status": "error",
                    "error": str(e)
                },
                parent_event_id=trace_action_id,
                tags=["error"]
            )

    return "OK", 200


# === サーバ起動 ===
if __name__ == "__main__":
    print("[Resonant Trace Bridge] Listening on port 5001 ...")
    app.run(host="0.0.0.0", port=5001)