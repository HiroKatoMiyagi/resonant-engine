"""FileModificationService - 統一ファイル操作サービス

Phase 3: コードレベルでの制約チェックを実現
"""

import asyncpg
import logging
import hashlib
import shutil
import json
from pathlib import Path
from typing import Optional
from datetime import datetime, timezone
from uuid import UUID

from .models import (
    FileModificationRequest, FileModificationResult,
    FileReadRequest, FileReadResult, FileOperationLog,
    ConstraintLevel, CheckResult, ConstraintCheckResult
)
from ..temporal_constraint.checker import TemporalConstraintChecker
from ..temporal_constraint.models import ModificationRequest

logger = logging.getLogger(__name__)


class FileModificationService:
    """統一ファイル操作サービス"""

    # 制約レベルごとの最小理由文字数
    MIN_REASON_LENGTH = {
        ConstraintLevel.CRITICAL: 100,  # 承認必須のため参考値
        ConstraintLevel.HIGH: 50,
        ConstraintLevel.MEDIUM: 20,
        ConstraintLevel.LOW: 0,
    }

    # バックアップディレクトリ
    BACKUP_DIR = Path("/app/backups")

    # 許可されるパスのプレフィックス（セキュリティ）
    ALLOWED_PATHS = [
        "/app/",
        "/home/user/",
        "/tmp/resonant/",
    ]

    # 禁止パターン（セキュリティ）
    FORBIDDEN_PATTERNS = [
        "..",
        "~",
        "/etc/",
        "/root/",
        "/var/",
        ".env",
        "credentials",
        "secret",
    ]

    def __init__(
        self,
        pool: asyncpg.Pool,
        constraint_checker: TemporalConstraintChecker,
        backup_dir: Optional[Path] = None
    ):
        self.pool = pool
        self.constraint_checker = constraint_checker
        if backup_dir:
            self.BACKUP_DIR = backup_dir
        # バックアップディレクトリの作成を試みる（失敗してもログのみ）
        try:
            self.BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        except OSError as e:
            logger.warning(f"Could not create backup directory {self.BACKUP_DIR}: {e}")

    # ==========================================
    # コア操作メソッド
    # ==========================================

    async def read_file(
        self,
        request: FileReadRequest
    ) -> FileReadResult:
        """
        ファイル読み込み（制約チェックなし）

        Args:
            request: 読み込みリクエスト

        Returns:
            FileReadResult: 読み込み結果
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=validation_error
            )

        path = Path(request.file_path)

        if not path.exists():
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=f"ファイルが存在しません: {request.file_path}"
            )

        try:
            content = path.read_text(encoding="utf-8")
            file_hash = self._calculate_hash(content)

            # ログ記録（読み込みも記録）
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="read",
                reason="file read",
                requested_by=request.requested_by,
                constraint_level="low",
                result="approved",
                new_content_hash=file_hash
            )

            return FileReadResult(
                success=True,
                file_path=request.file_path,
                content=content,
                file_hash=file_hash,
                message="ファイルを読み込みました"
            )

        except Exception as e:
            logger.error(f"File read error: {e}")
            return FileReadResult(
                success=False,
                file_path=request.file_path,
                content=None,
                file_hash=None,
                message=f"読み込みエラー: {str(e)}"
            )

    async def write_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル書き込み（制約チェック必須）

        Args:
            request: 書き込みリクエスト

        Returns:
            FileModificationResult: 書き込み結果
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return self._create_error_result(
                request, CheckResult.REJECTED, validation_error
            )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result == CheckResult.BLOCKED:
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=check_result.constraint_level.value,
                result="blocked"
            )
            return self._create_error_result(
                request, CheckResult.BLOCKED,
                "CRITICAL制約: このファイルは変更できません。手動承認が必要です。",
                constraint_level=check_result.constraint_level
            )

        if check_result.check_result == CheckResult.PENDING:
            # 理由が不十分
            min_length = self.MIN_REASON_LENGTH.get(
                check_result.constraint_level, 0
            )
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=check_result.constraint_level.value,
                result="rejected"
            )
            return self._create_error_result(
                request, CheckResult.PENDING,
                f"理由が不十分です（最低{min_length}文字必要、現在{len(request.reason)}文字）",
                constraint_level=check_result.constraint_level
            )

        # ファイル操作実行
        return await self._execute_write(request, check_result.constraint_level)

    async def delete_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル削除（制約チェック必須）
        """
        # パス検証
        validation_error = self._validate_path(request.file_path)
        if validation_error:
            return self._create_error_result(
                request, CheckResult.REJECTED, validation_error
            )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result in [CheckResult.BLOCKED, CheckResult.PENDING]:
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="delete",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=check_result.constraint_level.value,
                result="blocked" if check_result.check_result == CheckResult.BLOCKED else "rejected"
            )
            return self._create_error_result(
                request, check_result.check_result,
                f"ファイル削除がブロックされました: {check_result.constraint_level.value}制約",
                constraint_level=check_result.constraint_level
            )

        # 削除実行
        return await self._execute_delete(request, check_result.constraint_level)

    async def rename_file(
        self,
        request: FileModificationRequest
    ) -> FileModificationResult:
        """
        ファイル名変更（制約チェック必須）
        """
        if not request.new_path:
            return self._create_error_result(
                request, CheckResult.REJECTED,
                "new_path が指定されていません"
            )

        # 両方のパス検証
        for path in [request.file_path, request.new_path]:
            validation_error = self._validate_path(path)
            if validation_error:
                return self._create_error_result(
                    request, CheckResult.REJECTED, validation_error
                )

        # 制約チェック
        check_result = await self._check_constraint(request)

        if check_result.check_result in [CheckResult.BLOCKED, CheckResult.PENDING]:
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="rename",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=check_result.constraint_level.value,
                result="blocked" if check_result.check_result == CheckResult.BLOCKED else "rejected",
                metadata={"new_path": request.new_path}
            )
            return self._create_error_result(
                request, check_result.check_result,
                f"ファイル名変更がブロックされました: {check_result.constraint_level.value}制約",
                constraint_level=check_result.constraint_level
            )

        # リネーム実行
        return await self._execute_rename(request, check_result.constraint_level)

    async def check_constraint(
        self,
        request: FileModificationRequest
    ) -> ConstraintCheckResult:
        """
        制約チェックのみ実行（ファイル操作なし）
        """
        check_result = await self._check_constraint(request)

        min_length = self.MIN_REASON_LENGTH.get(
            check_result.constraint_level, 0
        )

        return ConstraintCheckResult(
            file_path=request.file_path,
            constraint_level=check_result.constraint_level.value,
            check_result=check_result.check_result.value,
            can_proceed=check_result.check_result == CheckResult.APPROVED,
            warning_message=check_result.warning_message,
            required_actions=check_result.required_actions,
            questions=check_result.questions,
            min_reason_length=min_length,
            current_reason_length=len(request.reason)
        )

    async def register_verification(
        self,
        user_id: str,
        file_path: str,
        verification_type: str,
        test_hours: float = 0,
        constraint_level: ConstraintLevel = ConstraintLevel.MEDIUM,
        description: Optional[str] = None,
        verified_by: Optional[str] = None
    ) -> UUID:
        """
        ファイル検証を登録
        """
        # temporal_constraint のConstraintLevelに変換
        from ..temporal_constraint.models import ConstraintLevel as TCConstraintLevel
        tc_constraint_level = TCConstraintLevel(constraint_level.value)

        return await self.constraint_checker.register_verification(
            user_id=user_id,
            file_path=file_path,
            verification_type=verification_type,
            test_hours=test_hours,
            constraint_level=tc_constraint_level,
            description=description,
            verified_by=verified_by
        )

    async def get_operation_logs(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        operation: Optional[str] = None,
        result: Optional[str] = None
    ) -> dict:
        """
        操作ログ取得
        """
        async with self.pool.acquire() as conn:
            # 総件数取得
            count_query = """
                SELECT COUNT(*) FROM file_operation_logs
                WHERE user_id = $1
            """
            params = [user_id]
            param_idx = 2

            if operation:
                count_query += f" AND operation = ${param_idx}"
                params.append(operation)
                param_idx += 1
            if result:
                count_query += f" AND result = ${param_idx}"
                params.append(result)
                param_idx += 1

            total = await conn.fetchval(count_query, *params)

            # ログ取得
            query = """
                SELECT id, file_path, operation, reason, requested_by,
                       constraint_level, result, created_at
                FROM file_operation_logs
                WHERE user_id = $1
            """
            params = [user_id]
            param_idx = 2

            if operation:
                query += f" AND operation = ${param_idx}"
                params.append(operation)
                param_idx += 1
            if result:
                query += f" AND result = ${param_idx}"
                params.append(result)
                param_idx += 1

            query += f" ORDER BY created_at DESC LIMIT ${param_idx} OFFSET ${param_idx + 1}"
            params.extend([limit, offset])

            rows = await conn.fetch(query, *params)

            logs = []
            for row in rows:
                log_dict = dict(row)
                # UUID と datetime を文字列に変換
                if log_dict.get('id'):
                    log_dict['id'] = str(log_dict['id'])
                if log_dict.get('created_at'):
                    log_dict['created_at'] = log_dict['created_at'].isoformat()
                logs.append(log_dict)

            return {
                "total": total or 0,
                "logs": logs
            }

    # ==========================================
    # プライベートメソッド
    # ==========================================

    def _validate_path(self, file_path: str) -> Optional[str]:
        """パス検証（セキュリティ）"""
        # 禁止パターンチェック
        for pattern in self.FORBIDDEN_PATTERNS:
            if pattern in file_path.lower():
                return f"禁止されたパスパターンが含まれています: {pattern}"

        # 許可パスチェック
        allowed = any(
            file_path.startswith(prefix)
            for prefix in self.ALLOWED_PATHS
        )
        if not allowed:
            return f"許可されていないパスです: {file_path}"

        return None

    async def _check_constraint(
        self,
        request: FileModificationRequest
    ):
        """制約チェック実行"""
        mod_request = ModificationRequest(
            user_id=request.user_id,
            file_path=request.file_path,
            modification_type=request.operation,
            modification_reason=request.reason,
            requested_by=request.requested_by
        )

        result = await self.constraint_checker.check_modification(mod_request)

        # temporal_constraint の ConstraintLevel を file_modification の ConstraintLevel に変換
        constraint_level = ConstraintLevel(result.constraint_level.value)

        # 結果オブジェクトを構築
        class CheckResultHolder:
            pass

        check_holder = CheckResultHolder()
        check_holder.constraint_level = constraint_level
        check_holder.warning_message = result.warning_message
        check_holder.required_actions = result.required_actions
        check_holder.questions = result.questions

        # CRITICAL は常にブロック
        if constraint_level == ConstraintLevel.CRITICAL:
            check_holder.check_result = CheckResult.BLOCKED

        # HIGH/MEDIUM で理由が不十分な場合
        elif constraint_level in [ConstraintLevel.HIGH, ConstraintLevel.MEDIUM]:
            min_length = self.MIN_REASON_LENGTH[constraint_level]
            if len(request.reason) < min_length and not request.force:
                check_holder.check_result = CheckResult.PENDING
            else:
                check_holder.check_result = CheckResult.APPROVED
        else:
            check_holder.check_result = CheckResult.APPROVED

        return check_holder

    async def _execute_write(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """書き込み実行"""
        path = Path(request.file_path)
        backup_path = None
        old_hash = None

        try:
            # バックアップ作成（既存ファイルの場合）
            if path.exists():
                old_content = path.read_text(encoding="utf-8")
                old_hash = self._calculate_hash(old_content)
                backup_path = self._create_backup(path, old_content)

            # 親ディレクトリ作成
            path.parent.mkdir(parents=True, exist_ok=True)

            # 書き込み
            path.write_text(request.content or "", encoding="utf-8")
            new_hash = self._calculate_hash(request.content or "")

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                new_content_hash=new_hash,
                backup_path=str(backup_path) if backup_path else None
            )

            return FileModificationResult(
                success=True,
                operation="write",
                file_path=request.file_path,
                message="ファイルを書き込みました",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path) if backup_path else None,
                file_hash=new_hash,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Write error: {e}")

            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="write",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="rejected",
                metadata={"error": str(e)}
            )

            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"書き込みエラー: {str(e)}",
                constraint_level=constraint_level
            )

    async def _execute_delete(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """削除実行"""
        path = Path(request.file_path)

        if not path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"ファイルが存在しません: {request.file_path}",
                constraint_level=constraint_level
            )

        try:
            # バックアップ作成
            old_content = path.read_text(encoding="utf-8")
            old_hash = self._calculate_hash(old_content)
            backup_path = self._create_backup(path, old_content)

            # 削除
            path.unlink()

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="delete",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                backup_path=str(backup_path)
            )

            return FileModificationResult(
                success=True,
                operation="delete",
                file_path=request.file_path,
                message="ファイルを削除しました",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path),
                file_hash=None,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Delete error: {e}")
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"削除エラー: {str(e)}",
                constraint_level=constraint_level
            )

    async def _execute_rename(
        self,
        request: FileModificationRequest,
        constraint_level: ConstraintLevel
    ) -> FileModificationResult:
        """リネーム実行"""
        old_path = Path(request.file_path)
        new_path = Path(request.new_path)

        if not old_path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"ファイルが存在しません: {request.file_path}",
                constraint_level=constraint_level
            )

        if new_path.exists():
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"移動先にファイルが既に存在します: {request.new_path}",
                constraint_level=constraint_level
            )

        try:
            # バックアップ作成
            old_content = old_path.read_text(encoding="utf-8")
            old_hash = self._calculate_hash(old_content)
            backup_path = self._create_backup(old_path, old_content)

            # 親ディレクトリ作成
            new_path.parent.mkdir(parents=True, exist_ok=True)

            # リネーム
            shutil.move(str(old_path), str(new_path))

            # ログ記録
            await self._log_operation(
                user_id=request.user_id,
                file_path=request.file_path,
                operation="rename",
                reason=request.reason,
                requested_by=request.requested_by,
                constraint_level=constraint_level.value,
                result="approved",
                old_content_hash=old_hash,
                new_content_hash=old_hash,
                backup_path=str(backup_path),
                metadata={"new_path": request.new_path}
            )

            return FileModificationResult(
                success=True,
                operation="rename",
                file_path=request.new_path,
                message=f"ファイルを移動しました: {request.file_path} → {request.new_path}",
                constraint_level=constraint_level,
                check_result=CheckResult.APPROVED,
                backup_path=str(backup_path),
                file_hash=old_hash,
                timestamp=datetime.now(timezone.utc)
            )

        except Exception as e:
            logger.error(f"Rename error: {e}")
            return self._create_error_result(
                request, CheckResult.REJECTED,
                f"リネームエラー: {str(e)}",
                constraint_level=constraint_level
            )

    def _calculate_hash(self, content: str) -> str:
        """SHA-256ハッシュ計算"""
        return f"sha256:{hashlib.sha256(content.encode()).hexdigest()}"

    def _create_backup(self, path: Path, content: str) -> Path:
        """バックアップ作成"""
        timestamp = int(datetime.now(timezone.utc).timestamp())
        backup_name = f"{path.name}.{timestamp}.bak"
        backup_path = self.BACKUP_DIR / path.parent.name / backup_name
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        backup_path.write_text(content, encoding="utf-8")
        return backup_path

    async def _log_operation(
        self,
        user_id: str,
        file_path: str,
        operation: str,
        reason: str,
        requested_by: str,
        constraint_level: str,
        result: str,
        old_content_hash: Optional[str] = None,
        new_content_hash: Optional[str] = None,
        backup_path: Optional[str] = None,
        metadata: Optional[dict] = None
    ):
        """操作ログを記録"""
        async with self.pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO file_operation_logs
                    (user_id, file_path, operation, reason, requested_by,
                     constraint_level, result, old_content_hash,
                     new_content_hash, backup_path, metadata)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11)
            """, user_id, file_path, operation, reason, requested_by,
                constraint_level, result, old_content_hash,
                new_content_hash, backup_path,
                json.dumps(metadata) if metadata else None)

    def _create_error_result(
        self,
        request: FileModificationRequest,
        check_result: CheckResult,
        message: str,
        constraint_level: ConstraintLevel = ConstraintLevel.LOW
    ) -> FileModificationResult:
        """エラー結果を作成"""
        return FileModificationResult(
            success=False,
            operation=request.operation,
            file_path=request.file_path,
            message=message,
            constraint_level=constraint_level,
            check_result=check_result,
            backup_path=None,
            file_hash=None,
            timestamp=datetime.now(timezone.utc)
        )
