# Sprint 12: Term Drift Detection - 受け入れテスト仕様書

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**対象バージョン**: Sprint 12
**総テストケース数**: 22

---

## 0. テスト哲学

### 用語ドリフト検出の本質
```yaml
testing_philosophy:
    essence: "用語の揺らぎ = 認知的不協和を正確に検出できるか"
    focus:
        - 用語定義の変化を見逃さない
        - エイリアスの適切な解決
        - コンテキスト不一致の検出
        - 影響分析の正確性
    principles:
        - False Positive Rate < 15%（誤検知率）
        - 検出レイテンシ < 300ms
        - 影響分析レイテンシ < 500ms
        - Intent Bridge統合動作
```

---

## 1. 環境セットアップ（Docker）

### AC-00: PostgreSQLマイグレーション実行

**優先度**: P0（必須）
**タイプ**: 環境構築

**Given**:
- Dockerコンテナが起動可能
- `docker/postgres/009_term_drift_detection.sql` が存在

**When**:
- マイグレーションを実行:
  ```bash
  cd docker
  docker-compose up -d postgres
  docker exec -i resonant-postgres psql -U postgres -d resonant_engine < postgres/009_term_drift_detection.sql
  ```

**Then**:
- 5つのテーブルが作成される:
  - `term_definitions`
  - `term_aliases`
  - `term_versions`
  - `term_usages`
  - `term_drift_alerts`
- 14個のインデックスが作成される

**検証コマンド**:
```sql
-- テーブル確認
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public' AND table_name LIKE 'term_%';

-- インデックス確認
SELECT indexname FROM pg_indexes
WHERE tablename LIKE 'term_%';
```

---

## 2. TermRegistry（用語レジストリ）

### AC-01: 新規用語の登録

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- PostgreSQL接続が有効

**When**:
- 用語を登録:
  ```python
  term = await registry.register_term(
      user_id="hiroki",
      term="ユーザー",
      definition="システムに登録済みのアカウントを持つ人物",
      scope="authentication",
      aliases=["アカウント", "メンバー"],
      created_by="hiroki"
  )
  ```

**Then**:
- TermDefinitionが作成される
- term.term == "ユーザー"
- term.scope == "authentication"
- term.version == 1
- term.is_active == True
- 2つのエイリアスが登録される

**検証コマンド**:
```python
term = await registry.register_term(
    user_id="hiroki",
    term="ユーザー",
    definition="システムに登録済みのアカウントを持つ人物",
    scope="authentication",
    aliases=["アカウント", "メンバー"],
    created_by="hiroki"
)

assert term.term == "ユーザー"
assert term.scope == "authentication"
assert term.version == 1
assert term.is_active is True

# Verify aliases
async with pool.acquire() as conn:
    aliases = await conn.fetch(
        "SELECT alias FROM term_aliases WHERE term_id = $1",
        term.id
    )
assert len(aliases) == 2
```

---

### AC-02: 重複用語登録の拒否

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」(scope="authentication")が登録済み

**When**:
- 同じ用語を再度登録しようとする

**Then**:
- ValueError例外が発生
- メッセージ: "Term 'ユーザー' already exists in scope 'authentication'"

**検証コマンド**:
```python
# First registration
await registry.register_term(
    user_id="hiroki",
    term="ユーザー",
    definition="定義1",
    scope="authentication",
    created_by="hiroki"
)

# Second registration should fail
with pytest.raises(ValueError) as exc_info:
    await registry.register_term(
        user_id="hiroki",
        term="ユーザー",
        definition="定義2",
        scope="authentication",
        created_by="hiroki"
    )

assert "already exists" in str(exc_info.value)
```

---

### AC-03: 用語定義の更新とバージョン管理

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み（version=1）
- 定義: "システムに登録済みのアカウントを持つ人物"

**When**:
- 定義を更新:
  ```python
  version = await registry.update_definition(
      term_id=term.id,
      new_definition="システムを利用する全ての人物（ゲスト含む）",
      change_reason="アナリティクス機能追加のため",
      changed_by="hiroki"
  )
  ```

