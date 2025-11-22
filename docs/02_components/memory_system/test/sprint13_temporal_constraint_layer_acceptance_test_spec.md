# Sprint 13: Temporal Constraint Layer - 受け入れテスト仕様書

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**対象バージョン**: Sprint 13
**総テストケース数**: 25

---

## 0. テスト哲学

### 時間軸制約の本質
```yaml
testing_philosophy:
    essence: "検証工数の価値を保護できているか"
    focus:
        - 検証済みファイルの変更検知
        - 警告レベルの適切な判定
        - 依存関係の影響分析
        - 承認フローの正常動作
    principles:
        - 警告レイテンシ < 200ms
        - False Positive Rate < 10%（不要な警告）
        - 影響分析レイテンシ < 500ms
        - Re-evaluation Phase統合動作
```

---

## 1. 環境セットアップ（Docker）

### AC-00: PostgreSQLマイグレーション実行

**優先度**: P0（必須）
**タイプ**: 環境構築

**Given**:
- Dockerコンテナが起動可能
- `docker/postgres/010_temporal_constraint_layer.sql` が存在

**When**:
- マイグレーションを実行:
  ```bash
  cd docker
  docker-compose up -d postgres
  docker exec -i resonant-postgres psql -U postgres -d resonant_engine < postgres/010_temporal_constraint_layer.sql
  ```

**Then**:
- 4つのテーブルが作成される:
  - `file_verifications`
  - `verification_history`
  - `file_dependencies`
  - `change_approvals`
- 15個以上のインデックスが作成される

**検証コマンド**:
```sql
-- テーブル確認
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name IN (
    'file_verifications', 'verification_history',
    'file_dependencies', 'change_approvals'
);

-- インデックス確認
SELECT indexname FROM pg_indexes
WHERE tablename IN ('file_verifications', 'verification_history',
    'file_dependencies', 'change_approvals');
```

---

## 2. FileVerificationRegistry（検証レジストリ）

### AC-01: 新規ファイル検証の登録

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- PostgreSQL接続が有効

**When**:
- 検証を登録:
  ```python
  verification = await registry.register_verification(
      user_id="hiroki",
      file_path="bridge/memory/service.py",
      verification_status="verified",
      test_hours=12.5,
      test_cases_count=45,
      coverage_percent=92.5,
      verified_by="hiroki"
  )
  ```

**Then**:
- FileVerificationが作成される
- verification.test_hours == 12.5
- verification.test_cases_count == 45
- verification.coverage_percent == 92.5
- verified_at が設定される
- expires_at が90日後に設定される

**検証コマンド**:
```python
verification = await registry.register_verification(
    user_id="hiroki",
    file_path="bridge/memory/service.py",
    verification_status="verified",
    test_hours=12.5,
    test_cases_count=45,
    coverage_percent=92.5,
    verified_by="hiroki"
)

assert verification.test_hours == 12.5
assert verification.test_cases_count == 45
assert verification.coverage_percent == 92.5
assert verification.verified_at is not None
assert verification.expires_at is not None

# Check expiry is ~90 days from now
from datetime import timedelta
expected_expiry = verification.verified_at + timedelta(days=90)
assert abs((verification.expires_at - expected_expiry).total_seconds()) < 60
```

---

### AC-02: 重複ファイル検証の拒否

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「service.py」の検証が登録済み

**When**:
- 同じファイルを再度登録しようとする

**Then**:
- ValueError例外が発生
- メッセージ: "Verification for 'service.py' already exists"

**検証コマンド**:
```python
# First registration
await registry.register_verification(
    user_id="hiroki",
    file_path="service.py",
    verification_status="pending",
    verified_by="hiroki"
)

# Second registration should fail
with pytest.raises(ValueError) as exc_info:
    await registry.register_verification(
        user_id="hiroki",
        file_path="service.py",
        verification_status="verified",
        verified_by="hiroki"
    )

assert "already exists" in str(exc_info.value)
```

---

