# Memory Management API 仕様書

**バージョン**: 1.0.0
**作成日**: 2025-11-17
**作成者**: Sonnet 4.5 (Claude Code Implementation)

## 概要

Memory Management API は、Resonant Engine の呼吸履歴と共鳴パターンを管理するための RESTful エンドポイントを提供します。セッション管理、Intent 追跡、共鳴記録、時間的スナップショットのための 15 以上のエンドポイントをサポートします。

## ベース URL

```
/api/memory
```

## 認証

現在はシングルユーザーモードをサポート。マルチユーザー認証はフェーズ4で計画中。

---

## エンドポイント

### ヘルスチェック

#### GET /health

サービスの健全性ステータスを確認。

**レスポンス:**
```json
{
  "status": "healthy",
  "version": "1.0.0",
  "service": "memory_management"
}
```

---

### セッション管理

#### POST /sessions

新しいセッション（呼吸ユニット）を作成。

**リクエスト:**
```json
{
  "user_id": "hiroaki",
  "metadata": {
    "client": "web",
    "version": "1.0.0"
  }
}
```

**レスポンス:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:00:00Z",
  "status": "active"
}
```

#### GET /sessions/{session_id}

セッション詳細とサマリーを取得。

**レスポンス:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:30:00Z",
  "status": "active",
  "summary": {
    "total_intents": 5,
    "completed_intents": 3,
    "resonance_events": 12,
    "choice_points": 2,
    "breathing_cycles": 3,
    "avg_intensity": 0.78
  }
}
```

#### PUT /sessions/{session_id}/heartbeat

セッションのハートビートタイムスタンプを更新。

**レスポンス:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "user_id": "hiroaki",
  "started_at": "2025-11-17T10:00:00Z",
  "last_active": "2025-11-17T10:35:00Z",
  "status": "active"
}
```

#### POST /sessions/{session_id}/continue

前回のセッションを継続（セッション継続性保証）。

**レスポンス:**
```json
{
  "session": {
    "session_id": "...",
    "user_id": "hiroaki",
    "status": "active"
  },
  "agent_contexts": {
    "kana": {"focus": "memory design"},
    "yuno": {"philosophy": "breathing preservation"}
  },
  "pending_choices": [...],
  "last_intent": {...},
  "current_breathing_phase": {...}
}
```

---

### Intent 管理（呼吸フェーズ1: 吸う）

#### POST /intents

新しい Intent を記録。

**リクエスト:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_intent_id": null,
  "intent_text": "メモリ管理システムの設計",
  "intent_type": "feature_request",
  "priority": 8,
  "metadata": {}
}
```

**Intent タイプ:**
- `feature_request` - 機能リクエスト
- `bug_fix` - バグ修正
- `exploration` - 探索
- `clarification` - 明確化
- `optimization` - 最適化
- `refactoring` - リファクタリング
- `documentation` - ドキュメント化
- `testing` - テスト

**レスポンス:**
```json
{
  "intent_id": "660e8400-e29b-41d4-a716-446655440001",
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "parent_intent_id": null,
  "intent_text": "メモリ管理システムの設計",
  "intent_type": "feature_request",
  "priority": 8,
  "created_at": "2025-11-17T10:32:00Z",
  "updated_at": "2025-11-17T10:32:00Z",
  "completed_at": null,
  "status": "pending",
  "outcome": null
}
```

#### GET /intents

セッションの Intent 一覧を取得。

**クエリパラメータ:**
- `session_id` (必須): UUID
- `status` (任意): pending, in_progress, completed, cancelled, deferred

**レスポンス:**
```json
{
  "intents": [...],
  "total": 5
}
```

#### PUT /intents/{intent_id}/complete

Intent を結果と共に完了させる。

**リクエスト:**
```json
{
  "outcome": {
    "implementation": "スキーマとAPI実装完了",
    "learnings": ["JSONB の柔軟性", "リポジトリパターン"],
    "next_steps": ["テスト", "ドキュメント"]
  }
}
```

**レスポンス:**
```json
{
  "intent_id": "...",
  "status": "completed",
  "completed_at": "2025-11-17T11:00:00Z",
  "outcome": {...}
}
```

---

### 共鳴管理（呼吸フェーズ2）

