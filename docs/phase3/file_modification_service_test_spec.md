# FileModificationService テスト仕様書

**作成日**: 2025-12-30
**作成者**: Kana (Claude Opus 4.5)
**関連文書**: `file_modification_service_spec.md`
**バージョン**: 1.0.0

---

## 1. テスト概要

### 1.1 目的

FileModificationServiceが正しく動作し、以下を保証することを検証する：

1. ファイル操作（読み込み、書き込み、削除、リネーム）が正常に動作する
2. 制約チェックが正しく機能する
3. セキュリティ検証（パス検証）が機能する
4. 操作ログが正しく記録される
5. バックアップが正しく作成される

### 1.2 テスト環境

| 項目 | 値 |
|------|-----|
| OS | Linux / macOS |
| Python | 3.11+ |
| Docker | Docker Compose |
| DB | PostgreSQL 15 (pgvector) |
| プロジェクトパス | `/home/user/resonant-engine` |

### 1.3 前提条件

- Docker環境が起動している
- PostgreSQLに必要なテーブルが作成されている
- `.env`ファイルが正しく設定されている
- venv環境がアクティベートされている

---

## 2. テストカテゴリ

| カテゴリ | 説明 | 優先度 |
|---------|------|--------|
| ユニットテスト | 各メソッドの単体テスト | 必須 |
| 統合テスト | コンポーネント間の連携テスト | 必須 |
| APIテスト | エンドポイントの動作確認 | 必須 |
| セキュリティテスト | パス検証、入力検証 | 必須 |
| E2Eテスト | シナリオベースのテスト | 重要 |
| パフォーマンステスト | レスポンス時間測定 | 推奨 |

---

## 3. フェーズ別テスト仕様

### 3.1 Day 1: データモデル・スキーマ

#### テスト1.1: PostgreSQLテーブル作成確認

**目的**: 必要なテーブルが作成されていること

**手順**:
```bash
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard -c "
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name IN ('file_operation_logs', 'file_backups');
"
```

**期待結果**:
```
    table_name
-------------------
 file_operation_logs
 file_backups
(2 rows)
```

**成功基準**: 2テーブルが存在する

---

#### テスト1.2: インデックス確認

**目的**: 必要なインデックスが作成されていること

**手順**:
```bash
docker exec -it resonant_postgres psql -U resonant -d resonant_dashboard -c "
SELECT indexname FROM pg_indexes
WHERE tablename = 'file_operation_logs';
"
```

**期待結果**:
```
           indexname
-------------------------------
 file_operation_logs_pkey
 idx_file_op_logs_user
 idx_file_op_logs_file
 idx_file_op_logs_time
 idx_file_op_logs_operation
 idx_file_op_logs_result
```

**成功基準**: 6個以上のインデックスが存在する

---

#### テスト1.3: Pydanticモデルインポート確認

**目的**: モデルが正しくインポートできること

**手順**:
```bash
cd /home/user/resonant-engine
source venv/bin/activate

python -c "
from app.services.file_modification.models import (
    ConstraintLevel,
    CheckResult,
    FileModificationRequest,
    FileModificationResult,
    FileReadRequest,
    FileReadResult,
    FileOperationLog
)
print('✅ All models imported successfully')
print(f'  - ConstraintLevel: {list(ConstraintLevel)}')
print(f'  - CheckResult: {list(CheckResult)}')
"
```

**期待結果**:
```
✅ All models imported successfully
  - ConstraintLevel: [<ConstraintLevel.CRITICAL: 'critical'>, ...]
  - CheckResult: [<CheckResult.APPROVED: 'approved'>, ...]
```

**成功基準**: エラーなしでインポート成功

---

### 3.2 Day 2: サービス実装

#### テスト2.1: サービスインスタンス作成

**目的**: FileModificationServiceが正しく初期化できること

**手順**:
```python
# tests/services/file_modification/test_service_init.py

import pytest
from unittest.mock import MagicMock, AsyncMock
from app.services.file_modification.service import FileModificationService
from app.services.temporal_constraint.checker import TemporalConstraintChecker

def test_service_initialization():
    """サービスが正しく初期化されること"""
    mock_pool = MagicMock()
    mock_checker = MagicMock(spec=TemporalConstraintChecker)

    service = FileModificationService(
        pool=mock_pool,
        constraint_checker=mock_checker
    )

    assert service.pool == mock_pool
    assert service.constraint_checker == mock_checker
    assert service.BACKUP_DIR.exists()
```

