# Bridge Lite Sprint 1.5 残作業指示書

**作成日**: 2025-11-15  
**対象**: Sprint 1.5 実装完了後の残作業  
**担当**: Tsumu (Cursor)  
**ブランチ**: `feature/sprint1.5-production-integration` (継続)  
**前提**: 作業報告書 `work_report_20251115_sprint1_5.md` を受領済み

---

## 1. 背景と目的

### 1.1 現状認識

Sprint 1.5の実装作業は完了し、以下が達成されている：
- ✅ ReEvalClient のコア化と共通クライアント昇格
- ✅ YunoFeedbackBridge / MockFeedbackBridge の ReEvalClient 統合
- ✅ BridgeFactory での自動配線
- ✅ BridgeSet FEEDBACK ステージでの呼吸循環実装
- ✅ テスト8件実装・PASS確認

### 1.2 未達成の Done Definition 項目

Sprint 1.5 仕様書のDone Definitionと照合した結果、以下が未完了：

| Done Definition項目 | 現状 | 未達成の理由 |
|-------------------|------|------------|
| OpenAPI文書更新完了 | ❌ | 報告書で「今後のフォロー事項」として先送り |
| 全テストケース 8件以上で通過 | ⚠️ | 8件PASSは確認済みだが、カバレッジ測定結果が未提示 |
| Sprint 2と矛盾しないことを確認 | ⚠️ | Sprint 2未実施のため検証不要だが、準備状況の確認が必要 |
| 日次同期チェック完遂（4日間） | ❌ | 記録なし（Sprint 2並行未実施のため不要だが、プロセスとして記録が必要） |

### 1.3 このタスクの目的

Sprint 1.5のDone Definitionを**完全達成**し、正式な完了報告書を作成できる状態にする。

---

## 2. 残作業一覧

### Task 1.5-R1: コードカバレッジ測定と検証

**優先度**: P0 (最優先)  
**所要時間**: 30分  
**目的**: テスト8件が実際にコードの80%以上をカバーしているか定量的に検証

#### 実施内容

```bash
# 1. カバレッジ測定実行
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

pytest \
  tests/bridge/test_sprint1_5_factory.py \
  tests/bridge/test_sprint1_5_yuno_feedback_bridge.py \
  tests/bridge/test_sprint1_5_bridge_set.py \
  tests/integration/test_sprint1_5_feedback_reeval_integration.py \
  --cov=bridge/core/reeval_client \
  --cov=bridge/providers/feedback/yuno_feedback_bridge \
  --cov=bridge/providers/feedback/mock_feedback_bridge \
  --cov=bridge/factory/bridge_factory \
  --cov-report=term-missing \
  --cov-report=html:coverage_report_sprint1_5

# 2. カバレッジレポート確認
open coverage_report_sprint1_5/index.html  # ブラウザで開く
```

#### 達成基準

- [ ] 全体カバレッジ ≥ 80%
- [ ] `bridge/core/reeval_client.py` カバレッジ ≥ 80%
- [ ] `bridge/providers/feedback/yuno_feedback_bridge.py` カバレッジ ≥ 80%
- [ ] `bridge/factory/bridge_factory.py` (ReEvalClient関連部分) カバレッジ ≥ 80%

#### 80%未達の場合の対応

もしカバレッジが80%未満の場合：
1. `--cov-report=term-missing` の出力で未カバー行を特定
2. 以下のいずれかを実施：
   - **Option A**: 追加テストケース作成（推奨）
   - **Option B**: 既存テストの拡充
   - **Option C**: 未カバー箇所が「テスト不要なエラーハンドリング」等である場合、その旨を文書化

#### 成果物

- [ ] `docs/test_coverage_sprint1_5.md` (カバレッジ測定結果レポート)
  - 全体カバレッジ率
  - モジュール別カバレッジ率
  - 未カバー箇所の理由説明（80%未達の場合）

---

### Task 1.5-R2: OpenAPI文書更新

**優先度**: P1 (高)  
**所要時間**: 1時間  
**目的**: Re-evaluation APIとFeedbackBridge統合に関する情報をAPI文書に反映

#### 実施内容

##### 2.1 FastAPI アプリケーションメタデータ更新

**ファイル**: `bridge/api/app.py`