### AC-03: 検証ステータスの更新

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「service.py」が "pending" 状態で登録済み

**When**:
- ステータスを "verified" に更新:
  ```python
  updated = await registry.update_verification(
      verification_id=verification.id,
      verification_status="verified",
      test_hours=15.0,
      test_cases_count=50,
      changed_by="hiroki",
      reason="All tests passed"
  )
  ```

**Then**:
- verification_status == "verified"
- test_hours == 15.0
- verified_at が設定される
- expires_at が設定される
- VerificationHistoryが作成される

**検証コマンド**:
```python
updated = await registry.update_verification(
    verification_id=verification.id,
    verification_status="verified",
    test_hours=15.0,
    test_cases_count=50,
    changed_by="hiroki",
    reason="All tests passed"
)

assert updated.verification_status == "verified"
assert updated.test_hours == 15.0
assert updated.verified_at is not None

# Verify history record
history = await registry.get_verification_history(verification.id)
assert len(history) >= 1
assert history[0].action in ["verified", "reverified"]
assert history[0].new_status == "verified"
```

---

### AC-04: 検証の失効

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「service.py」が "verified" 状態

**When**:
- 検証を失効:
  ```python
  history = await registry.invalidate_verification(
      verification_id=verification.id,
      reason="File modified",
      invalidated_by="hiroki"
  )
  ```

**Then**:
- verification_status == "needs_reverification"
- VerificationHistoryのaction == "invalidated"
- history.old_status == "verified"
- history.new_status == "needs_reverification"

**検証コマンド**:
```python
history = await registry.invalidate_verification(
    verification_id=verification.id,
    reason="File modified",
    invalidated_by="hiroki"
)

assert history.action == "invalidated"
assert history.old_status == "verified"
assert history.new_status == "needs_reverification"

# Verify the verification is now invalidated
updated = await registry.get_verification_by_id(verification.id)
assert updated.verification_status == "needs_reverification"
```

---

### AC-05: 期限切れ間近の検証取得

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 3つのファイル検証が存在:
  - file_a: expires_at = 7日後
  - file_b: expires_at = 30日後
  - file_c: expires_at = 100日後

**When**:
- 14日以内に期限切れの検証を取得:
  ```python
  expiring = await registry.get_expiring_verifications(
      user_id="hiroki",
      days_until_expiry=14
  )
  ```

**Then**:
- 1件のみ返される（file_a）
- expires_at順でソート

**検証コマンド**:
```python
expiring = await registry.get_expiring_verifications(
    user_id="hiroki",
    days_until_expiry=14
)

assert len(expiring) == 1
assert expiring[0].file_path == "file_a"
```

---

## 3. ChangeGuard（変更ガード）

### AC-06: 検証済みファイルの変更警告

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「service.py」が "verified" 状態
- test_hours = 12.5

**When**:
- 変更チェックを実行:
  ```python
  warning = await guard.check_file_modification(
      user_id="hiroki",
      file_path="service.py"
  )
  ```

**Then**:
- ChangeWarningが返される
- warning_level == "critical" または "warning"
- test_hours == 12.5
- message に警告メッセージが含まれる

**検証コマンド**:
```python
warning = await guard.check_file_modification(
    user_id="hiroki",
    file_path="service.py"
)

assert warning is not None
assert warning.warning_level in ["warning", "critical"]
assert warning.test_hours == 12.5
assert "検証済み" in warning.message or "verified" in warning.message.lower()
```

---

### AC-07: 未検証ファイルは警告なし

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「new_file.py」は検証登録なし

**When**:
- 変更チェックを実行

**Then**:
- None が返される（警告なし）

**検証コマンド**:
```python
warning = await guard.check_file_modification(
    user_id="hiroki",
    file_path="new_file.py"
)

assert warning is None
```

---

### AC-08: 警告レベル判定 - Critical

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「core.py」が "verified" 状態
- test_hours = 25.0（10時間以上）

**When**:
- 変更チェックを実行

