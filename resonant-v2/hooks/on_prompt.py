#!/usr/bin/env python3
"""UserPromptSubmit hook: 失敗の確定 + 過去の失敗経路の検索 + 証拠の注入。

判定はしない。モデルが答え始める前に証拠を置くだけ（詳細は README / 仕様書参照）。
性能予算 200ms を守るため、依存ライブラリなし・埋め込みなし・常駐なし。
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, ".."))

from core import store, signals, render  # noqa: E402


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    cwd = data.get("cwd") or os.getcwd()
    session_id = data.get("session_id")
    prompt = data.get("prompt", "") or ""

    try:
        project_root = store.resolve_project_root(cwd)
        conn = store.connect(project_root)

        # (a) 直前の pending を、ユーザーの失敗報告で failed に確定する
        if signals.is_failure_utterance(prompt):
            store.mark_latest_pending_failed(
                conn, session_id, project_root,
                failure_signal=prompt[:300],
                evidence="user_utterance",
            )

        # (b) 今回の入力に近い failed 経路を検索する
        hits = store.search_failed(conn, project_root, prompt, limit=5)

        if hits:
            block = render.render_block(hits)
            store.log_injection(conn, project_root, session_id, prompt[:200], len(hits))
            print(json.dumps({
                "hookSpecificOutput": {
                    "hookEventName": "UserPromptSubmit",
                    "additionalContext": block,
                }
            }, ensure_ascii=False))
        conn.close()
    except Exception:
        # 何が起きてもセッションを止めない。証拠を出せなかっただけ、として通過する。
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
