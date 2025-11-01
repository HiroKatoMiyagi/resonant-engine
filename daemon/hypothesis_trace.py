"""
hypothesis_trace.py
-------------------
Resonant Engine – Hypothesis Trace Layer (Phase 1)

このモジュールは「仮説追跡層」の基礎を担う。
ユノ（Yuno）が出した意図や指示を仮説（Hypothesis）として記録し、
observer_daemon や log_archiver と連携して「意図→結果→検証」を一貫して追跡する。

フェーズ（phase）引数は、仮説検証の各段階を識別するためのキーであり、
これにより複数段階の検証プロセスを明示的に管理可能とする。

ログパス (log_path) は外部から指定可能。observer_daemon との柔軟連携を想定。
"""

import json
import uuid
from datetime import datetime
from pathlib import Path

TRACE_FILE = Path(__file__).parent / "logs" / "hypothesis_trace_log.json"

# 外部設定ファイル (optional)
CONFIG_FILE = Path(__file__).parent / "config" / "observer_settings.json"
CHECK_INTERVAL = 10
if CONFIG_FILE.exists():
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            config = json.load(f)
            CHECK_INTERVAL = config.get("check_interval", CHECK_INTERVAL)
    except Exception as e:
        print(f"[⚠️ Config Load Error] {e}")


class HypothesisTrace:
    """
    HypothesisTraceクラスは、仮説の記録・更新・一覧表示を担う。
    仮説は意図(intent)、期待効果(expected_effect)、対象ファイル(target_files)などの情報を持ち、
    フェーズ(phase)により検証段階を管理する。

    ログファイルパスは外部から指定可能であり、observer_daemonとの柔軟連携を想定している。
    """

    def __init__(self, log_path=None):
        """
        初期化時にトレースログファイルを準備する。
        log_path引数で外部指定ログパスに対応。
        """
        self.trace_file = Path(log_path) if log_path else TRACE_FILE
        self.trace_file.parent.mkdir(parents=True, exist_ok=True)
        if not self.trace_file.exists():
            with open(self.trace_file, "w", encoding="utf-8") as f:
                json.dump([], f, ensure_ascii=False, indent=2)

    def _timestamp(self):
        """
        現在時刻をISO8601形式のタイムスタンプ文字列で返す。
        """
        return datetime.now().strftime("%Y-%m-%dT%H:%M:%S%z")

    def record(self, intent_text: str, expected_effect: str, target_files=None, origin="Yuno"):
        """
        新しい仮説を登録する。

        Parameters:
            intent_text (str): 仮説の意図を表すテキスト。
            expected_effect (str): 仮説の期待効果。
            target_files (list[str], optional): 対象ファイルのリスト。
            origin (str, optional): 仮説の発信元。

        Returns:
            str: 登録された仮説の一意ID。
        """
        hypothesis_id = f"HYP-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid.uuid4().hex[:6]}"
        entry = {
            "id": hypothesis_id,
            "intent_hash": hash(intent_text),
            "origin": origin,
            "timestamp": self._timestamp(),
            "target_files": target_files or [],
            "expected_effect": expected_effect,
            "status": "pending",
            # フェーズは初期登録時は未指定（None）とする
            "phase": None,
        }
        entries = []
        if self.trace_file.exists():
            try:
                with open(self.trace_file, "r", encoding="utf-8") as f:
                    entries = json.load(f)
            except json.JSONDecodeError:
                entries = []
        entries.append(entry)
        with open(self.trace_file, "w", encoding="utf-8") as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
        print(f"[🧠 Hypothesis Recorded] {hypothesis_id}: {expected_effect}")
        return hypothesis_id

    def update(self, hypothesis_id: str, status: str, result_diff: str = None, related_commit: str = None, phase: str = None):
        """
        仮説の状態を更新する。

        Parameters:
            hypothesis_id (str): 更新対象の仮説ID。
            status (str): 新しい状態（例："validated", "rejected"など）。
            result_diff (str, optional): 結果の差分情報。
            related_commit (str, optional): 関連コミットID。
            phase (str, optional): 仮説検証フェーズの識別キー。

        フェーズが指定された場合は、ログ出力に明示的に表示し、
        JSONログにも確実に記録する。
        """
        entries = []
        if self.trace_file.exists():
            with open(self.trace_file, "r", encoding="utf-8") as f:
                try:
                    entries = json.load(f)
                except json.JSONDecodeError:
                    entries = []
        updated = False
        for data in entries:
            if data["id"] == hypothesis_id:
                data["status"] = status
                if result_diff:
                    data["result_diff"] = result_diff
                if related_commit:
                    data["related_commit"] = related_commit
                if phase is not None:
                    data["phase"] = phase
                data["updated_at"] = self._timestamp()
                updated = True
        if updated:
            with open(self.trace_file, "w", encoding="utf-8") as f:
                json.dump(entries, f, ensure_ascii=False, indent=2)
            phase_info = f" [Phase: {phase}]" if phase is not None else ""
            print(f"[✅ Hypothesis Updated]{phase_info} {hypothesis_id} → {status}")
        else:
            print(f"[⚠️ Hypothesis Not Found] {hypothesis_id}")

    def list_all(self):
        """
        全ての仮説を一覧表示する。
        """
        if not self.trace_file.exists():
            print("No hypotheses recorded yet.")
            return
        with open(self.trace_file, "r", encoding="utf-8") as f:
            try:
                entries = json.load(f)
            except json.JSONDecodeError:
                entries = []
        for entry in entries:
            print(entry)


if __name__ == "__main__":
    tracer = HypothesisTrace()
    # テスト登録
    hyp_id = tracer.record("observer_daemonの外部更新テスト", "外部commitを検知してpullする", ["daemon/observer_daemon.py"])
    tracer.update(hyp_id, "validated", "diff example +3 insertions", "3aa9ebc", phase="verification")
    tracer.list_all()