**Then**:
- TermVersionが作成される
- version.old_definition = "システムに登録済みのアカウントを持つ人物"
- version.new_definition = "システムを利用する全ての人物（ゲスト含む）"
- version.semantic_diff_score > 0.0（意味的変化あり）
- term_definitionsテーブルのversion = 2

**検証コマンド**:
```python
version = await registry.update_definition(
    term_id=term.id,
    new_definition="システムを利用する全ての人物（ゲスト含む）",
    change_reason="アナリティクス機能追加のため",
    changed_by="hiroki"
)

assert version.old_definition == "システムに登録済みのアカウントを持つ人物"
assert version.new_definition == "システムを利用する全ての人物（ゲスト含む）"
assert version.semantic_diff_score > 0.0

# Verify term version updated
updated_term = await registry.get_term("hiroki", "ユーザー", "authentication")
assert updated_term.version == 2
```

---

### AC-04: エイリアスによる用語検索

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- エイリアス「アカウント」「メンバー」が登録済み

**When**:
- エイリアス「アカウント」で検索

**Then**:
- 用語「ユーザー」が返される

**検証コマンド**:
```python
term = await registry.get_term(
    user_id="hiroki",
    term="アカウント"
)

assert term is not None
assert term.term == "ユーザー"
```

---

### AC-05: 意味的差分スコア計算（Jaccard距離）

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- old_definition = "システムに登録済みのアカウント"
- new_definition = "システムを利用する全ての人物"

**When**:
- 意味的差分スコアを計算

**Then**:
- semantic_diff_score: 0.6～0.8の範囲（部分的に異なる）

**検証コマンド**:
```python
diff_score = registry._calculate_semantic_diff(
    "システムに登録済みのアカウント",
    "システムを利用する全ての人物"
)

# Should indicate significant semantic change
assert 0.4 < diff_score < 0.9
```

---

## 3. TermScanner（用語スキャナー）

### AC-06: コンテンツ内の用語検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」「ログイン」が登録済み

**When**:
- コンテンツをスキャン:
  ```python
  usages = await scanner.scan_content(
      user_id="hiroki",
      content="ユーザーはログイン後にダッシュボードを表示する",
      source_type="intent"
  )
  ```

**Then**:
- 2つのTermUsageが検出される
- usages[0].term_id = 「ユーザー」のID
- usages[1].term_id = 「ログイン」のID
- 各usageにcontextが含まれる

**検証コマンド**:
```python
usages = await scanner.scan_content(
    user_id="hiroki",
    content="ユーザーはログイン後にダッシュボードを表示する",
    source_type="intent"
)

assert len(usages) == 2

# Verify context extraction
for usage in usages:
    assert usage.context is not None
    assert len(usage.context) > 0
```

---

### AC-07: エイリアスを含むスキャン

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- エイリアス「アカウント」が登録済み

**When**:
- コンテンツをスキャン:
  ```python
  usages = await scanner.scan_content(
      user_id="hiroki",
      content="アカウント作成後にメール送信",
      source_type="documentation"
  )
  ```

**Then**:
- TermUsageが検出される
- usage.term_id = 「ユーザー」のID（エイリアス経由で解決）

**検証コマンド**:
```python
usages = await scanner.scan_content(
    user_id="hiroki",
    content="アカウント作成後にメール送信",
    source_type="documentation"
)

assert len(usages) >= 1
# The term_id should point to "ユーザー" term, found via alias
assert any(u.term_id == user_term.id for u in usages)
```

---

### AC-08: コンテキスト抽出ウィンドウ

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- content = "これは長いテキストです。ユーザーはログインする必要があります。その後、操作を続けます。"
- window_size = 20

**When**:
- 「ユーザー」のコンテキストを抽出

**Then**:
- コンテキスト: "...テキストです。ユーザーはログインする必..."
- 前後20文字が含まれる

