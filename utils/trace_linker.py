#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
trace_linker.py — Resonant Trace Bridge Commit Linker
-----------------------------------------------------
GitHub webhookログ(webhook_log.jsonl)と意図ログ(intent_log.jsonl)を突合し、
trace_map.jsonl に「意図 ⇔ コミット」の対応関係を記録するスクリプト。

2025-10-31 修正版:
 - GitHub payload構造の変更 (payload.after / payload.head_commit.id) に対応
 - 最新 commit 情報を正しく抽出する get_latest_commit_info() を改修
 - 出力の安全性・日本語ログ整備
"""

import json
from pathlib import Path
from difflib import SequenceMatcher
from datetime import datetime

# === 設定パス ===
BASE_DIR = Path("/Users/zero/Projects/resonant-engine")
LOG_DIR = BASE_DIR / "logs"
INTENT_LOG = LOG_DIR / "intent_log.jsonl"
WEBHOOK_LOG = LOG_DIR / "webhook_log.jsonl"
TRACE_MAP = LOG_DIR / "trace_map.jsonl"

# === 最新コミット情報を取得 ===
def get_latest_commit_info():
    """
    webhook_log.jsonl から最新の push イベントを探索し、
    commit_id / message / timestamp を抽出して返す。
    """
    if not WEBHOOK_LOG.exists():
        print("[Error] webhook_log.jsonl が存在しません。")
        return None

    lines = WEBHOOK_LOG.read_text().strip().splitlines()
    lines.reverse()  # 最新を優先的に探索
    for line in lines:
        try:
            event = json.loads(line)
            if event.get("event") == "push":
                payload = event.get("payload", {})
                head_commit = payload.get("head_commit", {})
                commit_id = head_commit.get("id") or payload.get("after")
                message = head_commit.get("message", "")
                timestamp = head_commit.get("timestamp", event.get("timestamp"))
                if commit_id:
                    return {
                        "commit_id": commit_id,
                        "message": message,
                        "timestamp": timestamp
                    }
        except json.JSONDecodeError:
            continue
    print("[Info] pushイベントが見つかりません。")
    return None


# === 最新のIntent情報を取得 ===
def get_latest_intent_info():
    """
    intent_log.jsonl から最新の意図(intent)情報を取得する。
    """
    if not INTENT_LOG.exists():
        print("[Error] intent_log.jsonl が存在しません。")
        return None

    lines = INTENT_LOG.read_text().strip().splitlines()
    if not lines:
        print("[Info] intent_log.jsonl にデータがありません。")
        return None

    try:
        last = json.loads(lines[-1])
        return {
            "intent_id": last.get("intent_id"),
            "intent": last.get("intent"),
            "timestamp": last.get("timestamp")
        }
    except json.JSONDecodeError:
        print("[Error] intent_log.jsonl の最終行を読み取れません。")
        return None


# === 類似度スコア計算 ===
def similarity(a: str, b: str) -> float:
    return SequenceMatcher(None, a or "", b or "").ratio()


# === Trace Map へ書き込み ===
def append_trace_map(data: dict):
    TRACE_MAP.parent.mkdir(parents=True, exist_ok=True)
    with TRACE_MAP.open("a", encoding="utf-8") as f:
        f.write(json.dumps(data, ensure_ascii=False) + "\n")


# === メイン処理 ===
def main():
    commit_info = get_latest_commit_info()
    intent_info = get_latest_intent_info()

    if not commit_info:
        print("[Info] コミット情報なし。")
        return
    if not intent_info:
        print("[Info] 意図情報なし。")
        return

    # 類似度計算
    score = similarity(commit_info["message"], intent_info["intent"])

    record = {
        "intent_id": intent_info["intent_id"],
        "intent": intent_info["intent"],
        "commit_id": commit_info["commit_id"],
        "message": commit_info["message"],
        "timestamp": commit_info["timestamp"],
        "match_score": round(score, 3)
    }

    append_trace_map(record)
    print(f"[Linked] intent={intent_info['intent_id']} ⇔ commit={commit_info['commit_id']} (score={round(score,3)})")


if __name__ == "__main__":
    main()