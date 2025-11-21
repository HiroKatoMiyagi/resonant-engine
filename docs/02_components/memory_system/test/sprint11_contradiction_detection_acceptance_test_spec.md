# Sprint 11: Contradiction Detection Layer - 受け入れテスト仕様書

**作成日**: 2025-11-21
**作成者**: Kana (Claude Sonnet 4.5)
**対象バージョン**: Sprint 11
**総テストケース数**: 15

---

## 0. テスト哲学

### 矛盾検出の本質
```yaml
testing_philosophy:
    essence: "矛盾 = 呼吸の乱れを正確に検出できるか"
    focus:
        - 技術スタック矛盾を見逃さない
        - 方針転換を適切に検出する
        - 重複作業を防ぐ
        - 未検証前提（ドグマ）を指摘する
    principles:
        - False Positive < 10%（誤検知率）
        - False Negative < 5%（見逃し率）
        - レイテンシ < 500ms
        - ユーザー確認フロー動作
```

---

## 1. 技術スタック矛盾検出

### AC-01: 基本的な技術スタック矛盾検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- Week 1にIntent-001「PostgreSQL使用」を作成済み
- Intent-001のステータスは「active」

**When**:
- Week 5にIntent-010「SQLite使用」を提出

**Then**:
- ContradictionDetectorが矛盾を検出
- contradiction_type = "tech_stack"
- confidence_score >= 0.85
- details.old_tech = "postgresql"
- details.new_tech = "sqlite"
- conflicting_intent_id = Intent-001のID

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=intent_010_id,
    new_intent_content="Use SQLite for database"
)

assert len(contradictions) == 1
assert contradictions[0].contradiction_type == "tech_stack"
assert contradictions[0].confidence_score >= 0.85
```

---

### AC-02: カテゴリ別技術スタック検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- Past Intent: "Use FastAPI framework with PostgreSQL database"

**When**:
- New Intent: "Use Django framework with MySQL database"

**Then**:
- 2つの矛盾を検出（framework & database）
- 矛盾1: category="framework", old_tech="fastapi", new_tech="django"
- 矛盾2: category="database", old_tech="postgresql", new_tech="mysql"

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="Use Django framework with MySQL database"
)

assert len(contradictions) == 2
tech_categories = [c.details["category"] for c in contradictions]
assert "framework" in tech_categories
assert "database" in tech_categories
```

---

### AC-03: Deprecated Intentは矛盾として検出しない

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- Past Intent: "Use PostgreSQL"（status = "deprecated"）

**When**:
- New Intent: "Use SQLite"

**Then**:
- 矛盾を検出しない（deprecatedは無視される）

**検証コマンド**:
```python
# Past intentをdeprecatedに設定
await set_intent_status(past_intent_id, "deprecated")

contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="Use SQLite for database"
)

assert len(contradictions) == 0
```

---

## 2. 方針急転換検出

### AC-04: 2週間以内の方針転換を検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 10日前にIntent-005「マイクロサービス化」を作成

**When**:
- 今日Intent-008「モノリス維持」を提出

**Then**:
- ContradictionDetectorが方針転換を検出
- contradiction_type = "policy_shift"
- details.old_policy = "microservice"
- details.new_policy = "monolith"
- details.days_elapsed = 10

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=intent_008_id,
    new_intent_content="Maintain monolithic architecture"
)

assert len(contradictions) == 1
assert contradictions[0].contradiction_type == "policy_shift"
assert contradictions[0].details["days_elapsed"] == 10
```

---

### AC-05: 2週間以上経過した方針転換は検出しない

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 30日前にIntent-005「マイクロサービス化」を作成

**When**:
- 今日Intent-008「モノリス維持」を提出

**Then**:
- 方針転換を検出しない（2週間の窓を超えている）

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=intent_008_id,
    new_intent_content="Maintain monolithic architecture"
)

policy_shift_contradictions = [
    c for c in contradictions if c.contradiction_type == "policy_shift"
]
assert len(policy_shift_contradictions) == 0
```