**検証コマンド**:
```python
content = "これは長いテキストです。ユーザーはログインする必要があります。その後、操作を続けます。"
context = scanner._extract_context(content, 15, 19, window_size=20)

assert "ユーザー" in context
assert context.startswith("...")
assert context.endswith("...")
```

---

## 4. DriftDetector（ドリフト検出）

### AC-09: 定義拡張ドリフトの検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- 定義: "システムに登録済みのアカウントを持つ人物"

**When**:
- コンテンツをチェック:
  ```python
  alerts = await detector.detect_drift(
      user_id="hiroki",
      content="ユーザー（ゲストを含む）の行動を追跡する",
      source_type="intent"
  )
  ```

**Then**:
- TermDriftAlertが検出される
- alert_type = "definition_drift"
- severity = "info"
- message: "用語「ユーザー」の定義が拡張されている可能性があります"

**検証コマンド**:
```python
alerts = await detector.detect_drift(
    user_id="hiroki",
    content="ユーザー（ゲストを含む）の行動を追跡する",
    source_type="intent"
)

drift_alerts = [a for a in alerts if a.alert_type == "definition_drift"]
assert len(drift_alerts) >= 1
assert "拡張" in drift_alerts[0].message
```

---

### AC-10: 定義制限ドリフトの検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- 定義: "システムを利用する全ての人物"

**When**:
- コンテンツをチェック:
  ```python
  alerts = await detector.detect_drift(
      user_id="hiroki",
      content="ユーザーは登録済みアカウントのみを指す",
      source_type="intent"
  )
  ```

**Then**:
- TermDriftAlertが検出される
- alert_type = "definition_drift"
- message: "用語「ユーザー」の定義が制限されている可能性があります"

**検証コマンド**:
```python
alerts = await detector.detect_drift(
    user_id="hiroki",
    content="ユーザーは登録済みアカウントのみを指す",
    source_type="intent"
)

drift_alerts = [a for a in alerts if a.alert_type == "definition_drift"]
assert len(drift_alerts) >= 1
assert "制限" in drift_alerts[0].message
```

---

### AC-11: コンテキスト不一致（否定）の検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「認証」が登録済み
- 定義: "本人確認を行うプロセス"

**When**:
- コンテンツをチェック:
  ```python
  alerts = await detector.detect_drift(
      user_id="hiroki",
      content="このエンドポイントは認証ではない方法でアクセスを許可する",
      source_type="code_comment"
  )
  ```

**Then**:
- TermDriftAlertが検出される
- alert_type = "context_mismatch"
- severity = "warning"
- message: "用語「認証」が否定的なコンテキストで使用されています"

**検証コマンド**:
```python
alerts = await detector.detect_drift(
    user_id="hiroki",
    content="このエンドポイントは認証ではない方法でアクセスを許可する",
    source_type="code_comment"
)

mismatch_alerts = [a for a in alerts if a.alert_type == "context_mismatch"]
assert len(mismatch_alerts) >= 1
assert "否定的" in mismatch_alerts[0].message
```

---

### AC-12: ドリフトなしコンテンツ

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- 定義: "システムに登録済みのアカウントを持つ人物"

**When**:
- 定義と一致するコンテンツをチェック:
  ```python
  alerts = await detector.detect_drift(
      user_id="hiroki",
      content="ユーザーはログイン後に設定を変更できる",
      source_type="intent"
  )
  ```

**Then**:
- ドリフトアラートなし（通常の使用）

**検証コマンド**:
```python
alerts = await detector.detect_drift(
    user_id="hiroki",
    content="ユーザーはログイン後に設定を変更できる",
    source_type="intent"
)

# No drift alerts expected for normal usage
drift_and_mismatch = [
    a for a in alerts
    if a.alert_type in ["definition_drift", "context_mismatch"]
]
assert len(drift_and_mismatch) == 0
```

---

### AC-13: アラート解決

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- ドリフトアラートが検出済み（resolution_status = "pending"）