**Then**:
- warning_level == "critical"

**検証コマンド**:
```python
# Register with high test hours
await registry.register_verification(
    user_id="hiroki",
    file_path="core.py",
    verification_status="verified",
    test_hours=25.0,
    verified_by="hiroki"
)

warning = await guard.check_file_modification(
    user_id="hiroki",
    file_path="core.py"
)

assert warning.warning_level == "critical"
```

---

### AC-09: 警告レベル判定 - Info

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- ファイル「helper.py」が "verified" 状態
- test_hours = 1.5（2時間未満）

**When**:
- 変更チェックを実行

**Then**:
- warning_level == "info"

**検証コマンド**:
```python
await registry.register_verification(
    user_id="hiroki",
    file_path="helper.py",
    verification_status="verified",
    test_hours=1.5,
    verified_by="hiroki"
)

warning = await guard.check_file_modification(
    user_id="hiroki",
    file_path="helper.py"
)

assert warning.warning_level == "info"
```

---

### AC-10: 承認リクエストの作成

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- ファイル検証が登録済み

**When**:
- 承認リクエストを作成:
  ```python
  approval = await guard.request_approval(
      verification_id=verification.id,
      requested_change="Add new method",
      requested_by="hiroki",
      approval_type="normal"
  )
  ```

**Then**:
- ChangeApprovalが作成される
- approval_status == "pending"
- approval_type == "normal"

**検証コマンド**:
```python
approval = await guard.request_approval(
    verification_id=verification.id,
    requested_change="Add new method",
    requested_by="hiroki",
    approval_type="normal"
)

assert approval.approval_status == "pending"
assert approval.approval_type == "normal"
assert approval.requested_change == "Add new method"
```

---

### AC-11: 変更の承認

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- 承認リクエストが存在（status = "pending"）

**When**:
- 承認を実行:
  ```python
  approved = await guard.approve_change(
      approval_id=approval.id,
      decided_by="admin",
      approval_reason="Reviewed and approved"
  )
  ```

**Then**:
- approval_status == "approved"
- decided_by == "admin"
- decided_at が設定される

**検証コマンド**:
```python
approved = await guard.approve_change(
    approval_id=approval.id,
    decided_by="admin",
    approval_reason="Reviewed and approved"
)

assert approved.approval_status == "approved"
assert approved.decided_by == "admin"
assert approved.decided_at is not None
```

---

### AC-12: 変更のバイパス（緊急時）

**優先度**: P1（重要）
**タイプ**: 統合テスト

**Given**:
- 承認リクエストが存在（status = "pending"）

**When**:
- バイパスを実行:
  ```python
  bypassed = await guard.bypass_change(
      approval_id=approval.id,
      bypassed_by="admin",
      bypass_reason="Emergency hotfix required"
  )
  ```

**Then**:
- approval_status == "bypassed"
- decided_by == "admin"
- approval_reason に緊急理由が記録される

**検証コマンド**:
```python
bypassed = await guard.bypass_change(
    approval_id=approval.id,
    bypassed_by="admin",
    bypass_reason="Emergency hotfix required"
)

assert bypassed.approval_status == "bypassed"
assert bypassed.decided_by == "admin"
assert "Emergency" in bypassed.approval_reason
```

---

## 4. DependencyAnalyzer（依存関係分析）

### AC-13: 依存関係の登録

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在

**When**:
- 依存関係を登録:
  ```python
  dep = await analyzer.register_dependency(
      user_id="hiroki",
      source_file="service.py",
      dependent_file="models.py",
      dependency_type="import"
  )
  ```

**Then**:
- FileDependencyが作成される
- source_file == "service.py"
- dependent_file == "models.py"
- dependency_type == "import"

**検証コマンド**:
```python
dep = await analyzer.register_dependency(
    user_id="hiroki",
    source_file="service.py",
    dependent_file="models.py",
    dependency_type="import"
)

assert dep.source_file == "service.py"
assert dep.dependent_file == "models.py"
assert dep.dependency_type == "import"
assert dep.is_active is True
```

