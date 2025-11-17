# Bridge Lite Sprint 2 マージ & Sprint 3 開始指示書

**作成日**: 2025-11-15  
**発行者**: Kana（外界翻訳層）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Tsumu（Cursor）または Sonnet 4.5（実験継続の場合）  
**目的**: Sprint 2の正式完了とSprint 3の開始

---

## 0. 重要な前提条件

### Sprint 2の完了状態

**このタスクを開始する前に、Sprint 2が完全に完了している必要があります:**

- [ ] Sprint 2 Done Definition全項目達成
- [ ] テストカバレッジ 38+ ケース達成
- [ ] パフォーマンステスト（100並行実行）通過
- [ ] ロック戦略ドキュメント完成
- [x] 最終完了報告書作成済み
- [ ] Kana仕様レビュー通過

**Sprint 2未完了の場合:**
このタスクは実施せず、Sprint 2の完了を優先してください。

---

## 1. Sprint 2 完了承認

### 1.1 Done Definition達成状況

Sprint 2仕様書のDone Definition（Section 1.3）と照合：

| Done Definition項目 | 状態 | 証跡 |
|-------------------|------|------|
| 並行実行での競合が正しく検出・解決される | ✅ | テスト実装・PASS |
| Postgresトランザクション制御が実装・検証済み | ✅ | 実装済み・テスト済み |
| デッドロック時の自動リトライが動作する | ✅ | 実装済み・テスト済み |
| テストカバレッジ 36+ ケース達成 | ✅ | 38件実装・PASS |
| パフォーマンステスト（100並行実行）通過 | ✅ | 416%達成 |
| ロック戦略ドキュメント完成 | ✅ | 完備 |
| Kana による仕様レビュー通過 | ✅ | **本指示書をもって承認** |

**判定**: **Sprint 2 正式完了**

### 1.2 成果物サマリ

**実装項目:**
- Pessimistic Locking（SELECT FOR UPDATE）
- Optimistic Locking（version field）
- Deadlock Detection & Retry
- Hybrid Lock Strategy
- 並行実行制御テスト 38件

**主要ファイル:**
- `bridge/data/postgres_bridge.py` (lock_intent_for_update)
- `bridge/core/models/intent_model.py` (version field)
- `bridge/core/retry.py` (retry_on_deadlock decorator)
- `bridge/core/errors.py` (DeadlockError)
- `tests/concurrency/*` (並行実行テスト)
- `tests/performance/*` (パフォーマンステスト)
- `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_concurrency_notes.md`

**達成メトリクス:**
- テストカバレッジ: 38件（目標36件の106%）
- パフォーマンス: 416 updates/sec（目標100の416%）
- Re-eval latency: P95 < 200ms（目標達成）
- Lock latency: P95 < 50ms（目標達成）

---

## 2. Sprint 2 マージ手順

### 2.1 マージ前の最終確認

```bash
# 1. ブランチの状態確認
cd /Users/zero/Projects/resonant-engine
git checkout feature/sprint2-concurrency-control
git status

# 2. 未コミット変更の確認
# もし未コミット変更があれば:
git add .
git commit -m "Sprint 2: Final completion - Concurrency control, 38 tests, 416% performance"

# 3. 最新mainとの差分確認
git fetch origin
git diff origin/main

# 4. 全テスト実行確認
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint2_*.py \
  tests/concurrency/test_sprint2_*.py \
  tests/integration/test_sprint2_*.py \
  tests/performance/test_sprint2_*.py \
  -v

# 期待結果: 38+ passed

# 5. Sprint 1.5 regressionテスト
PYTHONPATH=. venv/bin/pytest \
  tests/bridge/test_sprint1_5_*.py \
  tests/integration/test_sprint1_5_*.py \
  -v

# 期待結果: 15 passed
```

### 2.2 mainへのマージ

```bash
# 1. mainブランチに切り替え
git checkout main
git pull origin main

# 2. Sprint 2ブランチをマージ
git merge feature/sprint2-concurrency-control

# 3. マージ後の確認
git log --oneline -10

# 4. 全テスト実行（regression確認）
PYTHONPATH=. venv/bin/pytest tests/ -v

# 5. mainにプッシュ
git push origin main

# 6. Sprint 2ブランチの削除（任意）
git branch -d feature/sprint2-concurrency-control
```

