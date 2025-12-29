#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Temporal Constraint CLI - 時間軸制約チェック付きファイル操作ツール
================================================================

AIエージェントが検証済みファイルを誤って変更することを防ぐための
「利用規約ベース」制約チェックツール。

使用例:
    # ファイル変更前に制約チェック
    python temporal_constraint_cli.py check --file path/to/file.py

    # 制約チェック付きでファイル書き込み（推奨）
    python temporal_constraint_cli.py write --file path/to/file.py --reason "バグ修正"
    
    # ファイルを検証済みとして登録
    python temporal_constraint_cli.py verify --file path/to/file.py --hours 10 --level high
"""

import sys
import os
import json
import hashlib
import asyncio
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

# Rich ライブラリ（オプション）
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich import box
    RICH_AVAILABLE = True
except ImportError:
    RICH_AVAILABLE = False

# プロジェクトルートをパスに追加
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class ConstraintLevel(str, Enum):
    """制約レベル"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class CheckResult(str, Enum):
    """チェック結果"""
    APPROVED = "approved"
    PENDING = "pending"
    REJECTED = "rejected"


# 制約レベルごとの設定
CONSTRAINT_CONFIG = {
    ConstraintLevel.CRITICAL: {
        "require_approval": True,
        "require_reason": True,
        "min_reason_length": 50,
        "questions": [
            "本当にこのファイルを変更する必要がありますか？",
            "変更後の再テスト時間を確保できますか？",
            "この変更のロールバック計画はありますか？"
        ],
        "color": "red",
        "emoji": "🔴"
    },
    ConstraintLevel.HIGH: {
        "require_approval": False,
        "require_reason": True,
        "min_reason_length": 20,
        "questions": [
            "この変更の目的を記録してください"
        ],
        "color": "yellow",
        "emoji": "🟠"
    },
    ConstraintLevel.MEDIUM: {
        "require_approval": False,
        "require_reason": False,
        "questions": [],
        "color": "blue",
        "emoji": "🟡"
    },
    ConstraintLevel.LOW: {
        "require_approval": False,
        "require_reason": False,
        "questions": [],
        "color": "green",
        "emoji": "🟢"
    }
}