#### POST /resonances

共鳴状態を記録。

**リクエスト:**
```json
{
  "session_id": "550e8400-e29b-41d4-a716-446655440000",
  "intent_id": null,
  "state": "aligned",
  "intensity": 0.85,
  "agents": ["yuno", "kana"],
  "pattern_type": "philosophical_alignment",
  "duration_ms": 1500,
  "metadata": {}
}
```

**共鳴状態:**
- `aligned` - 整合
- `conflicted` - 対立
- `converging` - 収束中
- `exploring` - 探索中
- `diverging` - 発散中

**レスポンス:**
```json
{
  "resonance_id": "770e8400-e29b-41d4-a716-446655440002",
  "session_id": "...",
  "intent_id": null,
  "state": "aligned",
  "intensity": 0.85,
  "agents": ["yuno", "kana"],
  "timestamp": "2025-11-17T10:35:00Z",
  "duration_ms": 1500,
  "pattern_type": "philosophical_alignment"
}
```

#### GET /resonances

セッションの共鳴一覧を取得。

**クエリパラメータ:**
- `session_id` (必須): UUID
- `state` (任意): ResonanceState

**レスポンス:**
```json
{
  "resonances": [...],
  "total": 12,
  "avg_intensity": 0.78
}
```

---

### エージェントコンテキスト管理（呼吸フェーズ4: 再内省）

#### POST /contexts

エージェントコンテキストを保存（新しいバージョンを作成）。

**リクエスト:**
```json
{
  "session_id": "...",
  "intent_id": null,
  "agent_type": "kana",
  "context_data": {
    "current_focus": "メモリスキーマ設計",
    "recent_decisions": ["PostgreSQL使用", "柔軟性のためJSONB"],
    "pending_questions": ["バージョニング戦略は？"]
  },
  "metadata": {}
}
```

**エージェントタイプ:**
- `yuno` - 哲学的思考中枢
- `kana` - 外界翻訳層
- `tsumu` - 実装具現層

**レスポンス:**
```json
{
  "context_id": "...",
  "session_id": "...",
  "intent_id": null,
  "agent_type": "kana",
  "version": 3,
  "context_data": {...},
  "created_at": "2025-11-17T10:40:00Z"
}
```

#### GET /contexts/latest

エージェントの最新コンテキストを取得。

**クエリパラメータ:**
- `session_id` (必須): UUID
- `agent_type` (必須): yuno, kana, tsumu

#### GET /contexts/all

セッションの全エージェントコンテキストを取得。

**クエリパラメータ:**
- `session_id` (必須): UUID

**レスポンス:**
```json
{
  "contexts": {
    "yuno": {...},
    "kana": {...},
    "tsumu": {...}
  }
}
```

---

### 選択ポイント管理（呼吸フェーズ3: 構造化）

#### POST /choice-points

選択ポイントを作成。

**リクエスト:**
```json
{
  "session_id": "...",
  "intent_id": "...",
  "question": "初期実装にPostgreSQLかSQLiteか？",
  "choices": [
    {
      "id": "choice_pg",
      "description": "PostgreSQL: フル機能、本番対応",
      "implications": {
        "pros": ["JSONBサポート", "並行アクセス", "スケーラビリティ"],
        "cons": ["セットアップ複雑", "リソース使用"]
      }
    },
    {
      "id": "choice_sqlite",
      "description": "SQLite: シンプル、軽量",
      "implications": {
        "pros": ["ゼロ設定", "低リソース"],
        "cons": ["限定的並行性", "JSONB なし"]
      }
    }
  ],
  "metadata": {}
}
```

**レスポンス:**
```json
{
  "choice_point_id": "...",
  "session_id": "...",
  "intent_id": "...",
  "question": "...",
  "choices": [...],
  "selected_choice_id": null,
  "created_at": "2025-11-17T10:45:00Z",
  "decided_at": null,
  "decision_rationale": null,
  "status": "pending"
}
```

#### PUT /choice-points/{choice_point_id}/decide

決定を記録。

**リクエスト:**
```json
{
  "selected_choice_id": "choice_pg",
  "decision_rationale": "Yuno評価A+。JSONB、並行性、将来性を考慮。"
}
```