**成功基準**: テストがパスする

---

#### テスト2.2: パス検証テスト

**目的**: セキュリティ検証が正しく機能すること

**手順**:
```python
# tests/services/file_modification/test_path_validation.py

import pytest
from app.services.file_modification.service import FileModificationService

class TestPathValidation:
    """パス検証テスト"""

    @pytest.fixture
    def service(self):
        mock_pool = MagicMock()
        mock_checker = MagicMock()
        return FileModificationService(mock_pool, mock_checker)

    def test_allowed_path_app(self, service):
        """許可されたパス /app/ が通過すること"""
        result = service._validate_path("/app/src/main.py")
        assert result is None

    def test_allowed_path_home(self, service):
        """許可されたパス /home/user/ が通過すること"""
        result = service._validate_path("/home/user/project/file.py")
        assert result is None

    def test_forbidden_path_traversal(self, service):
        """ディレクトリトラバーサルがブロックされること"""
        result = service._validate_path("/app/../etc/passwd")
        assert result is not None
        assert ".." in result

    def test_forbidden_path_etc(self, service):
        """/etc/ がブロックされること"""
        result = service._validate_path("/etc/passwd")
        assert result is not None

    def test_forbidden_path_env(self, service):
        """.env がブロックされること"""
        result = service._validate_path("/app/.env")
        assert result is not None

    def test_forbidden_path_credentials(self, service):
        """credentials がブロックされること"""
        result = service._validate_path("/app/credentials.json")
        assert result is not None

    def test_disallowed_path(self, service):
        """許可リストにないパスがブロックされること"""
        result = service._validate_path("/usr/local/bin/script.sh")
        assert result is not None
```

**成功基準**: 全テストがパスする

---

#### テスト2.3: ファイル読み込みテスト

**目的**: read_fileが正しく動作すること

**手順**:
```python
# tests/services/file_modification/test_read.py

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

@pytest.mark.asyncio
async def test_read_file_success():
    """ファイル読み込みが成功すること"""
    # テスト用ファイル作成
    with tempfile.NamedTemporaryFile(
        mode='w', suffix='.py', delete=False,
        dir='/tmp/resonant/'
    ) as f:
        f.write("# Test content\nprint('hello')")
        temp_path = f.name

    try:
        mock_pool = MagicMock()
        mock_pool.acquire = AsyncMock()
        mock_checker = MagicMock()

        service = FileModificationService(mock_pool, mock_checker)

        # ALLOWED_PATHS に /tmp/resonant/ を追加するか、
        # テスト用にオーバーライド
        service.ALLOWED_PATHS.append('/tmp/')

        request = FileReadRequest(
            user_id="test_user",
            file_path=temp_path,
            requested_by="test"
        )

        result = await service.read_file(request)

        assert result.success is True
        assert "Test content" in result.content
        assert result.file_hash.startswith("sha256:")
    finally:
        Path(temp_path).unlink()

@pytest.mark.asyncio
async def test_read_file_not_found():
    """存在しないファイルでエラーになること"""
    mock_pool = MagicMock()
    mock_checker = MagicMock()
    service = FileModificationService(mock_pool, mock_checker)
    service.ALLOWED_PATHS.append('/tmp/')

    request = FileReadRequest(
        user_id="test_user",
        file_path="/tmp/resonant/nonexistent.py",
        requested_by="test"
    )

    result = await service.read_file(request)

    assert result.success is False
    assert "存在しません" in result.message
```

**成功基準**: 全テストがパスする

---

#### テスト2.4: ファイル書き込みテスト（制約なし）

**目的**: LOW制約でのwrite_fileが正しく動作すること