class TemporalConstraintCLI:
    """時間軸制約CLIツール"""
    
    def __init__(self, use_rich: bool = True, api_base_url: Optional[str] = None):
        """
        Args:
            use_rich: Rich形式の出力を使用
            api_base_url: APIベースURL（None の場合はローカルJSONファイルを使用）
        """
        self.use_rich = use_rich and RICH_AVAILABLE
        self.api_base_url = api_base_url or os.getenv("RESONANT_API_URL")
        
        # ローカルストレージ（APIが使えない場合のフォールバック）
        self.local_storage_path = PROJECT_ROOT / "data" / "file_verifications.json"
        self.local_storage_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.use_rich:
            self.console = Console()
    
    def _load_local_storage(self) -> Dict[str, Any]:
        """ローカルストレージを読み込み"""
        if self.local_storage_path.exists():
            with open(self.local_storage_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return {"verifications": {}, "logs": []}
    
    def _save_local_storage(self, data: Dict[str, Any]):
        """ローカルストレージに保存"""
        with open(self.local_storage_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def _get_file_hash(self, file_path: Path) -> Optional[str]:
        """ファイルのSHA-256ハッシュを取得"""
        if not file_path.exists():
            return None
        
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def check(
        self,
        file_path: str,
        reason: Optional[str] = None,
        requested_by: str = "ai_agent"
    ) -> Dict[str, Any]:
        """
        ファイル変更の制約チェック
        
        Args:
            file_path: チェック対象ファイルパス
            reason: 変更理由
            requested_by: リクエスト元（'user', 'ai_agent', 'system'）
            
        Returns:
            チェック結果の辞書
        """
        path = Path(file_path).resolve()
        storage = self._load_local_storage()
        verifications = storage.get("verifications", {})
        
        # 正規化したパスをキーとして使用
        path_key = str(path)
        verification = verifications.get(path_key)
        
        if not verification:
            # 未登録ファイル = LOW制約（変更OK）
            result = {
                "file_path": str(path),
                "constraint_level": ConstraintLevel.LOW.value,
                "check_result": CheckResult.APPROVED.value,
                "warning_message": None,
                "required_actions": [],
                "questions": [],
                "can_proceed": True
            }
            self._log_check(storage, path_key, result, reason, requested_by)
            return result
        
        # 制約レベルを取得
        constraint_level = ConstraintLevel(verification.get("constraint_level", "low"))
        config = CONSTRAINT_CONFIG[constraint_level]
        
        # 警告メッセージ生成
        warning = self._generate_warning(verification)
        
        # 必要なアクション
        required_actions = []
        if config["require_approval"]:
            required_actions.append("approval_required")
        if config["require_reason"]:
            required_actions.append("reason_required")
        
        # 結果判定
        can_proceed = True
        check_result = CheckResult.APPROVED
        
        if constraint_level == ConstraintLevel.CRITICAL:
            # CRITICAL: 明示的な承認が必要
            check_result = CheckResult.PENDING
            can_proceed = False
        elif constraint_level == ConstraintLevel.HIGH:
            # HIGH: 十分な理由が必要
            if not reason or len(reason) < config["min_reason_length"]:
                check_result = CheckResult.PENDING
                can_proceed = False
        
        result = {
            "file_path": str(path),
            "constraint_level": constraint_level.value,
            "check_result": check_result.value,
            "warning_message": warning,
            "required_actions": required_actions,
            "questions": config["questions"],
            "can_proceed": can_proceed,
            "verification_info": verification
        }
        
        self._log_check(storage, path_key, result, reason, requested_by)
        return result
    
    def _generate_warning(self, verification: Dict[str, Any]) -> str:
        """警告メッセージ生成"""
        verified_at = verification.get("verified_at", "N/A")
        constraint_level = verification.get("constraint_level", "low")
        test_hours = verification.get("test_hours_invested", 0)
        verification_type = verification.get("verification_type", "unknown")
        
        config = CONSTRAINT_CONFIG.get(ConstraintLevel(constraint_level), CONSTRAINT_CONFIG[ConstraintLevel.LOW])
        
        warning_parts = [
            f"{config['emoji']} Temporal Constraint Warning!",
            f"",
            f"File: {verification.get('file_path', 'N/A')}",
            f"Status: VERIFIED (検証済み)",
            f"Constraint Level: {constraint_level.upper()}",
            f"",
            f"Verification History:",
            f"  - Type: {verification_type}",
            f"  - Verified: {verified_at}",
            f"  - Test Hours Invested: {test_hours}h",
        ]
        
        if verification.get("stable_since"):
            warning_parts.append(f"  - Stable Since: {verification['stable_since']}")
        
        if verification.get("description"):
            warning_parts.append(f"  - Note: {verification['description']}")
        
        return "\n".join(warning_parts)
    
    def _log_check(
        self,
        storage: Dict[str, Any],
        path_key: str,
        result: Dict[str, Any],
        reason: Optional[str],
        requested_by: str
    ):
        """チェックログを記録"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "file_path": path_key,
            "constraint_level": result["constraint_level"],
            "check_result": result["check_result"],
            "reason": reason,
            "requested_by": requested_by
        }
        
        if "logs" not in storage:
            storage["logs"] = []
        storage["logs"].append(log_entry)
        
        # ログは最大1000件保持
        if len(storage["logs"]) > 1000:
            storage["logs"] = storage["logs"][-1000:]
        
        self._save_local_storage(storage)
    
    def write_with_check(
        self,
        file_path: str,
        content: str,
        reason: str,
        requested_by: str = "ai_agent",
        force: bool = False
    ) -> Dict[str, Any]:
        """
        制約チェック付きでファイルに書き込む
        
        これがAIエージェント向けのメイン関数。
        検証済みファイルの場合は警告を表示し、確認を求める。
        
        Args:
            file_path: 書き込み先ファイルパス
            content: 書き込む内容
            reason: 変更理由（必須）
            requested_by: リクエスト元
            force: 強制書き込み（CRITICAL以外）
            
        Returns:
            結果の辞書
        """
        # まず制約チェック
        check_result = self.check(file_path, reason, requested_by)
        
        path = Path(file_path)
        constraint_level = ConstraintLevel(check_result["constraint_level"])
        
        # CRITICAL は絶対にブロック
        if constraint_level == ConstraintLevel.CRITICAL:
            return {
                "success": False,
                "action": "blocked",
                "message": "⛔ CRITICAL制約: このファイルは変更できません。手動承認が必要です。",
                "check_result": check_result,
                "file_written": False
            }
        
        # HIGH で理由が不十分
        config = CONSTRAINT_CONFIG[constraint_level]
        if constraint_level == ConstraintLevel.HIGH:
            if not reason or len(reason) < config["min_reason_length"]:
                return {
                    "success": False,
                    "action": "reason_required",
                    "message": f"⚠️ HIGH制約: 変更理由が不十分です（最低{config['min_reason_length']}文字必要）",
                    "check_result": check_result,
                    "file_written": False
                }
        
        # 警告を表示（HIGH/MEDIUM）
        if constraint_level in [ConstraintLevel.HIGH, ConstraintLevel.MEDIUM]:
            if check_result.get("warning_message"):
                if self.use_rich:
                    self.console.print(Panel(
                        check_result["warning_message"],
                        title=f"{config['emoji']} Temporal Constraint",
                        border_style=config["color"]
                    ))
                else:
                    print("=" * 60)
                    print(check_result["warning_message"])
                    print("=" * 60)
        
        # ファイル書き込み実行
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            
            # バックアップ作成（既存ファイルの場合）
            backup_path = None
            if path.exists():
                backup_path = path.with_suffix(path.suffix + ".bak")
                import shutil
                shutil.copy2(path, backup_path)
            
            # 書き込み
            with open(path, "w", encoding="utf-8") as f:
                f.write(content)
            
            return {
                "success": True,
                "action": "written",
                "message": f"✅ ファイルを書き込みました: {path}",
                "check_result": check_result,
                "file_written": True,
                "backup_path": str(backup_path) if backup_path else None,
                "file_hash": self._get_file_hash(path)
            }
            
        except Exception as e:
            return {
                "success": False,
                "action": "error",
                "message": f"❌ 書き込みエラー: {str(e)}",
                "check_result": check_result,
                "file_written": False,
                "error": str(e)
            }
    
    def verify(
        self,
        file_path: str,
        verification_type: str = "manual_test",
        test_hours: float = 0,
        constraint_level: str = "medium",
        description: Optional[str] = None,
        verified_by: str = "user"
    ) -> Dict[str, Any]:
        """
        ファイルを検証済みとして登録
        
        Args:
            file_path: 登録するファイルパス
            verification_type: 検証タイプ（'unit_test', 'integration_test', 'manual_test', 'production_stable'）
            test_hours: テストに費やした時間
            constraint_level: 制約レベル（'critical', 'high', 'medium', 'low'）
            description: 説明
            verified_by: 検証者
            
        Returns:
            登録結果
        """
        path = Path(file_path).resolve()
        
        if not path.exists():
            return {
                "success": False,
                "message": f"❌ ファイルが存在しません: {path}"
            }
        
        storage = self._load_local_storage()
        path_key = str(path)
        
        # 既存の検証情報があれば更新
        existing = storage["verifications"].get(path_key, {})
        existing_hours = existing.get("test_hours_invested", 0)
        
        verification = {
            "file_path": path_key,
            "file_hash": self._get_file_hash(path),
            "verification_type": verification_type,
            "test_hours_invested": existing_hours + test_hours,
            "constraint_level": constraint_level,
            "description": description,
            "verified_by": verified_by,
            "verified_at": datetime.now().isoformat()
        }
        
        storage["verifications"][path_key] = verification
        self._save_local_storage(storage)
        
        config = CONSTRAINT_CONFIG[ConstraintLevel(constraint_level)]
        
        return {
            "success": True,
            "message": f"{config['emoji']} ファイルを検証済みとして登録しました",
            "verification": verification
        }
    
    def mark_stable(self, file_path: str) -> Dict[str, Any]:
        """ファイルを安定稼働としてマーク（HIGHに昇格）"""
        path = Path(file_path).resolve()
        path_key = str(path)
        
        storage = self._load_local_storage()
        verification = storage["verifications"].get(path_key)
        
        if not verification:
            return {
                "success": False,
                "message": f"❌ 検証情報が見つかりません: {path}"
            }
        
        verification["stable_since"] = datetime.now().isoformat()
        verification["constraint_level"] = "high"
        
        self._save_local_storage(storage)
        
        return {
            "success": True,
            "message": f"🟠 ファイルを安定稼働としてマークしました（HIGH制約）",
            "verification": verification
        }
    
    def upgrade_to_critical(self, file_path: str, reason: str) -> Dict[str, Any]:
        """ファイルをCRITICALレベルに昇格"""
        path = Path(file_path).resolve()
        path_key = str(path)
        
        storage = self._load_local_storage()
        verification = storage["verifications"].get(path_key)
        
        if not verification:
            return {
                "success": False,
                "message": f"❌ 検証情報が見つかりません: {path}"
            }
        
        verification["constraint_level"] = "critical"
        verification["critical_reason"] = reason
        verification["upgraded_at"] = datetime.now().isoformat()
        
        self._save_local_storage(storage)
        
        return {
            "success": True,
            "message": f"🔴 ファイルをCRITICALレベルに昇格しました",
            "verification": verification
        }
    
    def status(self, file_path: Optional[str] = None) -> Dict[str, Any]:
        """
        ファイルまたは全体の制約状態を確認
        
        Args:
            file_path: 特定ファイル（Noneなら全体）
        """
        storage = self._load_local_storage()
        verifications = storage.get("verifications", {})
        
        if file_path:
            path = Path(file_path).resolve()
            path_key = str(path)
            verification = verifications.get(path_key)
            
            if not verification:
                return {
                    "file_path": str(path),
                    "constraint_level": "low",
                    "status": "unregistered",
                    "message": "🟢 未登録ファイル（制約なし）"
                }
            
            config = CONSTRAINT_CONFIG[ConstraintLevel(verification["constraint_level"])]
            return {
                "file_path": str(path),
                "constraint_level": verification["constraint_level"],
                "status": "registered",
                "message": f"{config['emoji']} {verification['constraint_level'].upper()} 制約",
                "verification": verification
            }
        else:
            # 全体統計
            stats = {
                "critical": 0,
                "high": 0,
                "medium": 0,
                "low": 0,
                "total": len(verifications)
            }
            
            for v in verifications.values():
                level = v.get("constraint_level", "low")
                stats[level] = stats.get(level, 0) + 1
            
            return {
                "status": "summary",
                "total_files": stats["total"],
                "by_level": stats,
                "files": list(verifications.keys())
            }
    
    def list_files(self, level: Optional[str] = None) -> None:
        """登録済みファイル一覧を表示"""
        storage = self._load_local_storage()
        verifications = storage.get("verifications", {})
        
        if not verifications:
            print("📭 登録済みファイルはありません")
            return
        
        if self.use_rich:
            table = Table(title="📋 Registered Files", box=box.ROUNDED)
            table.add_column("Level", style="cyan", width=10)
            table.add_column("File", style="white")
            table.add_column("Type", style="green")
            table.add_column("Hours", justify="right", style="magenta")
            table.add_column("Verified", style="yellow")
            
            for path, v in sorted(verifications.items(), key=lambda x: x[1].get("constraint_level", "low")):
                if level and v.get("constraint_level") != level:
                    continue
                
                config = CONSTRAINT_CONFIG[ConstraintLevel(v.get("constraint_level", "low"))]
                
                # パスを短縮
                display_path = path
                if len(display_path) > 50:
                    display_path = "..." + display_path[-47:]
                
                table.add_row(
                    f"{config['emoji']} {v.get('constraint_level', 'low').upper()}",
                    display_path,
                    v.get("verification_type", "N/A"),
                    f"{v.get('test_hours_invested', 0):.1f}h",
                    v.get("verified_at", "N/A")[:10]
                )
            
            self.console.print(table)
        else:
            print("=" * 80)
            print("📋 Registered Files")
            print("=" * 80)
            
            for path, v in sorted(verifications.items()):
                if level and v.get("constraint_level") != level:
                    continue
                
                config = CONSTRAINT_CONFIG[ConstraintLevel(v.get("constraint_level", "low"))]
                print(f"{config['emoji']} [{v.get('constraint_level', 'low').upper()}] {path}")
                print(f"   Type: {v.get('verification_type', 'N/A')}, Hours: {v.get('test_hours_invested', 0)}h")
                print()
    
    def show_logs(self, limit: int = 20) -> None:
        """チェックログを表示"""
        storage = self._load_local_storage()
        logs = storage.get("logs", [])[-limit:]
        
        if not logs:
            print("📭 ログはありません")
            return
        
        if self.use_rich:
            table = Table(title="📜 Recent Checks", box=box.ROUNDED)
            table.add_column("Time", style="cyan", width=20)
            table.add_column("File", style="white")
            table.add_column("Level", style="yellow")
            table.add_column("Result", style="green")
            table.add_column("By", style="magenta")
            
            for log in reversed(logs):
                file_path = log.get("file_path", "N/A")
                if len(file_path) > 40:
                    file_path = "..." + file_path[-37:]
                
                table.add_row(
                    log.get("timestamp", "N/A")[:19],
                    file_path,
                    log.get("constraint_level", "N/A"),
                    log.get("check_result", "N/A"),
                    log.get("requested_by", "N/A")
                )
            
            self.console.print(table)
        else:
            print("=" * 80)
            print("📜 Recent Checks")
            print("=" * 80)
            
            for log in reversed(logs):
                print(f"[{log.get('timestamp', 'N/A')[:19]}] {log.get('file_path', 'N/A')}")
                print(f"   Level: {log.get('constraint_level')}, Result: {log.get('check_result')}, By: {log.get('requested_by')}")
                print()


def main():
    """CLIエントリーポイント"""
    import argparse
    
    # 共通オプション用の親パーサー
    parent_parser = argparse.ArgumentParser(add_help=False)
    parent_parser.add_argument("--plain", action="store_true", 
                              help="Use plain text output (disable rich formatting)")
    
    parser = argparse.ArgumentParser(
        description="Temporal Constraint CLI - 時間軸制約チェック付きファイル操作ツール",
        epilog="""
使用例:
  # ファイルの制約チェック
  python temporal_constraint_cli.py check --file src/api/main.py
  
  # 制約チェック付きでファイル書き込み（AIエージェント向け推奨）
  python temporal_constraint_cli.py write --file src/api/main.py --reason "バグ修正: #123"
  
  # ファイルを検証済みとして登録
  python temporal_constraint_cli.py verify --file src/api/main.py --hours 5 --level high
  
  # 登録済みファイル一覧
  python temporal_constraint_cli.py list

詳細: https://docs.resonant-engine.dev/temporal-constraint
        """
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # check コマンド
    check_parser = subparsers.add_parser("check", help="ファイル変更の制約チェック", parents=[parent_parser])
    check_parser.add_argument("--file", "-f", required=True, help="チェック対象ファイルパス")
    check_parser.add_argument("--reason", "-r", help="変更理由")
    check_parser.add_argument("--by", default="ai_agent", help="リクエスト元（user/ai_agent/system）")
    
    # write コマンド（AIエージェント向けメイン）
    write_parser = subparsers.add_parser("write", help="制約チェック付きでファイル書き込み", parents=[parent_parser])
    write_parser.add_argument("--file", "-f", required=True, help="書き込み先ファイルパス")
    write_parser.add_argument("--content", "-c", help="書き込む内容（省略時は標準入力から読み込み）")
    write_parser.add_argument("--reason", "-r", required=True, help="変更理由（必須）")
    write_parser.add_argument("--by", default="ai_agent", help="リクエスト元")
    write_parser.add_argument("--force", action="store_true", help="警告を無視して強制書き込み（CRITICALは不可）")
    
    # verify コマンド
    verify_parser = subparsers.add_parser("verify", help="ファイルを検証済みとして登録", parents=[parent_parser])
    verify_parser.add_argument("--file", "-f", required=True, help="登録するファイルパス")
    verify_parser.add_argument("--type", "-t", default="manual_test", 
                              choices=["unit_test", "integration_test", "manual_test", "production_stable"],
                              help="検証タイプ")
    verify_parser.add_argument("--hours", type=float, default=0, help="テストに費やした時間")
    verify_parser.add_argument("--level", "-l", default="medium",
                              choices=["critical", "high", "medium", "low"],
                              help="制約レベル")
    verify_parser.add_argument("--description", "-d", help="説明")
    verify_parser.add_argument("--by", default="user", help="検証者")
    
    # mark-stable コマンド
    stable_parser = subparsers.add_parser("mark-stable", help="ファイルを安定稼働としてマーク", parents=[parent_parser])
    stable_parser.add_argument("--file", "-f", required=True, help="対象ファイルパス")
    
    # upgrade コマンド
    upgrade_parser = subparsers.add_parser("upgrade", help="ファイルをCRITICALレベルに昇格", parents=[parent_parser])
    upgrade_parser.add_argument("--file", "-f", required=True, help="対象ファイルパス")
    upgrade_parser.add_argument("--reason", "-r", required=True, help="昇格理由")
    
    # status コマンド
    status_parser = subparsers.add_parser("status", help="制約状態を確認", parents=[parent_parser])
    status_parser.add_argument("--file", "-f", help="特定ファイル（省略時は全体統計）")
    
    # list コマンド
    list_parser = subparsers.add_parser("list", help="登録済みファイル一覧", parents=[parent_parser])
    list_parser.add_argument("--level", "-l", choices=["critical", "high", "medium", "low"],
                            help="指定レベルのみ表示")
    
    # logs コマンド
    logs_parser = subparsers.add_parser("logs", help="チェックログを表示", parents=[parent_parser])
    logs_parser.add_argument("--limit", "-n", type=int, default=20, help="表示件数")
    
    args = parser.parse_args()
    
    # CLI初期化
    cli = TemporalConstraintCLI(use_rich=not getattr(args, 'plain', False))
    
    if args.command == "check":
        result = cli.check(args.file, args.reason, args.by)
        
        if result["can_proceed"]:
            print(f"✅ チェック通過: {result['constraint_level'].upper()}")
        else:
            print(f"⚠️ 確認が必要: {result['constraint_level'].upper()}")
            if result.get("warning_message"):
                print()
                print(result["warning_message"])
            if result.get("questions"):
                print()
                print("確認事項:")
                for q in result["questions"]:
                    print(f"  - {q}")
        
        # 終了コード: 通過=0, 確認必要=1
        sys.exit(0 if result["can_proceed"] else 1)
    
    elif args.command == "write":
        # 内容の取得
        if args.content:
            content = args.content
        else:
            # 標準入力から読み込み
            print("📝 内容を入力してください（Ctrl+D で終了）:")
            content = sys.stdin.read()
        
        result = cli.write_with_check(args.file, content, args.reason, args.by, args.force)
        
        print(result["message"])
        
        if result.get("backup_path"):
            print(f"📦 バックアップ: {result['backup_path']}")
        
        sys.exit(0 if result["success"] else 1)
    
    elif args.command == "verify":
        result = cli.verify(
            args.file,
            args.type,
            args.hours,
            args.level,
            args.description,
            args.by
        )
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
    
    elif args.command == "mark-stable":
        result = cli.mark_stable(args.file)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
    
    elif args.command == "upgrade":
        result = cli.upgrade_to_critical(args.file, args.reason)
        print(result["message"])
        sys.exit(0 if result["success"] else 1)
    
    elif args.command == "status":
        result = cli.status(args.file)
        
        if args.file:
            print(result["message"])
            if result.get("verification"):
                print(json.dumps(result["verification"], indent=2, ensure_ascii=False))
        else:
            print(f"📊 登録済みファイル: {result['total_files']}件")
            print()
            for level in ["critical", "high", "medium", "low"]:
                config = CONSTRAINT_CONFIG[ConstraintLevel(level)]
                count = result["by_level"].get(level, 0)
                print(f"  {config['emoji']} {level.upper()}: {count}件")
    
    elif args.command == "list":
        cli.list_files(args.level)
    
    elif args.command == "logs":
        cli.show_logs(args.limit)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