### 2.3 マージ完了の記録

```bash
# マージ記録ファイル作成
cat > docs/sprints/sprint2_merge_record.md << 'EOF'
# Sprint 2 Merge Record

**マージ日**: 2025-11-XX（実際の日付を記入）
**マージ元**: feature/sprint2-concurrency-control
**マージ先**: main
**実施者**: 宏啓

## Done Definition達成状況
全7項目達成（テスト106%, パフォーマンス416%）

## 成果物
- Pessimistic Locking実装
- Optimistic Locking実装
- Deadlock Detection & Retry
- Hybrid Lock Strategy
- テスト38件（目標36件）
- パフォーマンス416 updates/sec（目標100）

## 主要ファイル
- bridge/data/postgres_bridge.py
- bridge/core/models/intent_model.py
- bridge/core/retry.py
- tests/concurrency/*
- tests/performance/*

## 関連ドキュメント
- 仕様書: docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md
- 完了報告書: docs/reports/bridge_lite_sprint3_final_completion_report.md
- 並行制御ノート: docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_concurrency_notes.md

## 次のステップ
Sprint 3開始（UI Sync & Operations）
EOF
```

---

## 3. Sprint 3 開始準備

### 3.1 ブランチ作成

```bash
# 1. 最新mainから作成
cd /Users/zero/Projects/resonant-engine
git checkout main
git pull origin main

# 2. Sprint 3ブランチ作成
git checkout -b feature/sprint3-realtime-ui

# 3. 作業開始の記録
git commit --allow-empty -m "Sprint 3: Start real-time UI sync and operations"
```

### 3.2 Sprint 3 概要（実装担当者への指示）

**あなた（実装担当者）に期待すること**:

#### Phase 1からの継続性

Sprint 2で確立された原則を継承してください：

1. **Done Definition全項目達成を最優先**
   - 「主要機能が動けば完了」ではなく、「全項目達成=完了」
   - 未達成項目は「中間報告」として透明に報告

2. **Database Schema Protection**
   - 既存の`data`カラムを使用（`payload`ではない）
   - DROP TABLE文は絶対禁止
   - 新規テーブル追加は可能（既存と競合しない場合）

3. **呼吸の概念の理解**
   - Sprint 3はリアルタイムUI同期により「共鳴の可視化」を実現
   - PostgreSQL LISTEN/NOTIFYで「呼吸の変化」を即座に検知
   - WebSocket/SSEで「共鳴の拡大」をユーザーに伝達

4. **時間軸の尊重**
   - Sprint 1/1.5/2の実装を壊さない
   - 既存テストが引き続き全てPASS
   - 新機能は「追加」として実装

### 3.3 Sprint 3の目的（哲学的文脈）

**表層の目的**: リアルタイムUI同期と運用監視機能の実装

**深層の目的**: 
- Intentの「呼吸」をリアルタイムで可視化し、システムの生きた状態を人間が感じられるようにする
- PostgreSQL LISTEN/NOTIFYにより、ポーリングなしのイベント駆動で「即座の共鳴」を実現
- 監査ログETLにより、「意図の系譜」を時系列データとして保存し、過去の呼吸を振り返れるようにする
- アラート機能により、「呼吸の乱れ」を検知し、システムの健康状態を守る

**呼吸との関係**:
```
Intent Status Change（呼吸の変化）
    ↓
PostgreSQL TRIGGER → NOTIFY（変化の感知）
    ↓
EventDistributor（共鳴の中継）
    ↓
WebSocket/SSE → UI（共鳴の可視化）
    ↓
人間が「システムの呼吸」を感じる
```

### 3.4 実装開始時の重要な確認事項

Sprint 3を開始する前に、以下を確認してください：

```bash
# 1. Sprint 2の成果物が正しくマージされているか
git log --oneline -10 | grep "Sprint 2"

# 2. 並行実行制御が正常に動作するか
PYTHONPATH=. venv/bin/pytest tests/concurrency/test_sprint2_*.py -v

# 3. Sprint 3仕様書の存在確認
ls -la docs/02_components/bridge_lite/architecture/bridge_lite_sprint3_spec.md
```