---

### AC-14: 直接依存の取得

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- models.py → service.py, router.py への依存関係が登録済み

**When**:
- 依存先を取得:
  ```python
  deps = await analyzer.get_dependents(
      user_id="hiroki",
      file_path="models.py",
      include_indirect=False
  )
  ```

**Then**:
- 2件の依存関係が返される
- service.py と router.py が含まれる

**検証コマンド**:
```python
deps = await analyzer.get_dependents(
    user_id="hiroki",
    file_path="models.py",
    include_indirect=False
)

assert len(deps) == 2
dep_files = [d.dependent_file for d in deps]
assert "service.py" in dep_files
assert "router.py" in dep_files
```

---

### AC-15: 間接依存を含む取得

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 依存関係チェーン: models.py → service.py → router.py → main.py

**When**:
- 間接依存を含めて取得:
  ```python
  deps = await analyzer.get_dependents(
      user_id="hiroki",
      file_path="models.py",
      include_indirect=True
  )
  ```

**Then**:
- 3件の依存関係が返される（直接+間接）

**検証コマンド**:
```python
deps = await analyzer.get_dependents(
    user_id="hiroki",
    file_path="models.py",
    include_indirect=True
)

assert len(deps) >= 3
```

---

### AC-16: 影響分析レポート生成

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- models.py が検証済み（test_hours=25.0）
- 依存ファイル3件（各test_hours=10.0）

**When**:
- 影響分析を実行:
  ```python
  report = await analyzer.analyze_change_impact(
      user_id="hiroki",
      file_path="models.py"
  )
  ```

**Then**:
- total_affected_test_hours >= 55.0
- total_affected_files >= 4
- risk_level == "critical" または "high"
- recommendations が含まれる

**検証コマンド**:
```python
report = await analyzer.analyze_change_impact(
    user_id="hiroki",
    file_path="models.py"
)

assert report.total_affected_test_hours >= 55.0
assert report.total_affected_files >= 4
assert report.risk_level in ["high", "critical"]
assert len(report.recommendations) > 0
```

---

### AC-17: リスクレベル判定

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- 異なる合計テスト工数のシナリオ

**When**:
- リスクレベルを判定

**Then**:
- total_hours < 10 → "low"
- 10 <= total_hours < 30 → "medium"
- 30 <= total_hours < 50 → "high"
- total_hours >= 50 → "critical"

**検証コマンド**:
```python
# Test risk level determination
assert analyzer._determine_risk_level(5.0) == "low"
assert analyzer._determine_risk_level(20.0) == "medium"
assert analyzer._determine_risk_level(40.0) == "high"
assert analyzer._determine_risk_level(60.0) == "critical"
```

---

## 5. API統合テスト

### AC-18: POST /api/v1/verifications 検証登録

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在

**When**:
- POST /api/v1/verifications?user_id=hiroki
  ```json
  {
    "file_path": "bridge/memory/service.py",
    "verification_status": "verified",
    "test_hours": 12.5,
    "test_cases_count": 45,
    "coverage_percent": 92.5
  }
  ```

**Then**:
- HTTP 200 OK
- Response body に検証情報が含まれる

**検証コマンド**:
```python
response = await client.post(
    "/api/v1/verifications?user_id=hiroki",
    json={
        "file_path": "bridge/memory/service.py",
        "verification_status": "verified",
        "test_hours": 12.5,
        "test_cases_count": 45,
        "coverage_percent": 92.5
    }
)

assert response.status_code == 200
data = response.json()
assert data["file_path"] == "bridge/memory/service.py"
assert data["test_hours"] == 12.5
```

---

### AC-19: POST /api/v1/verifications/check 変更前チェック

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在
- ファイル「service.py」が検証済み

**When**:
- POST /api/v1/verifications/check?user_id=hiroki
  ```json
  {
    "file_path": "service.py"
  }
  ```

**Then**:
- HTTP 200 OK
- Response body に警告情報が含まれる

