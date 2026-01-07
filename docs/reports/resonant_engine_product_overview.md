# Resonant Engine

**Time-Aware AI Development Environment**

製品仕様書 | 2026年1月

---

## 1. プロダクト概要

**Resonant Engine**は、AIと人間の協調開発における「時間軸の喪失」問題を解決する開発環境です。従来のAI開発ツールが「今この瞬間」のコード生成に特化するのに対し、Resonant Engineはプロジェクトの歴史、意思決定の理由、用語の変遷を追跡し、一貫性のある開発を支援します。

### 1.1 解決する課題

1. **時間軸喪失問題**：AIが過去の検証済みコードを無視して破壊的変更を提案
2. **意思決定の忘却**：「なぜこの技術を選んだか」の理由が失われる
3. **用語の意味変化**：プロジェクト進行中に用語の定義がズレる
4. **矛盾する意思決定**：過去の決定と矛盾する新しい決定に気づかない

---

## 2. 全機能一覧

### 2.1 コアAPI（CRUD操作）

| リソース | エンドポイント | 機能 |
|---------|--------------|------|
| Messages | `/api/messages` | 会話履歴の保存・取得・更新・削除 |
| Intents | `/api/intents` | 開発意図の登録・ステータス管理・履歴追跡 |
| Specifications | `/api/specifications` | 仕様書のCRUD・タグ検索・バージョン管理 |
| Notifications | `/api/notifications` | システム通知・既読管理・フィルタリング |

### 2.2 矛盾検出システム（Contradiction Detection）

新しいIntentが過去の決定と矛盾していないかを自動検出。4種類の矛盾タイプを識別。

| 矛盾タイプ | 説明 |
|-----------|------|
| **TECH_STACK** | 技術スタックの矛盾（例: PostgreSQL → SQLiteへの変更） |
| **POLICY_SHIFT** | 2週間以内の方針転換（例: マイクロサービス → モノリス） |
| **DUPLICATE** | 重複作業（Jaccard類似度 ≥ 0.85） |
| **DOGMA** | 未検証の仮定（「常に」「絶対」などの断定表現） |

**API**: `POST /api/v1/contradiction/check`, `GET /pending`, `PUT /{id}/resolve`

### 2.3 選択保存システム（Choice Preservation）

意思決定時に「なぜその選択をしたか」「却下した選択肢とその理由」を記録。3ヶ月後でも判断理由を追跡可能。

- **選択肢の構造化保存**：question + choices[] + tags + context_type
- **決定理由の記録**：selected_choice_id + decision_rationale + rejection_reasons
- **履歴検索**：タグ・日付範囲・テキストによる過去の決定検索

**API**: `POST /api/v1/memory/choice-points/`, `PUT /{id}/decide`, `GET /search`

### 2.4 用語ドリフト検出（Term Drift Detection）

プロジェクト内の用語定義が時間とともに変化したことを自動検出。「Intent」の意味が拡張されたら警告。

| ドリフトタイプ | 説明 |
|--------------|------|
| **EXPANSION** | 用語の意味が拡張された |
| **CONTRACTION** | 用語の意味が縮小された |
| **SEMANTIC_SHIFT** | 用語の意味が根本的に変化した |
| **CONTEXT_CHANGE** | 用語の使用文脈が変化した |

**API**: `POST /api/v1/term-drift/analyze`, `GET /pending`, `PUT /{id}/resolve`

### 2.5 時間軸制約レイヤー（Temporal Constraint Layer）

検証済みコードへの無秩序な変更を防止。ファイルごとに制約レベルを設定し、変更時に警告・ブロック。

| レベル | 要件 | 動作 |
|-------|------|------|
| **CRITICAL** | 手動承認必須 | 変更を完全ブロック。管理者承認が必要 |
| **HIGH** | 理由50文字以上 | 詳細な変更理由の記録を強制 |
| **MEDIUM** | 理由20文字以上 | 簡潔な変更理由の記録を要求 |
| **LOW** | 制限なし | 自由に変更可能（デフォルト） |

**API**: `POST /api/v1/temporal-constraint/check`, `/verify`, `/mark-stable`, `/upgrade-critical`

### 2.6 統一ファイル操作サービス（FileModificationService）

Temporal Constraintと連携したセキュアなファイル操作。自動バックアップ・操作ログ・パス検証を統合。

- **操作**：write / delete / rename / read
- **セキュリティ**：許可パスリスト、禁止パターン（.env, credentials等）
- **自動バックアップ**：変更前のファイルを自動保存（SHA-256ハッシュ付き）
- **操作ログ**：全操作を記録（誰が・いつ・なぜ・結果）

**API**: `POST /api/v1/files/write`, `/delete`, `/rename`, `GET /read`, `/logs`