**手順**:
```python
# tests/services/file_modification/test_write.py

import pytest
import tempfile
from pathlib import Path

@pytest.mark.asyncio
async def test_write_file_low_constraint():
    """LOW制約でファイル書き込みが成功すること"""
    mock_pool = MagicMock()
    mock_pool.acquire = AsyncMock()

    # 制約チェッカーをモック
    mock_checker = MagicMock()
    mock_checker.check_modification = AsyncMock(return_value=MagicMock(
        constraint_level=ConstraintLevel.LOW,
        check_result=CheckResult.APPROVED,
        warning_message=None,
        required_actions=[],
        questions=[]
    ))

    service = FileModificationService(mock_pool, mock_checker)
    service.ALLOWED_PATHS.append('/tmp/')

    request = FileModificationRequest(
        user_id="test_user",
        file_path="/tmp/resonant/test_write.py",
        operation="write",
        content="# New file content",
        reason="Test write",
        requested_by="test"
    )

    result = await service.write_file(request)

    assert result.success is True
    assert result.check_result == CheckResult.APPROVED
    assert result.file_hash is not None

    # ファイルが作成されたことを確認
    assert Path("/tmp/resonant/test_write.py").exists()

    # クリーンアップ
    Path("/tmp/resonant/test_write.py").unlink()
```

**成功基準**: テストがパスする

---

#### テスト2.5: 制約レベル別テスト

**目的**: 各制約レベルで正しく動作すること

**手順**:
```python
# tests/services/file_modification/test_constraints.py

import pytest
from app.services.file_modification.models import ConstraintLevel, CheckResult

class TestConstraintLevels:
    """制約レベル別テスト"""

    @pytest.mark.asyncio
    async def test_critical_blocked(self, service_with_critical_constraint):
        """CRITICAL制約でブロックされること"""
        request = FileModificationRequest(
            user_id="test_user",
            file_path="/app/core/critical_file.py",
            operation="write",
            content="new content",
            reason="I really need to change this file because of important bug fix",
            requested_by="ai_agent"
        )

        result = await service_with_critical_constraint.write_file(request)

        assert result.success is False
        assert result.check_result == CheckResult.BLOCKED
        assert "CRITICAL" in result.message

    @pytest.mark.asyncio
    async def test_high_short_reason_rejected(self, service_with_high_constraint):
        """HIGH制約で短い理由が拒否されること"""
        request = FileModificationRequest(
            user_id="test_user",
            file_path="/app/important/file.py",
            operation="write",
            content="new content",
            reason="short",  # 50文字未満
            requested_by="ai_agent"
        )

        result = await service_with_high_constraint.write_file(request)

        assert result.success is False
        assert result.check_result == CheckResult.PENDING
        assert "50" in result.message  # 最低50文字必要

    @pytest.mark.asyncio
    async def test_high_long_reason_approved(self, service_with_high_constraint):
        """HIGH制約で十分な理由が承認されること"""
        long_reason = "バグ修正: ユーザー認証のエラーハンドリングを改善。" * 3  # 50文字以上

        request = FileModificationRequest(
            user_id="test_user",
            file_path="/app/important/file.py",
            operation="write",
            content="new content",
            reason=long_reason,
            requested_by="ai_agent"
        )

        result = await service_with_high_constraint.write_file(request)

        assert result.success is True
        assert result.check_result == CheckResult.APPROVED

    @pytest.mark.asyncio
    async def test_medium_short_reason_rejected(self, service_with_medium_constraint):
        """MEDIUM制約で短すぎる理由が拒否されること"""
        request = FileModificationRequest(
            user_id="test_user",
            file_path="/app/src/file.py",
            operation="write",
            content="new content",
            reason="fix",  # 20文字未満
            requested_by="ai_agent"
        )

        result = await service_with_medium_constraint.write_file(request)

        assert result.success is False
        assert "20" in result.message

    @pytest.mark.asyncio
    async def test_medium_valid_reason_approved(self, service_with_medium_constraint):
        """MEDIUM制約で十分な理由が承認されること"""
        request = FileModificationRequest(
            user_id="test_user",
            file_path="/app/src/file.py",
            operation="write",
            content="new content",
            reason="バグ修正: エラーハンドリングの改善",  # 20文字以上
            requested_by="ai_agent"
        )

        result = await service_with_medium_constraint.write_file(request)

        assert result.success is True
```

**成功基準**: 全テストがパスする

---

### 3.3 Day 3: API実装

#### テスト3.1: APIエンドポイント存在確認

**目的**: 全エンドポイントが登録されていること