**検証コマンド**:
```python
response = await client.post(
    "/api/v1/verifications/check?user_id=hiroki",
    json={"file_path": "service.py"}
)

assert response.status_code == 200
data = response.json()
assert data["warning_level"] in ["info", "warning", "critical"]
assert "message" in data
```

---

### AC-20: GET /api/v1/dependencies/{file_path}/impact 影響分析

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在
- ファイル「models.py」が検証済み、依存関係あり

**When**:
- GET /api/v1/dependencies/models.py/impact?user_id=hiroki

**Then**:
- HTTP 200 OK
- Response body に影響分析レポートが含まれる

**検証コマンド**:
```python
response = await client.get(
    "/api/v1/dependencies/models.py/impact?user_id=hiroki"
)

assert response.status_code == 200
data = response.json()
assert "total_affected_files" in data
assert "risk_level" in data
assert "recommendations" in data
```

---

### AC-21: PUT /api/v1/approvals/{id}/approve 承認実行

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- 承認リクエストが存在

**When**:
- PUT /api/v1/approvals/{approval_id}/approve?user_id=admin
  ```json
  {
    "approval_reason": "Reviewed and approved"
  }
  ```

**Then**:
- HTTP 200 OK
- approval_status == "approved"

**検証コマンド**:
```python
response = await client.put(
    f"/api/v1/approvals/{approval.id}/approve?user_id=admin",
    json={"approval_reason": "Reviewed and approved"}
)

assert response.status_code == 200
data = response.json()
assert data["approval_status"] == "approved"
```

---

## 6. パフォーマンステスト

### AC-22: 変更前チェックレイテンシ < 200ms

**優先度**: P1（重要）
**タイプ**: パフォーマンステスト

**Given**:
- User「hiroki」が存在
- 50件のファイル検証が登録済み

**When**:
- 変更前チェックを実行

**Then**:
- 処理時間 < 200ms

**検証コマンド**:
```python
import time

start = time.time()
warning = await guard.check_file_modification(
    user_id="hiroki",
    file_path="service.py"
)
elapsed = (time.time() - start) * 1000

assert elapsed < 200  # 200ms以内
```

---

### AC-23: 影響分析レイテンシ < 500ms

**優先度**: P1（重要）
**タイプ**: パフォーマンステスト

**Given**:
- User「hiroki」が存在
- 依存関係チェーン深さ5レベル

**When**:
- 影響分析を実行

**Then**:
- 処理時間 < 500ms

**検証コマンド**:
```python
import time

start = time.time()
report = await analyzer.analyze_change_impact(
    user_id="hiroki",
    file_path="models.py"
)
elapsed = (time.time() - start) * 1000

assert elapsed < 500  # 500ms以内
```

---

## 7. データベース制約テスト

### AC-24: file_verificationsテーブル制約

**優先度**: P1（重要）
**タイプ**: データベーステスト

**Given**:
- PostgreSQL接続

**When**:
- 無効なverification_statusで挿入を試行

**Then**:
- CHECK制約違反エラー

**検証コマンド**:
```sql
-- Should fail: invalid verification_status
INSERT INTO file_verifications (
    user_id, file_path, verification_status, verified_by
) VALUES (
    'hiroki', 'test.py', 'invalid_status', 'hiroki'
);

-- Expected: ERROR: new row for relation "file_verifications" violates check constraint
```

---

### AC-25: file_dependencies UNIQUE制約

**優先度**: P1（重要）
**タイプ**: データベーステスト

**Given**:
- PostgreSQL接続
- 依存関係 (hiroki, service.py, models.py) が存在

**When**:
- 同じ依存関係を再挿入

**Then**:
- UNIQUE制約違反エラー（ON CONFLICTなし）
- または更新される（ON CONFLICT DO UPDATE）

