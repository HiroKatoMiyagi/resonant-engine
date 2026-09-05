#!/usr/bin/env python3
"""PostToolUse hook: コマンドの非ゼロ終了/失敗を検出し、直近の pending を failed に確定する。

言葉に頼らない経路。黙っていても失敗が貯まる（これが手動記録との決定的な差）。
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, ".."))

from core import store, signals  # noqa: E402


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    cwd = data.get("cwd") or os.getcwd()
    session_id = data.get("session_id")
    tool_name = data.get("tool_name", "")
    tool_input = data.get("tool_input") or {}
    tool_response = data.get("tool_response") or {}

    try:
        failure_text = signals.detect_tool_failure(tool_name, tool_input, tool_response)
        if failure_text:
            project_root = store.resolve_project_root(cwd)
            conn = store.connect(project_root)
            store.mark_latest_pending_failed(
                conn, session_id, project_root,
                failure_signal=failure_text[:500],
                evidence="posttooluse",
            )
            conn.close()
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