**手順**:
```bash
curl -s http://localhost:8000/openapi.json | jq '.paths | keys[]' | grep files
```

**期待結果**:
```
"/api/v1/files/check"
"/api/v1/files/delete"
"/api/v1/files/logs"
"/api/v1/files/read"
"/api/v1/files/register-verification"
"/api/v1/files/rename"
"/api/v1/files/write"
```

**成功基準**: 7個のエンドポイントが存在する

---

#### テスト3.2: 制約チェックAPI

**目的**: /api/v1/files/check が正しく動作すること

**手順**:
```bash
# LOW制約ファイル
curl -s -X POST http://localhost:8000/api/v1/files/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "file_path": "/app/src/new_file.py",
    "operation": "write",
    "reason": "test"
  }' | jq .
```

**期待結果**:
```json
{
    "file_path": "/app/src/new_file.py",
    "constraint_level": "low",
    "check_result": "approved",
    "can_proceed": true,
    "warning_message": null,
    "required_actions": [],
    "questions": [],
    "min_reason_length": 0,
    "current_reason_length": 4
}
```

**成功基準**: can_proceed が true

---

#### テスト3.3: ファイル書き込みAPI

**目的**: /api/v1/files/write が正しく動作すること

**手順**:
```bash
# 1. ファイル書き込み
curl -s -X POST http://localhost:8000/api/v1/files/write \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "file_path": "/app/test_api_write.py",
    "operation": "write",
    "content": "# API Test\nprint(\"hello\")",
    "reason": "APIテスト用ファイル作成",
    "requested_by": "test"
  }' | jq .
```

**期待結果**:
```json
{
    "success": true,
    "operation": "write",
    "file_path": "/app/test_api_write.py",
    "message": "ファイルを書き込みました",
    "constraint_level": "low",
    "check_result": "approved",
    "backup_path": null,
    "file_hash": "sha256:...",
    "timestamp": "..."
}
```

**成功基準**: success が true

---

#### テスト3.4: ファイル読み込みAPI

**目的**: /api/v1/files/read が正しく動作すること

**手順**:
```bash
curl -s "http://localhost:8000/api/v1/files/read?user_id=test_user&file_path=/app/test_api_write.py" | jq .
```

**期待結果**:
```json
{
    "success": true,
    "file_path": "/app/test_api_write.py",
    "content": "# API Test\nprint(\"hello\")",
    "file_hash": "sha256:...",
    "message": "ファイルを読み込みました"
}
```

**成功基準**: content が正しい

---

#### テスト3.5: 操作ログAPI

**目的**: /api/v1/files/logs が正しく動作すること

**手順**:
```bash
curl -s "http://localhost:8000/api/v1/files/logs?user_id=test_user&limit=10" | jq .
```

**期待結果**:
```json
{
    "total": 2,
    "logs": [
        {
            "id": "...",
            "file_path": "/app/test_api_write.py",
            "operation": "read",
            "result": "approved",
            "...": "..."
        },
        {
            "id": "...",
            "file_path": "/app/test_api_write.py",
            "operation": "write",
            "result": "approved",
            "...": "..."
        }
    ]
}
```

**成功基準**: ログが記録されている

---

### 3.4 Day 4: AIエージェント統合

#### テスト4.1: CLIとAPIの連携

**目的**: CLIからAPIを呼び出せること

**手順**:
```bash
# CLIで制約チェック
python utils/temporal_constraint_cli.py check --file /app/src/main.py

# 結果を確認
echo $?  # 0 = 通過, 1 = 確認必要
```

**成功基準**: 終了コードが適切

---

#### テスト4.2: シナリオテスト - AIエージェントのファイル変更

**目的**: AIエージェントのワークフローが動作すること