**When**:
- アラートを解決:
  ```python
  await detector.resolve_alert(
      alert_id=alert.id,
      resolution_action="definition_updated",
      resolution_note="定義を更新して拡張範囲を含める",
      resolved_by="hiroki"
  )
  ```

**Then**:
- resolution_status = "resolved"
- resolution_action = "definition_updated"
- resolved_at が設定される
- resolved_by = "hiroki"

**検証コマンド**:
```python
await detector.resolve_alert(
    alert_id=alert.id,
    resolution_action="definition_updated",
    resolution_note="定義を更新して拡張範囲を含める",
    resolved_by="hiroki"
)

# Verify database update
async with pool.acquire() as conn:
    row = await conn.fetchrow(
        "SELECT * FROM term_drift_alerts WHERE id = $1",
        alert.id
    )

assert row["resolution_status"] == "resolved"
assert row["resolution_action"] == "definition_updated"
assert row["resolved_by"] == "hiroki"
assert row["resolved_at"] is not None
```

---

## 5. ImpactAnalyzer（影響分析）

### AC-14: 影響分析レポート生成

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- 10箇所で使用済み（intent x 5, documentation x 3, code_comment x 2）

**When**:
- 影響分析を実行:
  ```python
  report = await analyzer.analyze_impact(term_id=term.id)
  ```

**Then**:
- report.usage_count == 10
- report.affected_intents == 5
- report.affected_files に使用ファイルがリストされる
- report.recommendations が生成される

**検証コマンド**:
```python
report = await analyzer.analyze_impact(term_id=term.id)

assert report.usage_count == 10
assert report.affected_intents == 5
assert len(report.recommendations) > 0
```

---

### AC-15: 高影響度の推奨事項生成

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- 用語使用回数 > 50

**When**:
- 推奨事項を生成

**Then**:
- "この用語は広く使用されています。定義変更は慎重に行ってください。" が含まれる

**検証コマンド**:
```python
recommendations = analyzer._generate_recommendations(
    usage_count=60,
    file_count=15,
    intent_count=20
)

assert any("広く使用" in r for r in recommendations)
assert any("段階的な更新" in r for r in recommendations)
```

---

## 6. API統合テスト

### AC-16: POST /api/v1/terms 用語登録

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在

**When**:
- POST /api/v1/terms?user_id=hiroki
  ```json
  {
    "term": "エージェント",
    "definition": "AIアシスタント",
    "scope": "ai",
    "aliases": ["Agent", "アシスタント"]
  }
  ```

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "id": "uuid",
    "term": "エージェント",
    "definition": "AIアシスタント",
    "scope": "ai",
    "version": 1,
    "is_active": true
  }
  ```

**検証コマンド**:
```python
response = await client.post(
    "/api/v1/terms?user_id=hiroki",
    json={
        "term": "エージェント",
        "definition": "AIアシスタント",
        "scope": "ai",
        "aliases": ["Agent", "アシスタント"]
    }
)

assert response.status_code == 200
data = response.json()
assert data["term"] == "エージェント"
assert data["scope"] == "ai"
assert data["version"] == 1
```

---

### AC-17: POST /api/v1/terms/scan コンテンツスキャン

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在
- 用語「ユーザー」が登録済み（定義: 登録済みアカウント）

**When**:
- POST /api/v1/terms/scan?user_id=hiroki
  ```json
  {
    "content": "ユーザー（ゲスト含む）がダッシュボードを表示",
    "source_type": "intent"
  }
  ```

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "alerts": [
      {
        "alert_type": "definition_drift",
        "severity": "info",
        "message": "用語「ユーザー」の定義が拡張されている可能性があります"
      }
    ],
    "count": 1
  }
  ```

**検証コマンド**:
```python
response = await client.post(
    "/api/v1/terms/scan?user_id=hiroki",
    json={
        "content": "ユーザー（ゲスト含む）がダッシュボードを表示",
        "source_type": "intent"
    }
)

assert response.status_code == 200
data = response.json()
assert data["count"] >= 1
assert data["alerts"][0]["alert_type"] == "definition_drift"
```