```python
# 現在の description を以下に更新

app = FastAPI(
    title="Bridge Lite API",
    version="2.1.0",
    description="""
    Bridge Lite API with Re-evaluation and Feedback integration.
    
    ## Features
    
    - Intent management (CRUD operations)
    - Pipeline execution with BridgeSet
    - Re-evaluation API for Intent correction
    - Feedback loop with Yuno integration
    - Audit logging and correction history tracking
    
    ## Re-evaluation Flow
    
    1. Intent is processed through pipeline (INPUT → AI → FEEDBACK → OUTPUT)
    2. FeedbackBridge (Yuno/Mock) analyzes Intent
    3. If correction needed, Re-eval API is called automatically
    4. Intent payload is updated with diff (e.g., `feedback.yuno.*`)
    5. `correction_history` is maintained for audit trail
    6. Intent status transitions to CORRECTED
    
    ## Feedback Payload Structure
    
    When YunoFeedbackBridge applies corrections, the following fields are added to `payload.feedback.yuno`:
    
    - `reason`: High-level reason for correction (str)
    - `recommended_changes`: List of specific change recommendations (list[dict])
    - `latest`: Full evaluation result from Yuno (dict)
      - `judgment`: "approved" | "requires_changes" | "rejected"
      - `evaluation_score`: Overall score (0.0-1.0)
      - `criteria`: Detailed criteria scores (dict)
      - `suggestions`: List of improvement suggestions (list[str])
      - `issues`: List of identified issues (list[str])
    
    ## Idempotency
    
    Re-evaluation requests are idempotent based on SHA256(intent_id + diff).
    Same correction applied twice returns `already_applied: true`
    without modifying Intent or `correction_history`.
    
    ## API Endpoints
    
    - `POST /api/v1/intent/reeval`: Re-evaluate and correct an Intent
    - See full documentation in `/docs` (Swagger UI)
    """,
    docs_url="/docs",
    redoc_url="/redoc"
)
```

##### 2.2 Re-evaluation API エンドポイント文書化

**ファイル**: `bridge/api/reeval.py`

エンドポイント関数に詳細なdocstringを追加：

```python
@router.post(
    "/api/v1/intent/reeval",
    response_model=ReEvaluationResponse,
    status_code=200,
    tags=["re-evaluation"],
    summary="Re-evaluate and correct an Intent",
    description="""
    Apply differential corrections to an Intent based on feedback from Yuno or Kana.
    
    This endpoint is typically called automatically by FeedbackBridge implementations
    (YunoFeedbackBridge, MockFeedbackBridge) when corrections are needed.
    
    **Idempotency**: Same (intent_id + diff) combination will return `already_applied: true`
    on subsequent calls without modifying the Intent.
    
    **Authorization**: Only YUNO and KANA sources are permitted. TSUMU is rejected.
    
    **Diff Format**: 
    - Use absolute values only (no relative operators like "+5")
    - Nested fields use dot notation (e.g., "payload.feedback.yuno.reason")
    - See Sprint 1 specification for full diff rules
    """,
    responses={
        200: {
            "description": "Intent successfully re-evaluated",
            "content": {
                "application/json": {
                    "example": {
                        "intent_id": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "corrected",
                        "already_applied": False,
                        "correction_id": "7c9e6679-7425-40de-944b-e07fc1f90ae7",
                        "applied_at": "2025-11-15T12:34:56.789Z",
                        "correction_count": 1
                    }
                }
            }
        },
        400: {"description": "Invalid diff format or validation error"},
        403: {"description": "Source not authorized for re-evaluation"},
        404: {"description": "Intent not found"},
        409: {"description": "Intent in non-correctable status"}
    }
)
async def reeval_intent(...):
    # 既存実装
```

##### 2.3 ユーザーガイド作成

**ファイル**: `docs/api/reeval_api_guide.md` (新規作成)

詳細なユーザーガイドを作成。内容には以下を含める：
- 概要
- Quick Start (curlコマンド例)
- FeedbackBridge統合の説明
- Diff形式ルール（有効/無効な例）
- 冪等性の仕組み
- 認可ルール
- エラーハンドリング
- ベストプラクティス

#### 達成基準

- [ ] `bridge/api/app.py` の description 更新完了
- [ ] `bridge/api/reeval.py` の docstring 詳細化完了
- [ ] `docs/api/reeval_api_guide.md` 作成完了
- [ ] Swagger UI (`http://localhost:8000/docs`) で新しい文書が表示されることを確認

#### 検証方法

```bash
# 1. FastAPI アプリ起動
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
uvicorn bridge.api.app:app --reload

# 2. ブラウザで確認
open http://localhost:8000/docs

# 3. 以下を確認:
# - API description に Feedback Flow と Payload Structure が記載されている
# - POST /api/v1/intent/reeval の詳細説明が表示される
# - Response examples が適切に表示される
```

---