**手順**:
```python
# tests/integration/test_ai_agent_workflow.py

import pytest
import httpx

@pytest.mark.asyncio
async def test_ai_agent_file_modification_workflow():
    """AIエージェントのファイル変更ワークフローテスト"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # 1. 制約チェック
        check_response = await client.post(
            "/api/v1/files/check",
            json={
                "user_id": "ai_agent_test",
                "file_path": "/app/src/feature.py",
                "operation": "write",
                "reason": "新機能の追加: ユーザー認証にMFA対応を追加"
            }
        )
        check_result = check_response.json()

        # 2. 通過可能か確認
        if not check_result["can_proceed"]:
            # 理由を拡充して再チェック
            min_length = check_result["min_reason_length"]
            extended_reason = "新機能の追加: " + "a" * (min_length + 10)

            check_response = await client.post(
                "/api/v1/files/check",
                json={
                    "user_id": "ai_agent_test",
                    "file_path": "/app/src/feature.py",
                    "operation": "write",
                    "reason": extended_reason
                }
            )
            check_result = check_response.json()

        # 3. ファイル書き込み
        if check_result["can_proceed"]:
            write_response = await client.post(
                "/api/v1/files/write",
                json={
                    "user_id": "ai_agent_test",
                    "file_path": "/app/src/feature.py",
                    "operation": "write",
                    "content": "# New feature\ndef mfa_authenticate():\n    pass",
                    "reason": check_result.get("reason", "新機能追加"),
                    "requested_by": "ai_agent"
                }
            )
            write_result = write_response.json()

            assert write_result["success"] is True
            assert write_result["backup_path"] is not None or write_result["check_result"] == "approved"

        # 4. ログ確認
        logs_response = await client.get(
            "/api/v1/files/logs",
            params={"user_id": "ai_agent_test", "limit": 5}
        )
        logs = logs_response.json()

        assert logs["total"] > 0
```

**成功基準**: ワークフローが正常に完了

---

### 3.5 Day 5: テスト・ドキュメント

#### テスト5.1: E2Eテスト - 完全ワークフロー

**目的**: 全機能が連携して動作すること

**手順**:
```bash
#!/bin/bash
# tests/e2e/test_file_modification_e2e.sh

set -e

BASE_URL="http://localhost:8000"
USER_ID="e2e_test_user"
TEST_FILE="/app/e2e_test_file.py"

echo "=== E2E Test: FileModificationService ==="

# 1. 検証登録
echo "1. 検証登録..."
curl -s -X POST "${BASE_URL}/api/v1/files/register-verification" \
  -G \
  --data-urlencode "user_id=${USER_ID}" \
  --data-urlencode "file_path=${TEST_FILE}" \
  --data-urlencode "verification_type=integration_test" \
  --data-urlencode "test_hours=5" \
  --data-urlencode "constraint_level=high" | jq .

# 2. 制約チェック（短い理由）
echo "2. 制約チェック（短い理由）..."
SHORT_CHECK=$(curl -s -X POST "${BASE_URL}/api/v1/files/check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"file_path\": \"${TEST_FILE}\",
    \"operation\": \"write\",
    \"reason\": \"短い理由\"
  }")
echo $SHORT_CHECK | jq .

CAN_PROCEED=$(echo $SHORT_CHECK | jq -r '.can_proceed')
if [ "$CAN_PROCEED" == "false" ]; then
    echo "   ✅ 短い理由が正しくブロックされた"
else
    echo "   ❌ 短い理由がブロックされなかった"
    exit 1
fi

# 3. 制約チェック（十分な理由）
echo "3. 制約チェック（十分な理由）..."
LONG_REASON="バグ修正: ユーザー認証のエラーハンドリングを改善。既存のtry-catchが不十分でエラーが握りつぶされていた問題を修正"
LONG_CHECK=$(curl -s -X POST "${BASE_URL}/api/v1/files/check" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"file_path\": \"${TEST_FILE}\",
    \"operation\": \"write\",
    \"reason\": \"${LONG_REASON}\"
  }")
echo $LONG_CHECK | jq .

CAN_PROCEED=$(echo $LONG_CHECK | jq -r '.can_proceed')
if [ "$CAN_PROCEED" == "true" ]; then
    echo "   ✅ 十分な理由で通過"
else
    echo "   ❌ 十分な理由でも通過しなかった"
    exit 1
fi

# 4. ファイル書き込み
echo "4. ファイル書き込み..."
WRITE_RESULT=$(curl -s -X POST "${BASE_URL}/api/v1/files/write" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"file_path\": \"${TEST_FILE}\",
    \"operation\": \"write\",
    \"content\": \"# E2E Test File\\nprint('hello e2e')\",
    \"reason\": \"${LONG_REASON}\",
    \"requested_by\": \"e2e_test\"
  }")
echo $WRITE_RESULT | jq .

SUCCESS=$(echo $WRITE_RESULT | jq -r '.success')
if [ "$SUCCESS" == "true" ]; then
    echo "   ✅ ファイル書き込み成功"
else
    echo "   ❌ ファイル書き込み失敗"
    exit 1
fi

# 5. ファイル読み込み確認
echo "5. ファイル読み込み確認..."
READ_RESULT=$(curl -s "${BASE_URL}/api/v1/files/read?user_id=${USER_ID}&file_path=${TEST_FILE}")
echo $READ_RESULT | jq .

CONTENT=$(echo $READ_RESULT | jq -r '.content')
if [[ "$CONTENT" == *"E2E Test File"* ]]; then
    echo "   ✅ ファイル内容が正しい"
else
    echo "   ❌ ファイル内容が不正"
    exit 1
fi

# 6. 操作ログ確認
echo "6. 操作ログ確認..."
LOGS=$(curl -s "${BASE_URL}/api/v1/files/logs?user_id=${USER_ID}&limit=10")
echo $LOGS | jq .

LOG_COUNT=$(echo $LOGS | jq -r '.total')
if [ "$LOG_COUNT" -ge 2 ]; then
    echo "   ✅ ログが記録されている（${LOG_COUNT}件）"
else
    echo "   ❌ ログが不足している"
    exit 1
fi

# 7. ファイル削除
echo "7. ファイル削除..."
DELETE_RESULT=$(curl -s -X POST "${BASE_URL}/api/v1/files/delete" \
  -H "Content-Type: application/json" \
  -d "{
    \"user_id\": \"${USER_ID}\",
    \"file_path\": \"${TEST_FILE}\",
    \"operation\": \"delete\",
    \"reason\": \"${LONG_REASON}\",
    \"requested_by\": \"e2e_test\"
  }")
echo $DELETE_RESULT | jq .

echo ""
echo "=== E2E Test Complete ==="
echo "✅ All tests passed!"
```