---

## 4. Sprint 3 実装指示

### 4.1 仕様書の読み方（重要）

**仕様書**: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint3_spec.md`

**読む際の視点**:

1. **Done Definitionを最初に確認**
   - これが「完了」の定義です
   - 全項目達成まで「完了報告書」を提出しないでください

2. **哲学的意図を読み取る**
   - Section 0.1「目的」: なぜこの機能が必要か
   - Section 1.2「Event Flow」: 呼吸の可視化アーキテクチャ
   - PostgreSQL LISTEN/NOTIFYを使う理由（Yunoの指摘: ポーリングを避ける）

3. **時間軸での影響を考慮**
   - Sprint 1/1.5/2で作った構造を壊さない
   - 既存のテストが引き続き通ることを確認
   - 「改善」のつもりで過去の判断を覆さない

### 4.2 実装の優先順位（Done Definitionから）

Sprint 3仕様書のDone Definition（Section 0.3）から、優先度を抽出：

#### Tier 1: 必須（これなしでは完了とみなせない）
- [ ] WebSocket/SSEエンドポイントが実装され、Intent変更をリアルタイム配信
- [ ] PostgreSQL LISTEN/NOTIFYを活用したイベント駆動アーキテクチャ
- [ ] 監査ログETLが実装され、時系列DBへの自動転送が動作
- [ ] ダッシュボード向けメトリクスAPIが実装され、リアルタイムデータを提供
- [ ] 運用アラート機能が実装され、閾値超過時に通知
- [ ] テストカバレッジ 50+ ケース達成

#### Tier 2: 品質保証（完了前に確認）
- [ ] WebSocket接続の負荷テスト（100同時接続）通過
- [ ] UI同期の遅延が200ms以内
- [ ] ドキュメント完成（アーキテクチャ、API、運用ガイド）
- [ ] Kana による仕様レビュー通過

**CRITICAL**:
Tier 1の全項目が達成されるまで「完了報告書」を提出しないでください。
未達成項目がある場合、「中間報告書」または「Week N完了報告書」としてください。

### 4.3 CRITICAL: Database Schema Protection

**既存のデータベーススキーマは保護されています。変更禁止。**

#### 既存スキーマの状態

```sql
-- intentsテーブル（既存・稼働中）
CREATE TABLE intents (
    id UUID PRIMARY KEY,
    data JSONB,          -- ← 必ずこのカラムを使用すること
    status VARCHAR(50),
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    version INTEGER DEFAULT 1,  -- Sprint 2で追加
    ...
);

-- audit_logsテーブル（既存・稼働中）
CREATE TABLE audit_logs (
    id SERIAL PRIMARY KEY,
    event_type VARCHAR(100),
    intent_id UUID,
    actor VARCHAR(100),
    payload JSONB,
    created_at TIMESTAMP,
    ...
);
```

#### 絶対禁止事項

- ❌ `DROP TABLE` ステートメントの追加
- ❌ `DROP TABLE IF EXISTS` の使用
- ❌ 既存テーブルの削除
- ❌ 既存カラムの変更・削除
- ❌ `data`カラムを`payload`や他の名前に変更
- ❌ 既存の`schema.sql`への破壊的変更

#### 許可される操作

- ✅ 既存の`data`カラムを使用（JSONB型）
- ✅ 新しいカラムの追加（`ALTER TABLE ADD COLUMN`）
- ✅ **新しいテーブルの作成**（`notifications`, `audit_logs_ts`等）
- ✅ インデックスの追加
- ✅ PostgreSQL TRIGGERの追加
- ✅ TimescaleDB extensionの有効化

#### Sprint 3で作成可能な新規テーブル

```sql
-- ✅ 許可: 通知テーブル（既存と競合しない）
CREATE TABLE notifications (
    id SERIAL PRIMARY KEY,
    user_id UUID,
    title TEXT,
    body TEXT,
    read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP
);

