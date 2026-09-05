"""UserPromptSubmit で注入するブロックの整形。
遮断ではなく提示。同一性の判断はモデルに委ねる（このモジュールは判断しない）。
"""


def _truncate(s, n):
    s = s or ""
    return s if len(s) <= n else s[: n - 1] + "…"


def render_block(hits):
    if not hits:
        return ""
    lines = [
        f"⚠ 過去に失敗した経路が見つかりました（候補 {len(hits)} 件）",
        "これらと今回の提案が同じ方向でないか、答える前に確認してください。",
        "同じ場合は、その旨を述べ、まだ潰していない方向を選択肢として示してください。",
        "",
    ]
    for h in hits:
        lines.append(f"■ {h.get('created_at', '?')} / branch: {h.get('branch') or '-'}")
        lines.append(f"  提案: {_truncate(h.get('proposal'), 200)}")
        lines.append(f"  結果: FAILED — {_truncate(h.get('failure_signal') or '(詳細なし)', 150)}")
        lines.append(f"  根拠: {h.get('evidence') or '-'}")
        lines.append("")
    return "\n".join(lines).strip()