**成功基準**: 全ステップが成功

---

#### テスト5.2: パフォーマンステスト

**目的**: レスポンス時間が目標内であること

**手順**:
```python
# tests/performance/test_file_modification_perf.py

import pytest
import time
import httpx

@pytest.mark.asyncio
async def test_read_file_performance():
    """read_file のレスポンス時間 < 100ms"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # ウォームアップ
        await client.get("/api/v1/files/read", params={
            "user_id": "perf_test",
            "file_path": "/app/main.py"
        })

        # 計測
        start = time.time()
        for _ in range(10):
            await client.get("/api/v1/files/read", params={
                "user_id": "perf_test",
                "file_path": "/app/main.py"
            })
        end = time.time()

        avg_time = (end - start) / 10 * 1000  # ms
        print(f"Average read_file time: {avg_time:.2f}ms")

        assert avg_time < 100, f"read_file too slow: {avg_time}ms"

@pytest.mark.asyncio
async def test_check_constraint_performance():
    """check_constraint のレスポンス時間 < 100ms"""
    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # ウォームアップ
        await client.post("/api/v1/files/check", json={
            "user_id": "perf_test",
            "file_path": "/app/main.py",
            "operation": "write",
            "reason": "test"
        })

        # 計測
        start = time.time()
        for _ in range(10):
            await client.post("/api/v1/files/check", json={
                "user_id": "perf_test",
                "file_path": "/app/main.py",
                "operation": "write",
                "reason": "test"
            })
        end = time.time()

        avg_time = (end - start) / 10 * 1000  # ms
        print(f"Average check_constraint time: {avg_time:.2f}ms")

        assert avg_time < 100, f"check_constraint too slow: {avg_time}ms"
```

**成功基準**: 全操作が目標時間内

---

## 4. 最終検証テスト

### 4.1 統合動作確認

**目的**: 全コンポーネントが連携して動作すること

**手順**:
```bash
cd /home/user/resonant-engine
source venv/bin/activate

# 全テスト実行
pytest tests/services/file_modification/ -v --tb=short
pytest tests/integration/test_file_modification*.py -v --tb=short
```