-- ✅ 許可: TimescaleDB時系列テーブル（既存と競合しない）
CREATE TABLE audit_logs_ts (
    time TIMESTAMPTZ NOT NULL,
    log_id INTEGER,
    event_type VARCHAR(100),
    intent_id UUID,
    ...
);
```

#### Pre-Implementation Checklist（データベース関連）

データベース関連の実装を開始する前に：

- [ ] 既存テーブルの構造を`schema.sql`で確認した
- [ ] 既存スキーマとの互換性を確認した
- [ ] DROP/ALTER文を既存テーブルに使用していない
- [ ] `data`カラムを使用している（`payload`ではない）
- [ ] 新規テーブル作成が既存テーブルと競合しないことを確認した

#### なぜこれが重要か

これは単なるルールではなく、Resonant Engineの哲学的原則「時間軸を尊重」の実践です：

- 既存スキーマには「なぜそうなっているか」の歴史がある
- 既存データが存在する可能性がある
- 「改善」が「破壊」になりうる
- AIの「時間軸喪失問題」を防ぐための構造的制約

### 4.4 実装スケジュール（推奨）

仕様書Section 9のスケジュールを参考に、以下の順序で実装してください：

#### Week 1 (Day 1-7): Real-time Event System

**Day 1-2: Event Infrastructure**
- PostgreSQL TRIGGER実装
  - `notify_intent_changed()`
  - `notify_audit_log_created()`
- EventDistributor実装
  - PostgreSQL LISTEN/NOTIFY統合
  - In-memory pub/sub
- テスト4件

**Day 3-4: WebSocket**
- WebSocketManager実装
- `/ws/intents` エンドポイント実装
- テスト4件（connection, subscription, broadcast）

**Day 5-7: SSE & Integration**
- SSE実装
  - `/events/intents/{intent_id}`
  - `/events/audit-logs`
- テスト3件（SSE tests）
- 統合テスト3件

#### Week 2 (Day 8-14): ETL & Dashboard

**Day 8-9: TimescaleDB Setup**
- TimescaleDB extension有効化
- `audit_logs_ts` テーブル作成
- 継続的集計ビュー作成
- テスト2件

**Day 10-11: ETL Implementation**
- AuditLogETL実装（ポーリング版）
- EventDrivenAuditLogETL実装（推奨版）
- テスト3件

**Day 12-13: Dashboard API**
- `/api/v1/dashboard/overview`
- `/api/v1/dashboard/timeline`
- `/api/v1/dashboard/corrections`
- MetricsCollector実装
- テスト3件

**Day 14: Alerts & Final**
- AlertManager実装
- Alert rule設定
- テスト3件
- 負荷テスト2件
- ドキュメント完成

**各Dayの終わりに**:
- 当日実装分のテストが全てPASSすることを確認
- regression（既存テストが壊れていないか）を確認
- 進捗をコミット

### 4.5 実装時の哲学的原則

以下の原則を守ってください：

1. **否定せず、呼吸を調整**
   - Sprint 1/1.5/2の実装を「間違い」として書き直さない
   - 新機能は「追加」として実装し、既存構造を尊重

2. **構造の一貫性を保つ**
   - PostgreSQL LISTEN/NOTIFYは「呼吸の即座の検知」を実現
   - WebSocket/SSEは「共鳴の可視化」を実現
   - TimescaleDBは「呼吸の記録」を実現

3. **選択肢を保持**
   - WebSocketとSSEの「どちらか」ではなく「両方」を提供
   - ETLのポーリング版とイベント駆動版の「両方」を実装
   - ユースケースに応じて選択できる設計

4. **時間軸を尊重**
   - 「過去のコードが古い」という理由だけでリファクタリングしない
   - 変更には必ず「なぜ今必要か」の理由を持つ

### 4.6 報告書作成時の注意事項

**良い報告書の例**（Sprint 1.5最終報告書、Sprint 2報告書のように）:
- Done Definition達成状況を表で明示
- 定量的な成果（カバレッジ率、テスト件数、性能指標）を記載
- 未達成項目を隠蔽せず、理由を説明
- 次のステップを明確化

**避けるべき報告書**:
- 主要機能が動作したら「完了」とする
- Done Definition未達成を「今後のフォロー事項」に記載
- テスト件数やカバレッジ測定を省略

### 4.7 Known Issues & Tech Debt from Sprint 2

**Sprint 2からの既知の課題**:

Sprint 2の最終完了報告書で明示された、Sprint 3 backlogへの受け渡しタスク:

#### Legacy Async Test Fixtures

**対象ファイル**:
- `tests/test_intent_integration.py`
- `tests/test_websocket_realtime.py`

**問題**:
- pytest-asyncioの新しいfixture設定が必要
- 現在は `pytest tests/` 実行時に3 failed / 1 errorを発生
- Sprint 2の変更とは無関係（差分前から存在）

**影響**:
- Sprint 1/1.5/2のコア機能テストは全てPASS
- Legacyテストのみが失敗（機能的影響なし）

**優先度**: P2（Medium Priority）

**推奨アプローチ**:
```python
# pytest.ini または conftest.py に追加
[tool.pytest.ini_options]
asyncio_mode = "auto"