### 2.7 メモリシステム

#### Memory Store Service

- **Working Memory**：短期記憶（TTL 24時間、自動アーカイブ）
- **Long-term Memory**：永続記憶（ベクトル検索対応）
- **ベクトル類似度検索**：pgvector (1536次元) による意味検索
- **ハイブリッド検索**：ベクトル + メタデータフィルタ

#### Memory Lifecycle Management

- **容量管理**：ユーザー別使用状況監視
- **自動圧縮**：古いメモリの要約・圧縮
- **期限切れクリーンアップ**：TTL超過メモリの自動アーカイブ

**API**: `GET /api/v1/memory/lifecycle/status`, `POST /compress`, `DELETE /expired`

### 2.8 検索オーケストレーター（Retrieval Orchestrator）

クエリ分析 → 戦略選択 → 複数検索実行 → リランキングの統合パイプライン。

- **Query Analyzer**：クエリの意図を分析
- **Strategy Selector**：最適な検索戦略を自動選択
- **Multi-Search Executor**：SEMANTIC / TEMPORAL / KEYWORD / HYBRID 検索
- **Reranker**：検索結果の最適順序付け
- **Metrics Collector**：検索パフォーマンスの計測・統計

### 2.9 コンテキストアセンブラー（Context Assembler）

AI APIに渡す最適なコンテキストを自動構築。トークン上限を考慮した圧縮機能付き。

- **メモリ階層の統合**：Working Memory + Semantic Memory + Session Summary + Past Choices
- **User Profile統合**：ユーザープロファイルをシステムプロンプトに注入
- **トークン推定・圧縮**：上限超過時に段階的圧縮（Summary → Choices → Semantic → Working）
- **並行取得**：asyncio.gather による高速データ収集

### 2.10 ダッシュボード & アナリティクス

- **System Overview**：ユーザー数・セッション数・Intent完了率・未解決矛盾数
- **Timeline**：イベントタイムライン（分/時/日 粒度）
- **Corrections History**：修正履歴（変更前後・理由・実行者）

**API**: `GET /api/v1/dashboard/overview`, `/timeline`, `/corrections`

### 2.11 再評価システム（Re-evaluation）

Intentの再評価リクエストを処理。Yunoレイヤーによる哲学的・構造的チェック。

**API**: `POST /api/v1/intent/reeval`

### 2.12 リアルタイム通信（WebSocket）

- **Intent Updates**：`ws://host/ws/intents`
- **Subscribe/Unsubscribe**：特定IntentIDの購読管理
- **Ping/Pong**：接続維持・ヘルスチェック

---

## 3. アーキテクチャ

### 3.1 三層AI構造

| レイヤー | エージェント | 役割 |
|---------|------------|------|
| **Yuno** | GPT-5 | 思想中枢：哲学・構造・規範形成、呼吸リズムの管理、再評価判断 |
| **Kana** | Claude Sonnet 4.5 | 翻訳層：思想→仕様→コード翻訳、設計監査、矛盾検出、API統合 |
| **Tsumu** | Cursor | 実装層：コード生成・ファイル管理・テスト実行 |

### 3.2 技術スタック

| カテゴリ | 技術 |
|---------|------|
| 言語 | Python 3.11+, TypeScript, SQL |
| バックエンド | FastAPI 0.111.0+, Pydantic v2, asyncpg 0.30.0+ |
| フロントエンド | React 18 + TypeScript + Tailwind CSS |
| データベース | PostgreSQL 15 + pgvector（ベクトル検索） |
| インフラ | Docker Compose, Oracle Cloud Free Tier（$0運用） |
| AI統合 | Anthropic Claude API, OpenAI GPT-5 API |
| テスト | pytest 8.0.0+, pytest-asyncio, 286+テストケース |

---

## 4. 今後の予定

### 4.1 Sprint 13：フロントエンドUI統合（進行中）

バックエンドAPIのフロントエンド統合を35% → 85%に引き上げ

1. Contradiction Resolve UI - 矛盾解決モーダル
2. Dashboard Analytics Page - システム概要ダッシュボード
3. Choice Points Page - 選択肢管理UI
4. Memory Lifecycle Page - メモリ状況監視UI
5. Term Drift Detection UI - 用語ドリフト管理UI
6. Temporal Constraint UI - 時間軸制約管理UI
7. File Modification UI - ファイル操作UI

### 4.2 Sprint 15：WebSocket統合（仕様策定済）

- リアルタイムIntent更新通知
- 矛盾検出アラートのプッシュ配信
- 複数クライアント間の同期

### 4.3 中期目標（3-6ヶ月）