---

### AC-06: 複数の方針キーワードペア検出

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- 5日前にIntent-020「Use async operations with NoSQL」

**When**:
- 今日Intent-025「Use sync operations with SQL database」

**Then**:
- 2つの方針転換を検出
- 転換1: async → sync
- 転換2: nosql → sql

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=intent_025_id,
    new_intent_content="Use sync operations with SQL database"
)

policy_shifts = [
    c for c in contradictions if c.contradiction_type == "policy_shift"
]
assert len(policy_shifts) == 2
```

---

## 3. 重複作業検出

### AC-07: 高類似度の重複Intent検出

**優先度**: P0（必須）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- Past Intent: "Implement user login functionality"（status = "completed"）

**When**:
- New Intent: "Implement user login feature"（類似度 > 0.85）

**Then**:
- 重複を検出
- contradiction_type = "duplicate"
- confidence_score >= 0.85
- details.similarity >= 0.85
- details.past_intent_status = "completed"

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="Implement user login feature"
)

duplicates = [c for c in contradictions if c.contradiction_type == "duplicate"]
assert len(duplicates) == 1
assert duplicates[0].confidence_score >= 0.85
```

---

### AC-08: 類似度が閾値以下の場合は検出しない

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在
- Past Intent: "Implement user login functionality"

**When**:
- New Intent: "Add OAuth authentication"（類似度 < 0.85）

**Then**:
- 重複を検出しない（類似度が閾値以下）

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="Add OAuth authentication"
)

duplicates = [c for c in contradictions if c.contradiction_type == "duplicate"]
assert len(duplicates) == 0
```

---

### AC-09: Jaccard係数による類似度計算

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- text_a = "implement user login authentication system"
- text_b = "implement user login system"

**When**:
- Jaccard係数を計算

**Then**:
- similarity = 4/5 = 0.8（共通4単語、全体5単語）

**検証コマンド**:
```python
detector = ContradictionDetector(pool)
set_a = set("implement user login authentication system".split())
set_b = set("implement user login system".split())

similarity = detector._jaccard_similarity(set_a, set_b)
assert similarity == pytest.approx(0.8, abs=0.01)
```

---

## 4. ドグマ（未検証前提）検出

### AC-10: ドグマキーワード検出

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在

**When**:
- New Intent: "All users always login before using the app"

**Then**:
- ドグマを検出
- contradiction_type = "dogma"
- details.detected_keywords = ["all users", "always"]
- confidence_score = 0.7

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="All users always login before using the app"
)

dogmas = [c for c in contradictions if c.contradiction_type == "dogma"]
assert len(dogmas) == 1
assert "all users" in dogmas[0].details["detected_keywords"]
assert "always" in dogmas[0].details["detected_keywords"]
```

---

### AC-11: 日本語ドグマキーワード検出

**優先度**: P1（重要）
**タイプ**: 単体テスト

**Given**:
- User「hiroki」が存在

**When**:
- New Intent: "ユーザーは必ずログインする"

**Then**:
- ドグマを検出
- details.detected_keywords = ["必ず"]

**検証コマンド**:
```python
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="ユーザーは必ずログインする"
)

dogmas = [c for c in contradictions if c.contradiction_type == "dogma"]
assert len(dogmas) == 1
assert "必ず" in dogmas[0].details["detected_keywords"]
```

---

## 5. 矛盾解決ワークフロー

### AC-12: 矛盾解決（方針転換）

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- 矛盾ID「contradiction-001」が検出済み
- resolution_status = "pending"

**When**:
- 矛盾を解決:
  - resolution_action = "policy_change"
  - resolution_rationale = "Switching to SQLite for development simplicity"
  - resolved_by = "hiroki"

**Then**:
- 矛盾レコードが更新される
- resolution_status = "approved"
- resolution_action = "policy_change"
- resolved_at = 現在時刻
- resolved_by = "hiroki"