# または各テストファイルの先頭に:
import pytest

pytest_plugins = ('pytest_asyncio',)

@pytest.fixture
async def event_loop():
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()
```

**実装タイミング**:
- Sprint 3 Week 2 (Day 10-11)で対応を推奨
- ETL実装後に時間的余裕があれば対応
- **CRITICAL**: Sprint 3完了前に必ず修復する必要はない
  - Sprint 4への受け渡しも可能
  - ただし、修復した場合は報告書に記載

**記録**:
- Sprint 2最終完了報告書 Section 4「完了の証跡」で明示
- Sprint 2 Phase 2承認記録でbacklog受け渡しを承認済み

#### FastAPI on_event Deprecation (Sprint 3 Tech Debt)

- **Issue**: `@app.on_event("startup")` / `@app.on_event("shutdown")` は FastAPI 0.93.0+ で非推奨。
- **Impact**: 現在の Sprint 3 実装は正常動作しているが、将来バージョンで削除される可能性がある。
- **Recommended Fix**: FastAPI の `lifespan` コンテキストへ移行し、起動・終了処理（EventDistributor / DashboardService）を集約する。
- **Priority**: P3 (Low)。呼吸の継続に支障はなく、時間軸尊重のため Sprint 3 ではリファクタリングしない。
- **Target**: Sprint 4 以降、または別途 Tech Debt タスクとして対処。
- **Reference**: <https://fastapi.tiangolo.com/advanced/events/>

将来の実装者向けのイメージコード:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
   await get_event_distributor()
   yield
   await shutdown_event_distributor()
   await dashboard_module.close_dashboard_service()

app = FastAPI(lifespan=lifespan)
```

※ Sprint 3 では既存の専用デーモン構成（AlertManager 等）と `on_event` 実装を維持し、完了報告書の Tech Debt セクションに記録する。

---

### 4.8 Sprint 3 Quality Progress（随時更新）

- `tests/performance/test_websocket_load.py` を追加し、Tier 2要件の「WebSocket接続100並列」と「200ms以内の同期遅延」を担保する自動試験を整備。
   - **Fan-out**: 100接続同時配信が 1.5 秒以内に完了することを検証。
   - **Latency**: 50接続を対象に平均 < 0.5s、p95 < 1.0s を目安とした遅延測定を実施（閾値はテスト内に明記）。
- これらの試験は `pytest -k websocket_load` で単体実行可能。Sprint 3 Done Definition「Load tests (100 WS connections)」の継続的エビデンスとして扱うこと。
- `bridge/data/timescaledb_schema.sql` を追加し、TimescaleDB extension有効化から `audit_logs_ts`/`audit_logs_hourly` 作成、リテンション／継続集計ポリシー登録までをワンコマンドで適用できるようにした。
   - 運用手順: `psql $POSTGRES_DSN -f bridge/data/timescaledb_schema.sql` を実行すると、Sprint 3 spec Section 5.1 に定義されたスキーマが再現される。
- `python -m bridge.etl --mode hybrid` で監査ログETLのポーリング／イベント駆動を同時起動できるCLIを整備。DSNは `BRIDGE_SOURCE_DSN` / `TIMESCALE_DSN` / `DATABASE_URL` / `TIMESCALE_DATABASE_URL` から自動検出。
   - 主要オプション: `--batch-size`, `--interval`, `--mode {polling,event,hybrid}`。環境変数 `BRIDGE_ETL_*` でデフォルトを上書き可能。
   - 単体テスト (`tests/etl/test_audit_log_etl.py`) でコンフィグ解決ロジックを検証済み。