**レスポンス:**
```json
{
  "choice_point_id": "...",
  "selected_choice_id": "choice_pg",
  "decided_at": "2025-11-17T10:50:00Z",
  "decision_rationale": "..."
}
```

#### GET /choice-points/pending

未決定の選択ポイントを取得。

**クエリパラメータ:**
- `session_id` (必須): UUID

---

### 呼吸サイクル管理

#### POST /breathing-cycles

呼吸フェーズを開始。

**リクエスト:**
```json
{
  "session_id": "...",
  "intent_id": null,
  "phase": "structuring",
  "phase_data": {
    "structures_created": ["データベーススキーマ", "API設計"],
    "tools_used": ["PostgreSQL", "FastAPI"]
  }
}
```

**呼吸フェーズ:**
1. `intake` - 吸う
2. `resonance` - 共鳴
3. `structuring` - 構造化
4. `re_reflection` - 再内省
5. `implementation` - 実装
6. `resonance_expansion` - 共鳴拡大

**レスポンス:**
```json
{
  "cycle_id": "...",
  "session_id": "...",
  "intent_id": null,
  "phase": "structuring",
  "started_at": "2025-11-17T11:00:00Z",
  "completed_at": null,
  "phase_data": {...},
  "success": null
}
```

#### PUT /breathing-cycles/{cycle_id}/complete

呼吸フェーズを完了。

**リクエスト:**
```json
{
  "success": true,
  "phase_data": {
    "duration_minutes": 30,
    "outcome": "スキーマ設計完了"
  }
}
```

#### GET /breathing-cycles

セッションの呼吸サイクル一覧を取得。

**クエリパラメータ:**
- `session_id` (必須): UUID

---

### スナップショット管理（時間軸保存）

#### POST /snapshots

時間的スナップショットを作成。

**リクエスト:**
```json
{
  "session_id": "...",
  "snapshot_type": "milestone",
  "description": "メモリスキーマ設計完了",
  "tags": ["schema_design", "milestone", "sprint4"]
}
```

**スナップショットタイプ:**
- `manual` - 手動
- `auto_hourly` - 自動（1時間ごと）
- `pre_major_change` - 大規模変更前
- `crisis_point` - 危機時点
- `milestone` - マイルストーン

**レスポンス:**
```json
{
  "snapshot_id": "...",
  "session_id": "...",
  "snapshot_type": "milestone",
  "created_at": "2025-11-17T11:30:00Z",
  "description": "メモリスキーマ設計完了",
  "tags": ["schema_design", "milestone", "sprint4"]
}
```

#### GET /snapshots

セッションのスナップショット一覧を取得。

**クエリパラメータ:**
- `session_id` (必須): UUID
- `tags` (任意): フィルタリング用タグリスト

#### GET /snapshots/{snapshot_id}

完全なスナップショットデータを取得。

**レスポンス:**
```json
{
  "snapshot_id": "...",
  "snapshot_type": "milestone",
  "created_at": "...",
  "description": "...",
  "tags": [...],
  "snapshot_data": {
    "session": {...},
    "intents": [...],
    "resonances": [...],
    "agent_contexts": [...],
    "choice_points": [...],
    "breathing_cycles": [...]
  }
}
```

---

### クエリAPI

#### POST /query

カスタムメモリクエリ。

**リクエスト:**
```json
{
  "session_id": "...",
  "query": {
    "type": "intents",
    "status": "completed"
  }
}
```

**クエリタイプ:**
- `intents`
- `resonances`
- `choice_points`

**レスポンス:**
```json
{
  "query_id": "...",
  "results": [...],
  "count": 10,
  "execution_time_ms": 45
}
```

---

## エラーコード

| コード | 説明 |
|--------|------|
| 400  | Bad Request - 無効な入力 |
| 404  | Not Found - リソースが見つからない |
| 422  | Validation Error - バリデーションエラー |
| 500  | Internal Server Error - 内部サーバーエラー |

## エラーレスポンス形式

```json
{
  "detail": "エラーメッセージの説明"
}
```

---

## レート制限

v1.0.0 では未実装。将来のバージョンで計画中。

---

## バージョニング

現在のバージョン: 1.0.0

将来のリリースでは URL パス経由で API バージョニングを実装予定。