**検証コマンド**:
```sql
-- Test UNIQUE constraint
INSERT INTO file_dependencies (
    user_id, source_file, dependent_file, dependency_type
) VALUES (
    'hiroki', 'service.py', 'models.py', 'import'
);

-- Second insert should trigger conflict
INSERT INTO file_dependencies (
    user_id, source_file, dependent_file, dependency_type
) VALUES (
    'hiroki', 'service.py', 'models.py', 'import'
)
ON CONFLICT (user_id, source_file, dependent_file)
DO UPDATE SET is_active = TRUE, detected_at = NOW();
```

---

## 完了基準

### Tier 1: 必須要件（全て満たす必要あり）
- [ ] AC-00: Docker環境セットアップ完了
- [ ] AC-01 ~ AC-21: 全21テストケースがPASS
- [ ] 単体テスト15件以上作成・PASS
- [ ] E2Eテスト4件以上作成・PASS

### Tier 2: 品質要件
- [ ] AC-22, AC-23: パフォーマンステストPASS
- [ ] False Positive Rate < 10%
- [ ] コードカバレッジ > 80%

---

## Docker環境構築手順

### 1. PostgreSQLコンテナ起動

```bash
cd /path/to/resonant-engine/docker
docker-compose up -d postgres
```

### 2. マイグレーション実行

```bash
# Sprint 12, 13マイグレーション実行
docker exec -i resonant-postgres psql -U postgres -d resonant_engine < postgres/009_term_drift_detection.sql
docker exec -i resonant-postgres psql -U postgres -d resonant_engine < postgres/010_temporal_constraint_layer.sql
```

### 3. マイグレーション確認

```bash
docker exec -it resonant-postgres psql -U postgres -d resonant_engine -c "\dt"
```

**期待される出力**（Sprint 13テーブル）:
```
          List of relations
 Schema |         Name         | Type  |  Owner
--------+----------------------+-------+----------
 public | change_approvals     | table | postgres
 public | file_dependencies    | table | postgres
 public | file_verifications   | table | postgres
 public | verification_history | table | postgres
```

### 4. インデックス確認

```bash
docker exec -it resonant-postgres psql -U postgres -d resonant_engine -c "SELECT indexname FROM pg_indexes WHERE tablename LIKE 'file_%' OR tablename LIKE 'verification_%' OR tablename LIKE 'change_%';"
```

---

## テスト実行コマンド

### 全テスト実行
```bash
pytest tests/temporal_constraint/ -v
```

### 単体テストのみ
```bash
pytest tests/temporal_constraint/test_models.py tests/temporal_constraint/test_registry.py tests/temporal_constraint/test_guard.py tests/temporal_constraint/test_analyzer.py -v
```

### E2Eテストのみ
```bash
pytest tests/integration/test_temporal_constraint_e2e.py -v
```

### パフォーマンステスト
```bash
pytest tests/temporal_constraint/test_performance.py -v --benchmark
```

---

## トラブルシューティング

### マイグレーションエラー

**問題**: `relation "file_verifications" already exists`

**対策**:
```sql
-- テーブルを削除して再作成
DROP TABLE IF EXISTS change_approvals CASCADE;
DROP TABLE IF EXISTS file_dependencies CASCADE;
DROP TABLE IF EXISTS verification_history CASCADE;
DROP TABLE IF EXISTS file_verifications CASCADE;
```

### 警告が出ない

**問題**: 検証済みファイルなのに警告が出ない

**対策**:
1. verification_status が "verified" であることを確認
2. expires_at が現在時刻より後であることを確認
3. ユーザーIDが一致していることを確認

### 依存関係が検出されない

**問題**: 依存ファイルがリストに出ない

**対策**:
1. is_active が TRUE であることを確認
2. user_id が一致していることを確認
3. source_file / dependent_file の向きを確認

### パフォーマンス問題

**問題**: 影響分析が500msを超える

**対策**:
1. インデックスが正しく作成されていることを確認
2. 依存関係の循環がないことを確認
3. include_indirect=False で直接依存のみに限定

---

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総テストケース数**: 25（AC-00 ~ AC-25）