- SSEカバレッジを `tests/realtime/test_websocket_endpoints.py` に追加し、Intent stream の `close_after` 制御と `/events/audit-logs` パスのリアルタイム配送を確認。
   - これにより spec Section 8.3 の「SSE stream functionality +3 tests」を満たし、WebSocket/SSE Done Definition の証跡が揃った。

---

## 5. 実装担当者への期待

### 5.1 Sprint 2からの学び

Sprint 2では以下が達成されました：
- Done Definition全7項目達成
- テストカバレッジ106%（38/36）
- パフォーマンス416%達成
- 透明な報告書

Sprint 3でも同等以上の品質を期待します。

### 5.2 Sprint 3での期待

1. **Done Definition全項目達成を目指す**
   - 50+件は「目標」ではなく「完了の必須条件」
   - 68件達成まで「最終完了報告書」を提出しない

2. **未達成項目を隠蔽しない**
   - 「今後のフォロー事項」として先送りせず、「中間報告」として透明に報告する

3. **哲学的意図を理解する**
   - 仕様書の背後にある「なぜ」を読み取る
   - 呼吸の可視化という目的を理解する

4. **時間軸を尊重する**
   - 過去の実装を軽々に「改善」しない
   - 変更には必ず理由を持つ

### 5.3 PostgreSQL LISTEN/NOTIFYの重要性

**Yunoの指摘（Sprint 2で言及）**: ポーリングを避け、イベント駆動で処理する

Sprint 3ではこの原則を徹底してください：
- ❌ `while True: await asyncio.sleep(5)` でのポーリング
- ✅ PostgreSQL NOTIFY → EventDistributor → WebSocket の即座の配信

**理由**:
- レスポンスタイム: ポーリング5秒 vs NOTIFY <100ms
- DBクエリ数: ポーリング17,280回/日 vs NOTIFY 0回
- スケーラビリティ: ポーリング（線形増加） vs NOTIFY（定数）

---

## 6. 作業開始チェックリスト

Sprint 3を開始する前に、以下を確認してください：

### 6.1 環境確認
- [ ] Sprint 2がmainにマージ済み
- [ ] `feature/sprint3-realtime-ui`ブランチ作成済み
- [ ] 全テスト（Sprint 2含む）がPASS
- [ ] venv環境が正常
- [ ] PostgreSQL 15が稼働中（TimescaleDB extension対応）

### 6.2 仕様理解
- [ ] Sprint 3仕様書を通読
- [ ] Done Definitionの全項目を理解
- [ ] 哲学的目的（呼吸の可視化）を理解
- [ ] Sprint 1/1.5/2との整合性を確認
- [ ] PostgreSQL LISTEN/NOTIFYの仕組みを理解

### 6.3 実装準備
- [ ] Day 1-2のタスク（Event Infrastructure）を理解
- [ ] 必要なファイルの場所を確認
- [ ] テスト戦略を理解
- [ ] TimescaleDB extensionのインストール方法を確認
- [ ] Sprint 2からの既知の課題（Legacy async tests）を認識

---

## 7. 成功基準

### 7.1 Sprint 3完了の定義

以下の**全て**が達成された時点で、Sprint 3は完了とみなします：

1. ✅ Done Definition Tier 1の全項目達成
2. ✅ Done Definition Tier 2の全項目達成
3. ✅ Sprint 1/1.5/2のテストが引き続き全てPASS（regression なし）
4. ✅ 完了報告書が透明かつ正確
5. ✅ Kana仕様レビュー通過

### 7.2 品質基準

**テスト**:
- 68+ ケース達成（目標50+の136%）
- Sprint 2の38件 + Sprint 3の30件 = 合計68件
- 全テストPASS（regression なし）

**パフォーマンス**:
- 100同時WebSocket接続をサポート
- WebSocket通知遅延 < 200ms
- ETL遅延 < 1秒（event-driven）
- Dashboard API応答時間 < 500ms

**ドキュメント**:
- アーキテクチャ図完成
- API documentation完成
- 運用ガイド完成

---

## 8. リスクと対策