---

### AC-18: GET /api/v1/terms/{term_id}/impact 影響分析

**優先度**: P1（重要）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在
- 用語「ユーザー」が登録済み

**When**:
- GET /api/v1/terms/{term_id}/impact

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "term_id": "uuid",
    "term": "ユーザー",
    "usage_count": 10,
    "affected_files": [...],
    "recommendations": [...]
  }
  ```

**検証コマンド**:
```python
response = await client.get(f"/api/v1/terms/{term.id}/impact")

assert response.status_code == 200
data = response.json()
assert data["term"] == "ユーザー"
assert "usage_count" in data
assert "recommendations" in data
```

---

### AC-19: PUT /api/v1/terms/drift-alerts/{alert_id}/resolve アラート解決

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPIアプリケーション起動
- User「hiroki」が存在
- ドリフトアラートが検出済み

**When**:
- PUT /api/v1/terms/drift-alerts/{alert_id}/resolve?user_id=hiroki
  ```json
  {
    "resolution_action": "definition_updated",
    "resolution_note": "定義を更新してゲストユーザーを含めることにした"
  }
  ```

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "status": "resolved",
    "alert_id": "uuid"
  }
  ```

**検証コマンド**:
```python
response = await client.put(
    f"/api/v1/terms/drift-alerts/{alert.id}/resolve?user_id=hiroki",
    json={
        "resolution_action": "definition_updated",
        "resolution_note": "定義を更新してゲストユーザーを含めることにした"
    }
)

assert response.status_code == 200
data = response.json()
assert data["status"] == "resolved"
```

---

## 7. Intent Bridge統合テスト

### AC-20: Intent処理時の自動ドリフト検出

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- Intent Bridge実行中
- DriftDetector統合済み
- User「hiroki」が存在
- 用語「ユーザー」が登録済み（定義: 登録済みアカウント）

**When**:
- 新規Intent提出: "ユーザー（ゲスト含む）の行動を追跡する"

**Then**:
- ドリフトアラートが生成される
- IntentResultにdrift_alertsが含まれる
- 重大なドリフト（critical）の場合はIntent処理がpause

**検証コマンド**:
```python
processor = IntentProcessor(
    ...,
    drift_detector=detector
)

result = await processor.process_intent(
    Intent(
        user_id="hiroki",
        content="ユーザー（ゲスト含む）の行動を追跡する"
    )
)

# Drift should be detected
assert hasattr(result, 'drift_alerts') or result.status != "error"
```

---

## 8. パフォーマンステスト

### AC-21: ドリフト検出レイテンシ < 300ms

**優先度**: P1（重要）
**タイプ**: パフォーマンステスト

**Given**:
- User「hiroki」が存在
- 20個の用語が登録済み

**When**:
- コンテンツスキャン実行（100文字）

**Then**:
- 処理時間 < 300ms

**検証コマンド**:
```python
import time

start = time.time()
alerts = await detector.detect_drift(
    user_id="hiroki",
    content="ユーザーがログインして認証後にダッシュボードを表示する",
    source_type="intent"
)
elapsed = (time.time() - start) * 1000

assert elapsed < 300  # 300ms以内
```

---

### AC-22: 影響分析レイテンシ < 500ms

**優先度**: P1（重要）
**タイプ**: パフォーマンステスト

**Given**:
- User「hiroki」が存在
- 用語「ユーザー」が登録済み
- 100箇所で使用済み

**When**:
- 影響分析を実行

**Then**:
- 処理時間 < 500ms

**検証コマンド**:
```python
import time

start = time.time()
report = await analyzer.analyze_impact(term_id=term.id)
elapsed = (time.time() - start) * 1000

assert elapsed < 500  # 500ms以内
```

---

## 9. データベース制約テスト

### AC-23: term_definitionsテーブル制約

**優先度**: P1（重要）
**タイプ**: データベーステスト

**Given**:
- PostgreSQL接続