### Task 1.5-R3: Sprint 1.5 完了報告書作成

**優先度**: P2 (中)  
**所要時間**: 30分  
**目的**: Done Definition全項目達成を証明する最終報告書を作成

#### 実施内容

**ファイル**: `docs/reports/work_report_20251115_sprint1_5_final.md` (新規作成)

以下の内容を含める：
- 概要（Done Definition全項目達成の宣言）
- Done Definition達成状況の表
- 実装内容サマリ
- コードカバレッジ測定結果（実数値）
- ドキュメント更新内容
- 主要ファイル一覧
- 既知の問題と今後の拡張
- マージ準備状況
- 次のステップ

#### 達成基準

- [ ] 最終報告書作成完了
- [ ] Done Definition全項目の達成状況を明記
- [ ] コードカバレッジ測定結果を反映
- [ ] OpenAPI文書更新完了を反映

---

## 3. 作業スケジュール

| タスク | 所要時間 | 優先度 | 依存関係 |
|--------|---------|--------|---------|
| R1: コードカバレッジ測定 | 30分 | P0 | なし |
| R2: OpenAPI文書更新 | 1時間 | P1 | なし |
| R3: 最終完了報告書作成 | 30分 | P2 | R1, R2完了後 |
| **合計** | **2時間** | - | - |

**推奨実施順序**:
1. R1（カバレッジ測定）→ 80%未達の場合はテスト追加
2. R2（OpenAPI文書更新）
3. R3（最終報告書作成）

---

## 4. 完了基準

### 4.1 Done Definition 完全達成

以下の全項目が達成されたことを確認：

- [x] YunoFeedbackBridge.execute に再評価呼び出しロジック実装
- [x] BridgeFactory で ReEvalClient 自動生成・配線
- [x] HTTP統合テスト 3件以上追加
- [x] 全テストケース 8件以上で通過
- [ ] **OpenAPI文書更新完了** ← このタスクで達成
- [x] Sprint 2と矛盾しないことを確認（Sprint 2未実施のため非該当）
- [ ] **コードカバレッジ ≥ 80%** ← このタスクで確認
- [ ] **Kana による仕様レビュー通過** ← 最終報告書提出後

### 4.2 成果物チェックリスト

- [ ] `docs/test_coverage_sprint1_5.md` (カバレッジレポート)
- [ ] `bridge/api/app.py` (description更新)
- [ ] `bridge/api/reeval.py` (docstring詳細化)
- [ ] `docs/api/reeval_api_guide.md` (ユーザーガイド)
- [ ] `docs/reports/work_report_20251115_sprint1_5_final.md` (最終報告書)

### 4.3 検証項目

- [ ] 全テスト8件が引き続きPASS
- [ ] コードカバレッジ ≥ 80%
- [ ] Swagger UI で新しいAPI文書が表示される
- [ ] マージ可能状態（コンフリクトなし）

---

## 5. 実装ガイドライン

### 5.1 Tsumuへの指示

**CRITICAL**: この作業指示書の全タスクを順番に実施してください。

**実施時の注意事項**:
1. ブランチは `feature/sprint1.5-production-integration` を継続使用
2. カバレッジ測定結果を必ず文書化すること
3. OpenAPI文書更新後、必ず Swagger UI で確認すること
4. 最終報告書にはカバレッジ測定結果の実数値を記載すること

**禁止事項**:
- Done Definition項目の「未達成」を隠蔽すること
- カバレッジ測定を省略すること
- OpenAPI文書更新を「TODO」のままにすること

---

## 6. リスクと対策

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| カバレッジ80%未達 | Low | Medium | 追加テスト作成 or 理由文書化 |
| OpenAPI文書更新の複雑化 | Low | Low | 段階的に実施（app.py → reeval.py → guide.md） |
| 既存テストの regression | Low | High | 全テスト再実行で確認 |

---

## 7. 成功基準

### 7.1 定量的基準
- コードカバレッジ ≥ 80%
- テスト8件全PASS
- 成果物5ファイル完成

### 7.2 定性的基準
- Done Definitionの全項目が「達成」となる
- OpenAPI文書が実用的な内容になっている
- 最終報告書が「完了」を宣言できる状態

---

## 8. 関連ドキュメント

- Sprint 1.5 仕様書: `bridge_lite_sprint1_5_spec.md`
- 初回作業報告書: `work_report_20251115_sprint1_5.md`
- Sprint 1 仕様書: `bridge_lite_sprint1_spec.md`
- Re-evaluation API仕様: Sprint 1 Section 2

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓さん  
**実装担当**: Tsumu（Cursor）
