"""失敗シグナルの検出規則。判定はしない。『失敗の確定』と『失敗の要約』だけを担当する。"""
import json

FAILURE_UTTERANCE_KEYWORDS = [
    # 日本語
    "失敗", "動かない", "うごかない", "まだ直って", "まだ治って",
    "直ってない", "治ってない", "できない", "うまくいかない",
    "うまく行かない", "だめ", "駄目", "変わらない", "解決してない",
    "解決しない", "同じエラー", "同じ問題", "また同じ",
    # English
    "failed", "doesn't work", "does not work", "not working",
    "still broken", "still failing", "same error", "same issue",
    "didn't work", "did not work", "no luck",
]

# Bash 出力に現れる、非ゼロ終了に頼らずに失敗を推測するための代表的な文言。
# 誤検知の主要因はここなので、意図的に短く保つ。
FAILURE_TEXT_MARKERS = [
    "traceback (most recent call last)",
    "assertionerror",
    " failed",
    "error:",
    "exception:",
    "fatal:",
    "panic:",
]


def is_failure_utterance(text):
    if not text:
        return False
    t = text.lower()
    return any(kw.lower() in t for kw in FAILURE_UTTERANCE_KEYWORDS)


def _extract_exit_code(tool_response):
    if not isinstance(tool_response, dict):
        return None
    for key in ("exitCode", "exit_code", "returncode", "return_code", "code"):
        if key in tool_response:
            try:
                return int(tool_response[key])
            except (TypeError, ValueError):
                pass
    return None


def _summarize(tool_response, prefix=""):
    if isinstance(tool_response, dict):
        for key in ("stderr", "output", "stdout"):
            v = tool_response.get(key)
            if v:
                return (prefix + str(v))[:500]
        try:
            return (prefix + json.dumps(tool_response, ensure_ascii=False))[:500]
        except Exception:
            pass
    return (prefix + str(tool_response))[:500]


def detect_tool_failure(tool_name, tool_input, tool_response):
    """非ゼロ終了・失敗フラグ・代表的な失敗文言のいずれかを検出したら要約を返す。
    何も検出しなければ None（黙って通過。誤って failed 扱いしない）。"""
    if not isinstance(tool_response, dict):
        return None

    if tool_response.get("is_error") is True:
        return _summarize(tool_response)

    if tool_response.get("success") is False:
        return _summarize(tool_response)

    exit_code = _extract_exit_code(tool_response)
    if exit_code is not None and exit_code != 0:
        return _summarize(tool_response, prefix=f"exit={exit_code} ")

    if tool_name == "Bash":
        blob = " ".join(
            str(tool_response.get(k, "")) for k in ("stdout", "stderr", "output")
        )
        low = blob.lower()
        if any(marker in low for marker in FAILURE_TEXT_MARKERS):
            return _summarize(tool_response)

    return None