**検証コマンド**:
```python
await detector.resolve_contradiction(
    contradiction_id="contradiction-001",
    resolution_action="policy_change",
    resolution_rationale="Switching to SQLite for development simplicity",
    resolved_by="hiroki"
)

# Verify database update
contradiction = await get_contradiction("contradiction-001")
assert contradiction.resolution_status == "approved"
assert contradiction.resolution_action == "policy_change"
assert contradiction.resolved_by == "hiroki"
assert contradiction.resolved_at is not None
```

---

### AC-13: 未解決矛盾一覧取得

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- User「hiroki」が存在
- 矛盾1: resolution_status = "pending"
- 矛盾2: resolution_status = "pending"
- 矛盾3: resolution_status = "approved"

**When**:
- 未解決矛盾一覧を取得

**Then**:
- 2件の矛盾が返される（矛盾1, 矛盾2）
- 矛盾3は含まれない（resolved済み）
- detected_at降順でソート

**検証コマンド**:
```python
pending = await detector.get_pending_contradictions(user_id="hiroki")

assert len(pending) == 2
assert all(c.resolution_status == "pending" for c in pending)
assert pending[0].detected_at >= pending[1].detected_at
```

---

## 6. API統合テスト

### AC-14: POST /api/v1/contradiction/check エンドポイント

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPI アプリケーション起動
- User「hiroki」が存在
- Past Intent: "Use PostgreSQL database"

**When**:
- POST /api/v1/contradiction/check
  ```json
  {
    "user_id": "hiroki",
    "intent_id": "new-intent-id",
    "intent_content": "Use SQLite database"
  }
  ```

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "contradictions": [
      {
        "contradiction_type": "tech_stack",
        "confidence_score": 0.9,
        "details": {
          "old_tech": "postgresql",
          "new_tech": "sqlite"
        }
      }
    ],
    "count": 1
  }
  ```

**検証コマンド**:
```python
response = await client.post(
    "/api/v1/contradiction/check",
    json={
        "user_id": "hiroki",
        "intent_id": str(new_intent_id),
        "intent_content": "Use SQLite database"
    }
)

assert response.status_code == 200
data = response.json()
assert data["count"] == 1
assert data["contradictions"][0]["contradiction_type"] == "tech_stack"
```

---

### AC-15: PUT /api/v1/contradiction/{id}/resolve エンドポイント

**優先度**: P0（必須）
**タイプ**: E2Eテスト

**Given**:
- FastAPI アプリケーション起動
- User「hiroki」が存在
- 矛盾ID「contradiction-001」が検出済み

**When**:
- PUT /api/v1/contradiction/contradiction-001/resolve
  ```json
  {
    "resolution_action": "policy_change",
    "resolution_rationale": "Switching to SQLite for dev environment",
    "resolved_by": "hiroki"
  }
  ```

**Then**:
- HTTP 200 OK
- Response body:
  ```json
  {
    "status": "resolved",
    "contradiction_id": "contradiction-001",
    "action": "policy_change"
  }
  ```
- データベースで矛盾が解決済みになっている

**検証コマンド**:
```python
response = await client.put(
    f"/api/v1/contradiction/{contradiction_id}/resolve",
    json={
        "resolution_action": "policy_change",
        "resolution_rationale": "Switching to SQLite for dev environment",
        "resolved_by": "hiroki"
    }
)

assert response.status_code == 200
data = response.json()
assert data["status"] == "resolved"
assert data["action"] == "policy_change"
```

---

## 7. パフォーマンステスト

### AC-16: 矛盾検出レイテンシ < 500ms

**優先度**: P1（重要）
**タイプ**: パフォーマンステスト

**Given**:
- User「hiroki」が存在
- 過去Intent 50件がデータベースに存在

**When**:
- 新規Intent矛盾チェック実行

**Then**:
- 処理時間 < 500ms

**検証コマンド**:
```python
import time

start = time.time()
contradictions = await detector.check_new_intent(
    user_id="hiroki",
    new_intent_id=new_id,
    new_intent_content="Use MongoDB database"
)
elapsed = (time.time() - start) * 1000