**期待結果**: 全テストがパス

---

### 4.2 既存機能との互換性確認

**目的**: 既存のTemporal Constraint機能が引き続き動作すること

**手順**:
```bash
# 既存APIの動作確認
curl -s -X POST http://localhost:8000/api/v1/temporal-constraint/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "file_path": "/app/src/main.py",
    "modification_type": "edit",
    "modification_reason": "test",
    "requested_by": "user"
  }' | jq .

# 既存CLIの動作確認
python utils/temporal_constraint_cli.py status
```

**成功基準**: 既存機能が正常動作

---

## 5. テスト結果記録テンプレート

```markdown
# FileModificationService テスト結果

**実行日**: YYYY-MM-DD
**実行者**: [名前]
**環境**: [環境情報]

## Day 1: データモデル・スキーマ
| テスト | 結果 | 備考 |
|--------|------|------|
| 1.1 テーブル作成 | ✅/❌ | |
| 1.2 インデックス確認 | ✅/❌ | |
| 1.3 モデルインポート | ✅/❌ | |

## Day 2: サービス実装
| テスト | 結果 | 備考 |
|--------|------|------|
| 2.1 サービス初期化 | ✅/❌ | |
| 2.2 パス検証 | ✅/❌ | X/Y passed |
| 2.3 ファイル読み込み | ✅/❌ | |
| 2.4 ファイル書き込み | ✅/❌ | |
| 2.5 制約レベル別 | ✅/❌ | X/Y passed |

## Day 3: API実装
| テスト | 結果 | 備考 |
|--------|------|------|
| 3.1 エンドポイント存在 | ✅/❌ | X/7 found |
| 3.2 制約チェックAPI | ✅/❌ | |
| 3.3 書き込みAPI | ✅/❌ | |
| 3.4 読み込みAPI | ✅/❌ | |
| 3.5 ログAPI | ✅/❌ | |

## Day 4: AIエージェント統合
| テスト | 結果 | 備考 |
|--------|------|------|
| 4.1 CLI連携 | ✅/❌ | |
| 4.2 ワークフロー | ✅/❌ | |

## Day 5: 最終検証
| テスト | 結果 | 備考 |
|--------|------|------|
| 5.1 E2Eテスト | ✅/❌ | |
| 5.2 パフォーマンス | ✅/❌ | read: Xms, check: Xms |

## 総合結果
- **成功**: X/Y テスト
- **失敗**: X テスト
- **判定**: 合格/不合格

## 問題点と対応
1. [問題1] → [対応]
2. [問題2] → [対応]
```

---

## 6. トラブルシューティング

### 6.1 テーブルが作成されない

**症状**: `file_operation_logs` テーブルが存在しない

**対処**:
```bash
# マイグレーション手動実行
docker exec -i resonant_postgres psql -U resonant -d resonant_dashboard < \
  docker/postgres/010_file_modification_service.sql
```

### 6.2 インポートエラー

**症状**: `ModuleNotFoundError: No module named 'app.services.file_modification'`

**対処**:
1. ディレクトリ構造確認:
   ```bash
   ls -la backend/app/services/file_modification/
   ```
2. `__init__.py` 存在確認
3. PYTHONPATH 確認

### 6.3 パス検証でブロックされる

**症状**: 正当なパスがブロックされる

**対処**:
1. `ALLOWED_PATHS` を確認
2. テスト環境用のパスを追加

### 6.4 パフォーマンスが遅い

**症状**: レスポンス時間が目標を超える

**対処**:
1. DB接続プール確認
2. インデックス存在確認
3. コネクション数確認

---

## 7. 成功基準サマリー

| Day | 必須条件 |
|-----|---------|
| Day 1 | テーブル作成、モデルインポート成功 |
| Day 2 | 全ユニットテストパス |
| Day 3 | 全APIエンドポイント動作 |
| Day 4 | AIエージェントワークフロー動作 |
| Day 5 | E2Eテスト成功、パフォーマンス目標達成 |
| **最終** | 全テスト90%以上パス |

---

**テスト仕様書作成完了**

この仕様書に従ってテストを実行してください。

---

**作成日**: 2025-12-30
**作成者**: Kana (Claude Opus 4.5)
**バージョン**: 1.0.0