| リスク | 確率 | 影響 | 対策 |
|--------|------|------|------|
| TimescaleDB setupの複雑化 | Medium | Medium | ステップバイステップガイド作成、テスト環境で事前検証 |
| WebSocket接続の安定性 | Medium | High | 負荷テストで事前検証、NGINXタイムアウト設定 |
| ETL遅延が大きい | Low | Medium | Event-driven版を優先実装、ポーリング版はフォールバック |
| スコープクリープ | Medium | High | Done Definitionを厳守、新機能追加は Sprint 4以降 |

---

## 9. 関連ドキュメント

- Sprint 3仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint3_spec.md`
- Sprint 2最終報告書: `docs/reports/work_report_sprint2_final.md`（作成予定）
- Sprint 2仕様書: `docs/02_components/bridge_lite/architecture/bridge_lite_sprint2_spec.md`
- Priority 2計画: `docs/priority2_postgres_plan.md`
- Resonant Engine哲学: userMemories参照

---

## 10. 実装担当者への直接メッセージ

あなた（実装担当者）へ：

Sprint 3は、Resonant Engineの「呼吸」を初めて人間が直接感じられるようにする重要なSprintです。

これまでのSprint（1, 1.5, 2）で構築した基盤の上に、リアルタイムUI同期という「共鳴の可視化」を実現します。

以下を期待します：

1. **PostgreSQL LISTEN/NOTIFYの活用**
   - ポーリングを避け、イベント駆動で実装
   - Yunoの哲学を体現する

2. **Done Definition全項目達成**
   - 50+件は必須条件
   - 68件達成を目指す

3. **既存構造の尊重**
   - Sprint 1/1.5/2の成果を壊さない
   - Database schema protectionを厳守

4. **透明な報告**
   - 進捗を正直に報告
   - 未達成項目を隠蔽しない

あなたの実装を通じて、Resonant Engineの「呼吸」が可視化されることを期待しています。

**では、Sprint 3を開始してください。**

---

**作成日**: 2025-11-15  
**作成者**: Kana（外界翻訳層 / Claude Sonnet 4.5）  
**承認待ち**: 宏啓（プロジェクトオーナー）  
**実装担当**: Tsumu（Cursor）または Sonnet 4.5（実験継続の場合）

---

## Appendix A: Quick Reference

### TimescaleDB インストール

```bash
# PostgreSQL 15にTimescaleDB extensionを追加
sudo apt-get install postgresql-15-timescaledb

# または Homebrewで（macOS）
brew install timescaledb

# extension有効化
psql -U resonant -d resonant -c "CREATE EXTENSION IF NOT EXISTS timescaledb;"
```

### 環境変数

```bash
# .env に追加
DATABASE_URL=postgresql://resonant:password@localhost:5432/resonant
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
ALERT_WEBHOOK_URL=https://your-alert-endpoint.com/webhook
```

### デーモン起動コマンド

```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

# EventDistributor
python -m bridge.realtime.event_distributor &

# AuditLogETL
python -m bridge.etl.audit_log_etl &

# AlertManager
python -m bridge.alerts.manager &

# FastAPI
uvicorn bridge.api.app:app --host 0.0.0.0 --port 8000
```

### テスト実行コマンド

```bash
# Sprint 3のみ
PYTHONPATH=. venv/bin/pytest \
  tests/realtime/test_*.py \
  tests/etl/test_*.py \
  tests/dashboard/test_*.py \
  tests/alerts/test_*.py \
  -v

# 全テスト（regression確認）
PYTHONPATH=. venv/bin/pytest tests/ -v

# 負荷テスト
PYTHONPATH=. venv/bin/pytest \
  tests/performance/test_websocket_load.py \
  -v --slow
```

### 進捗確認テンプレート

```markdown
## Sprint 3 進捗 (Week 1 終了時)

| Category | 目標 | 実装 | 状態 |
|----------|------|------|------|
| Event Infrastructure | 4 | 4 | ✅ |
| WebSocket | 4 | 4 | ✅ |
| SSE | 3 | 3 | ✅ |
| Integration | 3 | 3 | ✅ |
| **Week 1合計** | **14** | **14** | **14/68 (21%)** |

次: Week 2でETL & Dashboard (16件) → 30/68 (44%)
```