assert elapsed < 500  # 500ms以内
```

---

## 8. Intent Bridge統合テスト

### AC-17: Intent処理時の自動矛盾チェック

**優先度**: P0（必須）
**タイプ**: 統合テスト

**Given**:
- Intent Bridge実行中
- ContradictionDetector統合済み
- User「hiroki」が存在
- Past Intent: "Use PostgreSQL"

**When**:
- 新規Intent提出: "Use SQLite"

**Then**:
- Intent処理がpause
- IntentResult.status = "paused_for_confirmation"
- IntentResult.contradictions に矛盾リストが含まれる

**検証コマンド**:
```python
processor = IntentProcessor(
    ...,
    contradiction_detector=detector
)

result = await processor.process_intent(
    Intent(
        user_id="hiroki",
        content="Use SQLite database"
    )
)

assert result.status == "paused_for_confirmation"
assert len(result.contradictions) > 0
```

---

## 9. エラーハンドリング

### AC-18: 矛盾検出失敗時の動作

**優先度**: P1（重要）
**タイプ**: 異常系テスト

**Given**:
- Intent Bridge実行中
- ContradictionDetectorでDBエラー発生

**When**:
- 新規Intent提出

**Then**:
- Intent処理は継続される（矛盾検出の失敗でIntent処理を止めない）
- エラーがログに記録される

**検証コマンド**:
```python
# Mock DB error
with patch.object(detector, 'check_new_intent', side_effect=Exception("DB Error")):
    result = await processor.process_intent(intent)

    # Intent processing should continue
    assert result.status != "error"
    # Error should be logged
    assert "Contradiction detection failed" in captured_logs
```

---

## 10. データ整合性テスト

### AC-19: contradictionsテーブル制約

**優先度**: P1（重要）
**タイプ**: データベーステスト

**Given**:
- PostgreSQL接続

**When**:
- 無効なcontradiction_typeで挿入を試行

**Then**:
- CHECK制約違反エラー

**検証コマンド**:
```sql
-- Should fail
INSERT INTO contradictions (
    user_id, new_intent_id, new_intent_content,
    contradiction_type, confidence_score
) VALUES (
    'hiroki', gen_random_uuid(), 'Test',
    'invalid_type', 0.9
);

-- Expected: ERROR:  new row for relation "contradictions" violates check constraint
```

---

## 完了基準

### Tier 1: 必須要件（全て満たす必要あり）
- [x] AC-01 ~ AC-15: 全15テストケースがPASS
- [x] 単体テスト10件以上作成・PASS
- [x] E2Eテスト3件以上作成・PASS
- [x] API統合テスト2件以上作成・PASS

### Tier 2: 品質要件
- [ ] AC-16: パフォーマンステストPASS（< 500ms）
- [ ] False Positive Rate < 10%
- [ ] コードカバレッジ > 80%

---

## テスト実行コマンド

### 全テスト実行
```bash
pytest tests/contradiction/ -v
```

### 単体テストのみ
```bash
pytest tests/contradiction/test_detector.py -v
```

### E2Eテストのみ
```bash
pytest tests/integration/test_contradiction_detection_e2e.py -v
```

### パフォーマンステスト
```bash
pytest tests/contradiction/test_performance.py -v --benchmark
```

---

## トラブルシューティング

### False Positive（誤検知）対策

**問題**: 技術スタック矛盾が誤検知される

**対策**:
1. confidence_scoreを確認（0.9以上のみ通知）
2. キーワード辞書を精緻化
3. ユーザーフィードバックで学習

### False Negative（見逃し）対策

**問題**: 明らかな矛盾が検出されない

**対策**:
1. キーワード辞書を拡充
2. 類似度計算アルゴリズムを改善
3. AI判定の導入（Sprint 12）

---

**作成日**: 2025-11-21
**作成者**: Kana (Claude Sonnet 4.5)
**バージョン**: 1.0.0
**総テストケース数**: 19（AC-01 ~ AC-19）