**When**:
- 無効なscopeで挿入を試行（100文字超）

**Then**:
- エラー発生

**検証コマンド**:
```sql
-- Should fail: scope too long
INSERT INTO term_definitions (
    user_id, term, definition, scope, created_by
) VALUES (
    'hiroki', 'test', 'test definition',
    'a_very_long_scope_that_exceeds_one_hundred_characters_which_is_the_maximum_allowed_length_for_this_field',
    'hiroki'
);
```

---

### AC-24: term_usages CHECK制約

**優先度**: P1（重要）
**タイプ**: データベーステスト

**Given**:
- PostgreSQL接続

**When**:
- 無効なsource_typeで挿入を試行

**Then**:
- CHECK制約違反エラー

**検証コマンド**:
```sql
-- Should fail: invalid source_type
INSERT INTO term_usages (
    term_id, user_id, source_type
) VALUES (
    gen_random_uuid(), 'hiroki', 'invalid_type'
);

-- Expected: ERROR: new row for relation "term_usages" violates check constraint
```

---

## 完了基準

### Tier 1: 必須要件（全て満たす必要あり）
- [ ] AC-00: Docker環境セットアップ完了
- [ ] AC-01 ~ AC-19: 全19テストケースがPASS
- [ ] 単体テスト15件以上作成・PASS
- [ ] E2Eテスト4件以上作成・PASS

### Tier 2: 品質要件
- [ ] AC-21, AC-22: パフォーマンステストPASS
- [ ] False Positive Rate < 15%
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
# Sprint 12マイグレーション実行
docker exec -i resonant-postgres psql -U postgres -d resonant_engine < postgres/009_term_drift_detection.sql
```

### 3. マイグレーション確認

```bash
docker exec -it resonant-postgres psql -U postgres -d resonant_engine -c "\dt term_*"
```

**期待される出力**:
```
          List of relations
 Schema |       Name        | Type  |  Owner
--------+-------------------+-------+----------
 public | term_aliases      | table | postgres
 public | term_definitions  | table | postgres
 public | term_drift_alerts | table | postgres
 public | term_usages       | table | postgres
 public | term_versions     | table | postgres
(5 rows)
```

### 4. インデックス確認

```bash
docker exec -it resonant-postgres psql -U postgres -d resonant_engine -c "SELECT indexname FROM pg_indexes WHERE tablename LIKE 'term_%';"
```

---

## テスト実行コマンド

### 全テスト実行
```bash
pytest tests/term_drift/ -v
```

### 単体テストのみ
```bash
pytest tests/term_drift/test_models.py tests/term_drift/test_registry.py tests/term_drift/test_scanner.py tests/term_drift/test_detector.py -v
```

### E2Eテストのみ
```bash
pytest tests/integration/test_term_drift_e2e.py -v
```

### パフォーマンステスト
```bash
pytest tests/term_drift/test_performance.py -v --benchmark
```

---

## トラブルシューティング

### マイグレーションエラー

**問題**: `relation "term_definitions" already exists`

**対策**:
```sql
-- テーブルを削除して再作成
DROP TABLE IF EXISTS term_drift_alerts CASCADE;
DROP TABLE IF EXISTS term_usages CASCADE;
DROP TABLE IF EXISTS term_versions CASCADE;
DROP TABLE IF EXISTS term_aliases CASCADE;
DROP TABLE IF EXISTS term_definitions CASCADE;
```

### False Positive（誤検知）対策

**問題**: 通常の用語使用がドリフトとして検出される

**対策**:
1. ドリフトインジケーターの閾値を調整
2. コンテキストウィンドウサイズを拡大
3. 除外キーワードリストを追加

### パフォーマンス問題

**問題**: スキャン処理が300msを超える

**対策**:
1. インデックスが正しく作成されていることを確認
2. 用語数が多い場合はキャッシュを検討
3. クエリ最適化（EXPLAINで確認）

---

**作成日**: 2025-11-22
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総テストケース数**: 24（AC-00 ~ AC-24）