1. Oracle Cloud Free Tierへの本番デプロイ（$0運用コスト達成）
2. マルチユーザー対応・認証認可
3. VS Code / Cursor 拡張機能の開発
4. CLI ツール（resonant コマンド）の開発
5. ベータ版公開・ユーザーフィードバック収集

---

## 5. 市場価値

### 5.1 ターゲット市場

| セグメント | 課題 → 価値提案 |
|-----------|----------------|
| 個人開発者 | AI生成コードの品質管理困難 → 時間軸制約による保護 |
| 小規模チーム | 意思決定の属人化 → Choice Preservationによる知識共有 |
| 中規模企業 | 用語・方針のズレ → Term Drift / Contradiction検出 |
| AI活用チーム | AIの「今だけ」思考 → 時間軸を考慮したAI統合 |

### 5.2 競合優位性

| 機能 | Kiro CLI | Cursor/Copilot | Resonant |
|------|----------|----------------|----------|
| 時間軸制約 | ❌ | ❌ | ✅ |
| 矛盾検出 | ❌ | ❌ | ✅ |
| 選択理由保存 | ❌ | ❌ | ✅ |
| 用語ドリフト | ❌ | ❌ | ✅ |
| コード生成 | ✅ | ✅ | △（統合） |

### 5.3 価格戦略（想定）

| プラン | 価格 | 機能 |
|-------|------|------|
| **Free** | ¥0 | 基本CRUD、メモリ上限100MB、1プロジェクト |
| **Pro** | ¥2,980/月 | 全機能、メモリ上限1GB、無制限プロジェクト、優先サポート |
| **Team** | ¥9,800/月 | Pro + チーム共有、監査ログ、SSO |

---

## 6. ストロングポイント

### 6.1 唯一無二の機能

1. **時間軸を考慮したAI統合**：検証済みコードをAIから保護する唯一のシステム
2. **矛盾検出の自動化**：過去の決定との整合性を自動チェック
3. **意思決定の追跡可能性**：「なぜこうしたか」を永続的に記録
4. **用語の進化追跡**：プロジェクト固有の用語変化を検出

### 6.2 技術的強み

- **完全非同期アーキテクチャ**：asyncio + asyncpg による高スループット
- **ベクトル検索統合**：pgvector による意味的記憶検索
- **$0運用可能**：Oracle Cloud Free Tier対応設計
- **拡張性**：三層AI構造により各レイヤーを独立して進化可能

### 6.3 ビジネス上の強み

- **ブルーオーシャン**：時間軸を扱う開発ツールは競合なし
- **AI時代の必然性**：AI活用が増えるほど時間軸問題は深刻化
- **B2B拡張性**：企業のナレッジマネジメントにも応用可能
- **研究価値**：学術論文発表による権威性構築が可能

---

## APIエンドポイント一覧

### Core

```
GET/POST/PUT/DELETE /api/messages
GET/POST/PUT/DELETE /api/intents
PATCH /api/intents/{id}/status
GET/POST/PUT/DELETE /api/specifications
GET/POST/DELETE /api/notifications
POST /api/notifications/mark-read
```

### Contradiction Detection

```
GET  /api/v1/contradiction/pending
POST /api/v1/contradiction/check
PUT  /api/v1/contradiction/{id}/resolve
```

### Choice Preservation

```
GET  /api/v1/memory/choice-points/pending
POST /api/v1/memory/choice-points/
PUT  /api/v1/memory/choice-points/{id}/decide
GET  /api/v1/memory/choice-points/search
```

### Term Drift Detection

```
GET  /api/v1/term-drift/pending
POST /api/v1/term-drift/analyze
PUT  /api/v1/term-drift/{id}/resolve
```

### Temporal Constraint

```
POST /api/v1/temporal-constraint/check
POST /api/v1/temporal-constraint/verify
POST /api/v1/temporal-constraint/mark-stable
POST /api/v1/temporal-constraint/upgrade-critical
```

### File Modification

```
POST /api/v1/files/write
POST /api/v1/files/delete
POST /api/v1/files/rename
GET  /api/v1/files/read
POST /api/v1/files/check
GET  /api/v1/files/logs
POST /api/v1/files/register-verification
```

### Memory Lifecycle

```
GET    /api/v1/memory/lifecycle/status
POST   /api/v1/memory/lifecycle/compress
DELETE /api/v1/memory/lifecycle/expired
```

### Dashboard

```
GET /api/v1/dashboard/overview
GET /api/v1/dashboard/timeline
GET /api/v1/dashboard/corrections
```

### Re-evaluation

```
POST /api/v1/intent/reeval
```

### WebSocket

```
WS /ws/intents
```

---

**Resonant Engine** — Time-Aware AI Development Environment
