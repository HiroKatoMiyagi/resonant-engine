#!/usr/bin/env python3
"""Stop hook: そのターンでAIが出した提案を pending として保存する。

stdin: {"session_id": ..., "cwd": ..., "transcript_path": ..., ...}
transcript_path のJSONLから直近の assistant テキストを取り出す。
形式が想定と違っても、絶対にセッションを止めない（fail soft）。
"""
import json
import os
import sys

_THIS_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(_THIS_DIR, ".."))

from core import store  # noqa: E402


def extract_last_assistant_text(transcript_path):
    if not transcript_path or not os.path.exists(transcript_path):
        return None
    last_text = None
    try:
        with open(transcript_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    entry = json.loads(line)
                except Exception:
                    continue
                if not isinstance(entry, dict):
                    continue
                msg = entry.get("message")
                role, content = None, None
                if isinstance(msg, dict):
                    role = msg.get("role")
                    content = msg.get("content")
                else:
                    role = entry.get("role")
                    content = entry.get("content")
                if role != "assistant" or not content:
                    continue
                if isinstance(content, str):
                    last_text = content
                elif isinstance(content, list):
                    texts = [
                        b.get("text", "")
                        for b in content
                        if isinstance(b, dict) and b.get("type") == "text"
                    ]
                    if texts:
                        last_text = "\n".join(texts)
    except Exception:
        return last_text
    return last_text


def main():
    try:
        raw = sys.stdin.read()
        data = json.loads(raw) if raw.strip() else {}
    except Exception:
        data = {}

    cwd = data.get("cwd") or os.getcwd()
    session_id = data.get("session_id")
    transcript_path = data.get("transcript_path")

    try:
        proposal = extract_last_assistant_text(transcript_path)
        if proposal:
            project_root = store.resolve_project_root(cwd)
            branch = store.get_branch(project_root)
            conn = store.connect(project_root)
            store.insert_pending(conn, session_id, project_root, branch, proposal[:2000])
            conn.close()
    except Exception:
        pass

    sys.exit(0)


if __name__ == "__main__":
    main()
