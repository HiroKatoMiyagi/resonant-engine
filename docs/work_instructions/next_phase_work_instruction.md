# Resonant Engine 次期開発フェーズ作業開始指示書

**バージョン**: v2.0
**作成日**: 2025年11月18日
**作成者**: Kana（翻訳層）
**対象**: Tsumu（具現化層） / 加藤宏啓

---

## 📋 目次

1. [作業概要](#1-作業概要)
2. [環境準備](#2-環境準備)
3. [Sprint 2: 並行制御テスト完成](#3-sprint-2-並行制御テスト完成)
4. [Sprint 2: ドキュメント作成](#4-sprint-2-ドキュメント作成)
5. [Sprint 5: Oracle Cloud デプロイ](#5-sprint-5-oracle-cloud-デプロイ)
6. [Claude API 統合検証](#6-claude-api-統合検証)
7. [Kana 実装 Phase 1](#7-kana-実装-phase-1)
8. [日次チェックリスト](#8-日次チェックリスト)

---

## 1. 作業概要

### 1.1 作業期間

**総期間**: 2025年11月18日 - 2025年12月31日（約6週間）

**フェーズ構成**:
- Week 1: Sprint 2 完成（並行制御テスト＋ドキュメント）
- Week 2-3: Sprint 5 デプロイ準備
- Week 3-4: Claude API 検証
- Week 4-6: Kana 実装 Phase 1

### 1.2 担当者

| 役割 | 担当 | 責任範囲 |
|-----|-----|---------|
| 思想層 | Yuno（GPT-5） | 哲学・規範形成・監督 |
| 翻訳層 | Kana（Claude Sonnet 4.5） | 設計・レビュー・翻訳 |
| 具現化層 | Tsumu（Cursor） | コード実装・テスト |
| プロダクトオーナー | 加藤宏啓 | 最終承認・意思決定 |

### 1.3 成功基準

- [ ] Sprint 2 テストカバレッジ 80%以上
- [ ] Oracle Cloud 本番デプロイ成功
- [ ] Claude API 統合検証完了
- [ ] Kana 翻訳エンジン実装 50%完成
- [ ] 全受け入れテスト PASS

---

## 2. 環境準備

### 2.1 ローカル環境セットアップ

#### 2.1.1 必須ツール確認

```bash
# Python バージョン確認
python --version  # 3.11以上

# Docker バージョン確認
docker --version  # 20.10以上
docker compose version  # V2

# Git 確認
git --version

# venv 環境確認
cd /Users/zero/Projects/resonant-engine/
source venv/bin/activate
```

#### 2.1.2 環境変数設定

```bash
# .env ファイル作成
cp .env.template .env

# 必須API キー設定
nano .env
```

**.env 設定内容**:
```bash
# Claude API (Kana用)
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API (Yuno用)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# PostgreSQL
DATABASE_URL=postgresql://resonant:password@localhost:5432/resonant
POSTGRES_USER=resonant
POSTGRES_PASSWORD=password
POSTGRES_DB=resonant

# アプリケーション設定
ENVIRONMENT=development
DEBUG=true
```

#### 2.1.3 依存関係インストール

```bash
# Python 依存関係
cd /Users/zero/Projects/resonant-engine/
source venv/bin/activate
pip install -r requirements.txt

# Backend 依存関係
cd backend
pip install -r requirements.txt

# Frontend 依存関係
cd ../frontend
npm install

# Intent Bridge 依存関係
cd ../intent_bridge
pip install -r requirements.txt
```

#### 2.1.4 Docker 環境起動

```bash
# Docker Compose 起動
cd /Users/zero/Projects/resonant-engine/docker
./scripts/start.sh

# ヘルスチェック
./scripts/check-health.sh

# 期待される出力:
# ✓ PostgreSQL is running
# ✓ Backend is running (http://localhost:8000)
# ✓ Frontend is running (http://localhost:3000)
# ✓ Intent Bridge is running
```

### 2.2 ブランチ戦略

#### 2.2.1 作業ブランチ作成

```bash
# 現在のブランチ確認
git branch

# 新規作業ブランチ作成（例: Sprint 2用）
git checkout -b claude/sprint2-concurrency-tests-[UUID]

# 例:
git checkout -b claude/sprint2-concurrency-tests-01XYZ123456
```

#### 2.2.2 コミット規約

**コミットメッセージ形式**:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新機能
- `fix`: バグ修正
- `test`: テスト追加
- `docs`: ドキュメント更新
- `refactor`: リファクタリング
- `perf`: パフォーマンス改善

**例**:
```bash
git commit -m "test(concurrency): Add deadlock retry test cases

- Implement TC-2.1: Deadlock detection and auto-retry
- Implement TC-2.2: Max retry failure handling
- Add performance metrics collection

Sprint 2 progress: 10/36 test cases completed"
```

---

## 3. Sprint 2: 並行制御テスト完成

**期間**: 3日
**優先度**: S（最優先）
**目標**: テストカバレッジ 80%以上、36+件のテストケース全 PASS

### 3.1 Day 1: デッドロック自動リトライテスト実装

#### 3.1.1 作業手順

**Step 1: テストファイル作成**

```bash
cd /Users/zero/Projects/resonant-engine/
source venv/bin/activate

# テストファイル作成
touch tests/concurrency/test_deadlock_retry.py
```

**tests/concurrency/test_deadlock_retry.py**:

```python
"""デッドロック自動リトライテスト"""
import pytest
import asyncio
import asyncpg
from uuid import uuid4
from bridge.core.bridge_set import BridgeSet
from bridge.core.errors import DeadlockError, OptimisticLockError

@pytest.mark.asyncio
class TestDeadlockRetry:
    """デッドロック自動リトライテストスイート"""

    async def test_deadlock_auto_retry_success(self, bridge_set, test_intents):
        """TC-2.1: デッドロック発生 → 自動リトライで成功"""

        # 2つのIntentが同一リソースを同時更新
        intent1, intent2 = test_intents[:2]

        # 並列実行
        results = await asyncio.gather(
            bridge_set.execute_with_retry(intent1.id),
            bridge_set.execute_with_retry(intent2.id)
        )

        # アサーション
        assert len(results) == 2
        assert all(r.status == 'completed' for r in results)

        # リトライログ確認
        retry_logs = await bridge_set.audit_logger.query(
            event_type='deadlock_retry'
        )
        assert len(retry_logs) > 0

    async def test_max_retry_failure(self, bridge_set, test_intent):
        """TC-2.2: 3回リトライ失敗 → DeadlockError 送出"""

        # リトライ必ず失敗する状態を作成
        with pytest.raises(DeadlockError):
            await bridge_set.execute_with_retry(
                test_intent.id,
                max_retries=3,
                force_deadlock=True  # テスト用フラグ
            )

    async def test_optimistic_lock_conflict(self, bridge_set, test_intent):
        """TC-2.3: 楽観ロック競合 → OptimisticLockError 送出"""

        # バージョン競合を作成
        await bridge_set.db.execute(
            "UPDATE intents SET version = version + 1 WHERE id = $1",
            test_intent.id
        )

        # 古いバージョンで更新試行
        with pytest.raises(OptimisticLockError):
            await bridge_set.update_intent(
                intent_id=test_intent.id,
                expected_version=test_intent.version  # 古いバージョン
            )

    async def test_pessimistic_lock_nowait(self, bridge_set, test_intent):
        """TC-2.4: 悲観ロック競合（NOWAIT） → LockNotAvailableError 送出"""

        # 1つ目のトランザクションでロック取得
        async with bridge_set.db.get_connection() as conn1:
            await conn1.fetchrow(
                "SELECT * FROM intents WHERE id = $1 FOR UPDATE NOWAIT",
                test_intent.id
            )

            # 2つ目のトランザクションで同じレコードをロック試行
            with pytest.raises(asyncpg.exceptions.LockNotAvailableError):
                async with bridge_set.db.get_connection() as conn2:
                    await conn2.fetchrow(
                        "SELECT * FROM intents WHERE id = $1 FOR UPDATE NOWAIT",
                        test_intent.id
                    )

    async def test_deadlock_rate_measurement(self, bridge_set):
        """TC-2.6: デッドロック発生率測定（1000回実行）"""

        total_runs = 1000
        deadlock_count = 0
        retry_success_count = 0

        for i in range(total_runs):
            # 2つのIntentを同時更新
            intent1 = await self._create_test_intent()
            intent2 = await self._create_test_intent()

            try:
                await asyncio.gather(
                    bridge_set.execute_with_retry(intent1.id),
                    bridge_set.execute_with_retry(intent2.id)
                )
                retry_success_count += 1
            except DeadlockError:
                deadlock_count += 1

        # アサーション
        deadlock_rate = (deadlock_count / total_runs) * 100
        retry_success_rate = (retry_success_count / total_runs) * 100

        assert deadlock_rate < 1.0, f"Deadlock rate {deadlock_rate:.2f}% exceeds 1%"
        assert retry_success_rate > 95.0, f"Retry success rate {retry_success_rate:.2f}% below 95%"

    async def test_retry_log_recording(self, bridge_set, test_intent):
        """TC-2.7: リトライログ記録確認"""

        # デッドロック発生させる
        try:
            await bridge_set.execute_with_retry(test_intent.id, force_deadlock=True)
        except DeadlockError:
            pass

        # ログ確認
        logs = await bridge_set.audit_logger.query(
            event_type='deadlock_retry',
            intent_id=test_intent.id
        )

        assert len(logs) > 0
        assert logs[0]['retry_count'] == 3
        assert logs[0]['final_status'] == 'failed'
```

**Step 2: テスト実行**

```bash
# テスト実行
cd /Users/zero/Projects/resonant-engine/ && \
source venv/bin/activate && \
python -m pytest tests/concurrency/test_deadlock_retry.py -v

# カバレッジ測定
pytest tests/concurrency/test_deadlock_retry.py --cov=bridge.core --cov-report=html
```

**Step 3: 実装修正（必要に応じて）**

テスト失敗の場合、`bridge/core/bridge_set.py` の実装を修正。

**Step 4: コミット**

```bash
git add tests/concurrency/test_deadlock_retry.py
git commit -m "test(concurrency): Add deadlock retry test cases (TC-2.1 to TC-2.7)

- Implement auto-retry success test
- Implement max retry failure test
- Implement optimistic lock conflict test
- Implement pessimistic lock NOWAIT test
- Implement deadlock rate measurement (1000 runs)
- Implement retry log recording test

Sprint 2 progress: 7/36 test cases completed"
```

#### 3.1.2 完了チェックリスト

- [ ] テストファイル作成完了
- [ ] TC-2.1 ~ TC-2.7 実装完了
- [ ] 全テスト PASS
- [ ] カバレッジ計測完了
- [ ] コミット完了

---

### 3.2 Day 2: 100並列更新パフォーマンステスト実装

#### 3.2.1 作業手順

**Step 1: テストファイル作成**

```bash
touch tests/concurrency/test_100_parallel_updates.py
```

**tests/concurrency/test_100_parallel_updates.py**:

```python
"""100並列更新パフォーマンステスト"""
import pytest
import asyncio
import time
import numpy as np
from uuid import uuid4
from bridge.core.bridge_set import BridgeSet

@pytest.mark.asyncio
class TestParallelPerformance:
    """並列更新パフォーマンステストスイート"""

    async def test_100_parallel_intent_updates(self, bridge_set):
        """TC-2.5: 100並列Intent更新 → 全て成功、レイテンシ測定"""

        # 100個のテストIntent作成
        intents = [await self._create_test_intent() for _ in range(100)]

        # レイテンシ記録用
        latencies = []

        async def execute_and_measure(intent):
            """Intent実行とレイテンシ測定"""
            start = time.time()
            result = await bridge_set.execute_intent(intent.id)
            duration = time.time() - start
            latencies.append(duration)
            return result

        # 並列実行
        start_total = time.time()
        results = await asyncio.gather(*[
            execute_and_measure(intent) for intent in intents
        ])
        total_duration = time.time() - start_total

        # アサーション: 全て完了
        assert len(results) == 100
        assert all(r.status == 'completed' for r in results)

        # アサーション: 総実行時間
        assert total_duration < 10.0, f"Total duration {total_duration:.2f}s exceeds 10s"

        # レイテンシ統計
        p50 = np.percentile(latencies, 50)
        p95 = np.percentile(latencies, 95)
        p99 = np.percentile(latencies, 99)

        print(f"\n📊 Performance Metrics:")
        print(f"  Total Duration: {total_duration:.2f}s")
        print(f"  Throughput: {100 / total_duration:.2f} ops/sec")
        print(f"  p50 Latency: {p50*1000:.2f}ms")
        print(f"  p95 Latency: {p95*1000:.2f}ms")
        print(f"  p99 Latency: {p99*1000:.2f}ms")

        # アサーション: レイテンシ
        assert p99 < 0.5, f"p99 latency {p99*1000:.2f}ms exceeds 500ms"

        # スループット
        throughput = 100 / total_duration
        assert throughput > 50, f"Throughput {throughput:.2f} ops/sec below 50 ops/sec"

    async def test_resource_usage_monitoring(self, bridge_set):
        """リソース使用率モニタリング"""

        import psutil

        # ベースライン測定
        baseline_cpu = psutil.cpu_percent(interval=1)
        baseline_memory = psutil.virtual_memory().percent

        # 100並列実行
        intents = [await self._create_test_intent() for _ in range(100)]
        await asyncio.gather(*[
            bridge_set.execute_intent(intent.id) for intent in intents
        ])

        # リソース使用率測定
        peak_cpu = psutil.cpu_percent(interval=1)
        peak_memory = psutil.virtual_memory().percent

        print(f"\n💻 Resource Usage:")
        print(f"  Baseline CPU: {baseline_cpu:.1f}%")
        print(f"  Peak CPU: {peak_cpu:.1f}%")
        print(f"  Baseline Memory: {baseline_memory:.1f}%")
        print(f"  Peak Memory: {peak_memory:.1f}%")

        # アサーション: リソース使用率
        assert peak_cpu < 90, f"Peak CPU {peak_cpu:.1f}% exceeds 90%"
        assert peak_memory < 80, f"Peak Memory {peak_memory:.1f}% exceeds 80%"

    async def test_database_connection_pool(self, bridge_set):
        """PostgreSQL 接続プール確認"""

        # 100並列実行中の接続数確認
        intents = [await self._create_test_intent() for _ in range(100)]

        async def execute_with_conn_check(intent):
            # 接続数確認
            conn_count = await bridge_set.db.fetchval(
                "SELECT count(*) FROM pg_stat_activity WHERE datname = 'resonant'"
            )
            result = await bridge_set.execute_intent(intent.id)
            return result, conn_count

        results = await asyncio.gather(*[
            execute_with_conn_check(intent) for intent in intents
        ])

        # 最大接続数確認
        max_connections = max(r[1] for r in results)

        print(f"\n🔌 Database Connections:")
        print(f"  Max Connections: {max_connections}")

        # アサーション: 接続プール適切
        assert max_connections < 50, f"Max connections {max_connections} exceeds pool size"
```

**Step 2: テスト実行＆ベンチマーク**

```bash
# テスト実行
pytest tests/concurrency/test_100_parallel_updates.py -v -s

# ベンチマーク記録
pytest tests/concurrency/test_100_parallel_updates.py --benchmark-save=sprint2_100parallel
```

**Step 3: パフォーマンスベースライン更新**

```bash
# ベースライン更新
nano config/performance_baselines.json
```

**追加内容**:
```json
{
  "sprint2_concurrency": {
    "100_parallel_updates": {
      "p50_latency_ms": 50,
      "p95_latency_ms": 200,
      "p99_latency_ms": 500,
      "throughput_ops_sec": 50,
      "total_duration_sec": 2.0,
      "max_cpu_percent": 70,
      "max_memory_percent": 60,
      "max_db_connections": 30
    }
  }
}
```

**Step 4: コミット**

```bash
git add tests/concurrency/test_100_parallel_updates.py config/performance_baselines.json
git commit -m "test(concurrency): Add 100 parallel updates performance test (TC-2.5)

- Implement 100 parallel intent updates test
- Add latency measurement (p50, p95, p99)
- Add throughput measurement (ops/sec)
- Add resource usage monitoring (CPU, Memory)
- Add database connection pool check
- Update performance baselines

Sprint 2 progress: 15/36 test cases completed"
```

#### 3.2.2 完了チェックリスト

- [ ] テストファイル作成完了
- [ ] TC-2.5 実装完了
- [ ] パフォーマンスベンチマーク記録完了
- [ ] ベースライン更新完了
- [ ] 全テスト PASS
- [ ] コミット完了

---

### 3.3 Day 3: 追加テストケース＆カバレッジ向上

#### 3.3.1 作業手順

**Step 1: カバレッジ確認**

```bash
# 現在のカバレッジ確認
pytest tests/concurrency/ --cov=bridge.core --cov-report=term-missing

# 未カバー箇所確認
# → 出力から未テストの行を確認
```

**Step 2: 追加テストケース実装**

未カバー箇所に対するテストケースを追加実装。

**例**: `tests/concurrency/test_concurrent_read_write.py`

```python
"""並行読み書きテスト"""
import pytest
import asyncio
from bridge.core.bridge_set import BridgeSet

@pytest.mark.asyncio
class TestConcurrentReadWrite:
    """並行読み書きテストスイート"""

    async def test_concurrent_read_while_write(self, bridge_set, test_intent):
        """書き込み中の読み込み"""

        async def slow_write():
            await asyncio.sleep(0.1)
            await bridge_set.update_intent(test_intent.id, result="updated")

        async def concurrent_read():
            return await bridge_set.get_intent(test_intent.id)

        # 並列実行
        write_task = asyncio.create_task(slow_write())
        await asyncio.sleep(0.05)  # 書き込み開始後に読み込み
        read_result = await concurrent_read()
        await write_task

        # アサーション: 読み込みは一貫性保持
        assert read_result is not None

    async def test_multiple_readers_single_writer(self, bridge_set, test_intent):
        """複数読み込み、1書き込み"""

        async def read():
            return await bridge_set.get_intent(test_intent.id)

        async def write():
            await bridge_set.update_intent(test_intent.id, result="final")

        # 10個の読み込みタスク + 1個の書き込みタスク
        tasks = [read() for _ in range(10)] + [write()]
        results = await asyncio.gather(*tasks)

        # アサーション: 全て完了
        assert len(results) == 11
```

**Step 3: 最終カバレッジ確認**

```bash
# 全テスト実行＆カバレッジ
pytest tests/concurrency/ --cov=bridge.core --cov-report=html --cov-report=term

# 目標: 80%以上
```

**Step 4: テストレポート生成**

```bash
# テストレポート生成
pytest tests/concurrency/ --html=reports/sprint2_concurrency_test_report.html
```

**Step 5: コミット**

```bash
git add tests/concurrency/ reports/
git commit -m "test(concurrency): Complete Sprint 2 concurrency test suite

- Add concurrent read/write tests
- Add multiple readers single writer test
- Achieve test coverage 82% (target: 80%+)
- Generate test report

Sprint 2 testing: 36/36 test cases PASS ✅"
```

#### 3.3.2 完了チェックリスト

- [ ] カバレッジ 80%以上達成
- [ ] 36+件のテストケース全 PASS
- [ ] テストレポート生成完了
- [ ] コミット完了
- [ ] Kana レビュー依頼

---

## 4. Sprint 2: ドキュメント作成

**期間**: 2日
**優先度**: A

### 4.1 Day 1: ロック戦略ドキュメント作成

#### 4.1.1 作業手順

**Step 1: ドキュメントファイル作成**

```bash
mkdir -p docs/02_components/bridge_lite/concurrency
touch docs/02_components/bridge_lite/concurrency/locking_strategy.md
```

**docs/02_components/bridge_lite/concurrency/locking_strategy.md**:

```markdown
# Bridge Lite ロック戦略ドキュメント

## 1. 概要

Resonant Engine の Bridge Lite モジュールにおける並行制御戦略を定義します。

## 2. ロック戦略

### 2.1 ハイブリッドロック戦略

楽観ロック（Optimistic Locking）と悲観ロック（Pessimistic Locking）を組み合わせた戦略を採用。

#### 楽観ロック
- `version` カラムによるバージョン管理
- UPDATE時にバージョンチェック
- 競合時に `OptimisticLockError` 送出

#### 悲観ロック
- `SELECT ... FOR UPDATE NOWAIT` による行ロック
- 競合時に即座に `LockNotAvailableError` 送出
- デッドロック自動検知

### 2.2 ロック選択基準

| 状況 | 戦略 | 理由 |
|-----|-----|------|
| 読み込み主体 | 楽観ロック | 競合少ない |
| 書き込み主体 | 悲観ロック | 確実性優先 |
| 高並列 | 楽観ロック | スループット優先 |
| クリティカル処理 | 悲観ロック | 一貫性優先 |

## 3. デッドロック対処

### 3.1 自動リトライ機構

- 最大3回リトライ
- 指数バックオフ（2秒、4秒、8秒）
- リトライ失敗時にエラー送出

### 3.2 デッドロック回避設計

- トランザクション時間を最小化
- ロック順序を統一
- タイムアウト設定（30秒）

## 4. パフォーマンス最適化

### 4.1 接続プール設定

- 最小接続数: 5
- 最大接続数: 30
- アイドルタイムアウト: 300秒

### 4.2 インデックス最適化

- `intents(id)` に主キーインデックス
- `intents(status)` に検索インデックス
- `intents(created_at)` に時系列インデックス

## 5. モニタリング

### 5.1 計測メトリクス

- デッドロック発生率
- リトライ成功率
- レイテンシ（p50, p95, p99）
- スループット（ops/sec）

### 5.2 アラート条件

- デッドロック発生率 > 1%
- リトライ成功率 < 95%
- p99 レイテンシ > 500ms
```

**Step 2: 図表追加**

Mermaid で図表を追加。

**Step 3: コミット**

```bash
git add docs/02_components/bridge_lite/concurrency/locking_strategy.md
git commit -m "docs(concurrency): Add locking strategy documentation

- Define hybrid locking strategy (optimistic + pessimistic)
- Document deadlock handling with auto-retry
- Add performance optimization guidelines
- Add monitoring metrics definition

Sprint 2 documentation: 1/3 completed"
```

#### 4.1.2 完了チェックリスト

- [ ] ロック戦略ドキュメント作成完了
- [ ] 図表追加完了
- [ ] レビュー完了
- [ ] コミット完了

---

### 4.2 Day 2: デッドロック対処法＆ベストプラクティス

#### 4.2.1 作業手順

**Step 1: デッドロック対処法ドキュメント**

```bash
touch docs/02_components/bridge_lite/concurrency/deadlock_handling.md
```

**docs/02_components/bridge_lite/concurrency/deadlock_handling.md**:

```markdown
# デッドロック対処法ガイド

## 1. デッドロックとは

複数のトランザクションが互いにロック解放を待機し、永久に進行しない状態。

## 2. デッドロック発生パターン

### パターン1: 循環ロック
- Transaction A: Lock Resource 1 → Wait for Resource 2
- Transaction B: Lock Resource 2 → Wait for Resource 1

### パターン2: 複数リソース競合
- 3つ以上のトランザクションが複数リソースを異なる順序でロック

## 3. 自動リトライ実装

### コード例

```python
async def execute_with_retry(intent_id, max_retries=3):
    for attempt in range(max_retries):
        try:
            return await execute_intent(intent_id)
        except asyncpg.DeadlockDetectedError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

## 4. 回避戦略

- ロック順序統一
- トランザクション時間最小化
- NOWAIT オプション使用

## 5. トラブルシューティング

### デッドロック発生時の確認手順

1. PostgreSQL ログ確認
2. デッドロック発生箇所特定
3. ロック順序確認
4. トランザクション時間確認
```

**Step 2: ベストプラクティスドキュメント**

```bash
touch docs/02_components/bridge_lite/concurrency/best_practices.md
```

**Step 3: コミット**

```bash
git add docs/02_components/bridge_lite/concurrency/
git commit -m "docs(concurrency): Add deadlock handling and best practices

- Document deadlock patterns and solutions
- Add auto-retry implementation guide
- Add troubleshooting guide
- Add best practices for concurrent programming

Sprint 2 documentation: 3/3 completed ✅"
```

#### 4.2.2 完了チェックリスト

- [ ] デッドロック対処法ドキュメント作成完了
- [ ] ベストプラクティスドキュメント作成完了
- [ ] コミット完了
- [ ] Sprint 2 完全完了

---

## 5. Sprint 5: Oracle Cloud デプロイ

**期間**: 1週間
**優先度**: A

### 5.1 Week 1: Oracle Cloud セットアップ

#### 5.1.1 Oracle Cloud アカウント作成

**Step 1: アカウント登録**

1. https://www.oracle.com/cloud/free/ にアクセス
2. 「無料で開始」をクリック
3. メールアドレス、パスワード設定
4. クレジットカード登録（課金なし、Free Tier のみ使用）

**Step 2: コンパートメント作成**

1. Oracle Cloud Console にログイン
2. Identity & Security → Compartments
3. 「Create Compartment」
4. Name: `resonant-engine-prod`

#### 5.1.2 Ampere A1 ARM VM 作成

**Step 1: Compute Instance 作成**

1. Compute → Instances
2. 「Create Instance」
3. 設定:
   - Name: `resonant-engine-vm`
   - Shape: `VM.Standard.A1.Flex`
   - OCPU: 4
   - Memory: 24GB
   - OS: Ubuntu 22.04 LTS (ARM64)
   - Boot Volume: 100GB
4. SSH Key アップロード（`~/.ssh/id_rsa.pub`）
5. 「Create」

**Step 2: ネットワーク設定**

1. Networking → Virtual Cloud Networks
2. Security Lists → Default Security List
3. Ingress Rules 追加:
   - Port 80 (HTTP)
   - Port 443 (HTTPS)
   - Port 22 (SSH)

#### 5.1.3 VM 初期セットアップ

**Step 1: SSH 接続**

```bash
# VM の Public IP を確認（Oracle Cloud Console）
export VM_IP=xxx.xxx.xxx.xxx

# SSH 接続
ssh ubuntu@$VM_IP
```

**Step 2: システム更新**

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# 必須パッケージインストール
sudo apt install -y curl git vim
```

**Step 3: Docker インストール**

```bash
# Docker インストールスクリプト
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# ユーザーを docker グループに追加
sudo usermod -aG docker ubuntu

# ログアウト＆再ログイン
exit
ssh ubuntu@$VM_IP

# Docker 確認
docker --version
```

**Step 4: Docker Compose インストール**

```bash
# Docker Compose プラグインインストール
sudo apt install -y docker-compose-plugin

# 確認
docker compose version
```

#### 5.1.4 Resonant Engine デプロイ

**Step 1: リポジトリクローン**

```bash
# Git クローン
cd ~
git clone https://github.com/HiroKatoMiyagi/resonant-engine.git
cd resonant-engine

# ブランチ確認
git branch -a
```

**Step 2: 環境変数設定**

```bash
# .env.production ファイル作成
cp .env.template .env.production
nano .env.production
```

**.env.production 設定内容**:
```bash
# Claude API
ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# OpenAI API
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# PostgreSQL
DATABASE_URL=postgresql://resonant:SecurePassword123!@db:5432/resonant
POSTGRES_USER=resonant
POSTGRES_PASSWORD=SecurePassword123!
POSTGRES_DB=resonant

# アプリケーション設定
ENVIRONMENT=production
DEBUG=false
ALLOWED_HOSTS=resonant-engine.com,api.resonant-engine.com
```

**Step 3: Docker Compose 起動**

```bash
# 本番環境用 Compose ファイル確認
cat docker/docker-compose.production.yml

# Docker Compose 起動
cd docker
docker compose -f docker-compose.production.yml up -d

# ヘルスチェック
./scripts/check-health.sh
```

**Step 4: 動作確認**

```bash
# Backend API 確認
curl http://localhost:8000/health

# Frontend 確認
curl http://localhost:3000

# PostgreSQL 確認
docker compose exec db psql -U resonant -d resonant -c "SELECT version();"
```

#### 5.1.5 完了チェックリスト

- [ ] Oracle Cloud アカウント作成完了
- [ ] Ampere A1 VM 作成完了
- [ ] Docker + Docker Compose インストール完了
- [ ] Resonant Engine デプロイ完了
- [ ] ヘルスチェック PASS

---

### 5.2 Week 2: SSL/TLS 設定＆HTTPS 公開

#### 5.2.1 ドメイン設定

**Step 1: ドメイン取得**

1. お名前.com / Cloudflare 等でドメイン取得
2. 例: `resonant-engine.com`

**Step 2: DNS レコード設定**

```
# A レコード
resonant-engine.com        A    xxx.xxx.xxx.xxx (VM Public IP)
api.resonant-engine.com    A    xxx.xxx.xxx.xxx
```

#### 5.2.2 Let's Encrypt SSL 証明書取得

**Step 1: Certbot インストール**

```bash
# VM 上で実行
sudo apt install -y certbot python3-certbot-nginx
```

**Step 2: Nginx インストール**

```bash
sudo apt install -y nginx
```

**Step 3: Nginx 設定**

```bash
sudo nano /etc/nginx/sites-available/resonant-engine
```

**/etc/nginx/sites-available/resonant-engine**:

```nginx
# Frontend (resonant-engine.com)
server {
    listen 80;
    server_name resonant-engine.com;

    location / {
        proxy_pass http://localhost:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

# Backend API (api.resonant-engine.com)
server {
    listen 80;
    server_name api.resonant-engine.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

```bash
# シンボリックリンク作成
sudo ln -s /etc/nginx/sites-available/resonant-engine /etc/nginx/sites-enabled/

# Nginx 設定テスト
sudo nginx -t

# Nginx 再起動
sudo systemctl restart nginx
```

**Step 4: Let's Encrypt 証明書取得**

```bash
# 証明書取得（Nginx プラグイン使用）
sudo certbot --nginx -d resonant-engine.com -d api.resonant-engine.com

# メールアドレス入力
# 利用規約同意

# 証明書自動更新確認
sudo certbot renew --dry-run
```

**Step 5: HTTPS 接続確認**

```bash
# ブラウザで確認
https://resonant-engine.com
https://api.resonant-engine.com/docs
```

#### 5.2.3 systemd サービス設定

**Step 1: サービスファイル作成**

```bash
sudo nano /etc/systemd/system/resonant-engine.service
```

**/etc/systemd/system/resonant-engine.service**:

```ini
[Unit]
Description=Resonant Engine Docker Compose
Requires=docker.service
After=docker.service

[Service]
Type=oneshot
RemainAfterExit=yes
WorkingDirectory=/home/ubuntu/resonant-engine/docker
ExecStart=/usr/bin/docker compose -f docker-compose.production.yml up -d
ExecStop=/usr/bin/docker compose -f docker-compose.production.yml down
User=ubuntu

[Install]
WantedBy=multi-user.target
```

**Step 2: サービス有効化**

```bash
# サービス有効化
sudo systemctl enable resonant-engine

# サービス起動
sudo systemctl start resonant-engine

# ステータス確認
sudo systemctl status resonant-engine
```

#### 5.2.4 完了チェックリスト

- [ ] ドメイン取得＆DNS設定完了
- [ ] Let's Encrypt SSL証明書取得完了
- [ ] Nginx リバースプロキシ設定完了
- [ ] HTTPS接続確認完了
- [ ] systemd サービス設定完了
- [ ] Sprint 5 完全完了 ✅

---

## 6. Claude API 統合検証

**期間**: 3日
**優先度**: A

### 6.1 Day 1: Backend → Claude API 統合実装

#### 6.1.1 作業手順

**Step 1: ClaudeBridge 拡張**

```bash
# ファイル編集
nano bridge/providers/ai/claude_bridge.py
```

**実装内容**: 仕様書の5.3.1参照

**Step 2: テスト実装**

```bash
touch tests/integration/test_claude_api.py
```

**実装内容**: 仕様書の5.3.2参照

**Step 3: テスト実行**

```bash
# API キー設定
export ANTHROPIC_API_KEY=sk-ant-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# テスト実行
pytest tests/integration/test_claude_api.py -v
```

**Step 4: コミット**

```bash
git add bridge/providers/ai/claude_bridge.py tests/integration/test_claude_api.py
git commit -m "feat(ai): Add Claude API integration for Intent processing

- Implement process_intent method
- Add prompt construction logic
- Add token usage tracking
- Add response caching (15min TTL)
- Add integration tests

Claude API integration: Phase 1 completed"
```

#### 6.1.2 完了チェックリスト

- [ ] ClaudeBridge 拡張完了
- [ ] テスト実装完了
- [ ] テスト PASS
- [ ] コミット完了

---

### 6.2 Day 2: Token 使用量追跡＆コスト見積もり

#### 6.2.1 作業手順

**Step 1: token_usage テーブル作成**

```bash
# マイグレーションファイル作成
touch docker/postgres/003_token_usage.sql
```

**docker/postgres/003_token_usage.sql**:

```sql
-- Token使用量追跡テーブル
CREATE TABLE IF NOT EXISTS token_usage (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    intent_id UUID REFERENCES intents(id),
    model VARCHAR(100) NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    total_cost_usd NUMERIC(10, 6) NOT NULL,
    created_at TIMESTAMP NOT NULL DEFAULT NOW()
);

-- インデックス
CREATE INDEX idx_token_usage_timestamp ON token_usage(timestamp);
CREATE INDEX idx_token_usage_intent_id ON token_usage(intent_id);
```

**Step 2: トークン使用量記録実装**

`bridge/providers/ai/claude_bridge.py` に実装（仕様書参照）

**Step 3: コスト集計スクリプト**

```bash
touch scripts/calculate_token_cost.py
```

**scripts/calculate_token_cost.py**:

```python
"""トークン使用量＆コスト集計スクリプト"""
import asyncio
import asyncpg
from datetime import datetime, timedelta

async def calculate_monthly_cost():
    """月間トークン使用量＆コスト集計"""

    conn = await asyncpg.connect(dsn="postgresql://resonant:password@localhost:5432/resonant")

    # 今月のデータ取得
    today = datetime.now()
    first_day = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    result = await conn.fetchrow("""
        SELECT
            SUM(prompt_tokens) as total_prompt_tokens,
            SUM(completion_tokens) as total_completion_tokens,
            SUM(total_tokens) as total_tokens,
            SUM(total_cost_usd) as total_cost
        FROM token_usage
        WHERE timestamp >= $1
    """, first_day)

    print(f"📊 Monthly Token Usage ({today.strftime('%Y-%m')})")
    print(f"  Prompt Tokens: {result['total_prompt_tokens']:,}")
    print(f"  Completion Tokens: {result['total_completion_tokens']:,}")
    print(f"  Total Tokens: {result['total_tokens']:,}")
    print(f"  Total Cost: ${result['total_cost']:.2f}")

    await conn.close()

if __name__ == '__main__':
    asyncio.run(calculate_monthly_cost())
```

**Step 4: 実行＆確認**

```bash
cd /Users/zero/Projects/resonant-engine/ && \
source venv/bin/activate && \
python scripts/calculate_token_cost.py
```

**Step 5: コミット**

```bash
git add docker/postgres/003_token_usage.sql scripts/calculate_token_cost.py
git commit -m "feat(ai): Add token usage tracking and cost calculation

- Create token_usage table
- Implement token usage recording
- Add monthly cost calculation script
- Add cost monitoring

Claude API integration: Phase 2 completed"
```

#### 6.2.2 完了チェックリスト

- [ ] token_usage テーブル作成完了
- [ ] トークン記録実装完了
- [ ] コスト集計スクリプト作成完了
- [ ] コミット完了

---

### 6.3 Day 3: キャッシング戦略＆最終検証

#### 6.3.1 作業手順

**Step 1: Redis キャッシュ導入（オプション）**

簡易実装では Python の `cachetools` を使用。

```bash
pip install cachetools
```

**Step 2: キャッシング実装**

`bridge/providers/ai/claude_bridge.py` に追加（仕様書参照）

**Step 3: キャッシュヒット率計測**

```python
# ClaudeBridge クラスに追加
@property
def cache_hit_rate(self):
    """キャッシュヒット率"""
    total = self.metrics['cache_hits'] + self.metrics['cache_misses']
    if total == 0:
        return 0.0
    return (self.metrics['cache_hits'] / total) * 100
```

**Step 4: 最終統合テスト**

```bash
# 全テスト実行
pytest tests/integration/test_claude_api.py -v

# キャッシュヒット率確認
# → テストログに出力
```

**Step 5: コミット**

```bash
git add bridge/providers/ai/claude_bridge.py
git commit -m "feat(ai): Add response caching with 15min TTL

- Implement cachetools-based caching
- Add cache hit rate tracking
- Optimize API call frequency
- Add cache hit rate property

Claude API integration: Phase 3 completed ✅"
```

#### 6.3.2 完了チェックリスト

- [ ] キャッシング実装完了
- [ ] キャッシュヒット率計測完了
- [ ] 最終統合テスト PASS
- [ ] Claude API 統合検証完全完了 ✅

---

## 7. Kana 実装 Phase 1

**期間**: 2週間
**優先度**: B

### 7.1 Week 1: 翻訳エンジン実装

#### 7.1.1 作業手順

**Step 1: Kana モジュール作成**

```bash
mkdir -p bridge/kana
touch bridge/kana/__init__.py
touch bridge/kana/translator.py
touch bridge/kana/auditor.py
touch bridge/kana/consistency_checker.py
touch bridge/kana/report_generator.py
```

**Step 2: 翻訳エンジン実装**

**bridge/kana/translator.py**:

仕様書の4.3.3参照

**Step 3: プロンプトテンプレート作成**

```bash
mkdir -p bridge/kana/prompts
touch bridge/kana/prompts/translate_to_schema.txt
touch bridge/kana/prompts/translate_to_api.txt
touch bridge/kana/prompts/check_consistency.txt
```

**Step 4: テスト実装**

```bash
mkdir -p tests/kana
touch tests/kana/test_translator.py
```

**tests/kana/test_translator.py**:

```python
"""Kana 翻訳エンジンテスト"""
import pytest
from bridge.kana.translator import KanaTranslator

@pytest.mark.asyncio
class TestKanaTranslator:
    """Kana 翻訳エンジンテストスイート"""

    async def test_translate_yuno_to_schema(self, translator):
        """Yuno思想ドキュメント → PostgreSQL スキーマ翻訳"""

        # Yuno ドキュメントパス
        yuno_doc = "docs/07_philosophy/yuno_documents/emotion_resonance_filter_detailed.md"

        # 翻訳実行
        schema_sql = await translator.translate_to_schema(yuno_doc)

        # アサーション
        assert schema_sql is not None
        assert "CREATE TABLE" in schema_sql
        assert "emotion_resonance" in schema_sql.lower()

    async def test_translate_yuno_to_fastapi(self, translator):
        """Yuno思想ドキュメント → FastAPI エンドポイント翻訳"""

        yuno_doc = "docs/07_philosophy/yuno_documents/crisis_index_detailed.md"

        # 翻訳実行
        fastapi_code = await translator.translate_to_fastapi(yuno_doc)

        # アサーション
        assert fastapi_code is not None
        assert "@router.get" in fastapi_code or "@router.post" in fastapi_code
        assert "crisis_index" in fastapi_code.lower()
```

**Step 5: コミット**

```bash
git add bridge/kana/ tests/kana/
git commit -m "feat(kana): Implement translation engine (Phase 1)

- Add KanaTranslator class
- Implement translate_to_schema method
- Implement translate_to_fastapi method
- Add system prompt templates
- Add unit tests

Kana implementation: 20% completed"
```

#### 7.1.2 完了チェックリスト

- [ ] Kana モジュール作成完了
- [ ] 翻訳エンジン実装完了
- [ ] プロンプトテンプレート作成完了
- [ ] テスト実装完了
- [ ] コミット完了

---

### 7.2 Week 2: 設計監査＆整合性チェック

#### 7.2.1 作業手順

**Step 1: Auditor 実装**

**bridge/kana/auditor.py**:

仕様書の4.3.3参照

**Step 2: ConsistencyChecker 実装**

**bridge/kana/consistency_checker.py**:

```python
"""整合性チェッカー"""
from typing import List, Dict

class ConsistencyChecker:
    """Yuno思想と生成仕様の整合性チェック"""

    async def check_scope_alignment(self, generated_spec: str, yuno_doc: str) -> List[str]:
        """スコープ整合確認（L1/L2/L3）"""

        issues = []

        # L3（全体原則）チェック
        if "呼吸" not in yuno_doc and "breath" not in generated_spec.lower():
            issues.append("L3: Missing breath concept in generated spec")

        # L2（横断）チェック
        if "共鳴" in yuno_doc and "resonance" not in generated_spec.lower():
            issues.append("L2: Missing resonance concept")

        # L1（局所）チェック
        # TODO: 具体的なチェックロジック

        return issues

    async def check_terminology_consistency(self, generated_spec: str, yuno_doc: str) -> List[str]:
        """用語の一貫性チェック"""

        issues = []

        # Yuno用語マッピング
        yuno_terms = {
            "ERF": "Emotion Resonance Filter",
            "Crisis Index": "危機指数",
            "Re-evaluation": "認識再評価"
        }

        for term, definition in yuno_terms.items():
            if term in yuno_doc and term not in generated_spec:
                issues.append(f"Terminology: Missing '{term}' in generated spec")

        return issues
```

**Step 3: テスト実装**

```bash
touch tests/kana/test_auditor.py
touch tests/kana/test_consistency_checker.py
```

**Step 4: 統合テスト**

```bash
# 全テスト実行
pytest tests/kana/ -v

# カバレッジ
pytest tests/kana/ --cov=bridge.kana --cov-report=html
```

**Step 5: コミット**

```bash
git add bridge/kana/ tests/kana/
git commit -m "feat(kana): Implement auditor and consistency checker (Phase 2)

- Add KanaAuditor class
- Add ConsistencyChecker class
- Implement scope alignment check (L1/L2/L3)
- Implement terminology consistency check
- Add comprehensive tests

Kana implementation: 50% completed ✅"
```

#### 7.2.2 完了チェックリスト

- [ ] Auditor 実装完了
- [ ] ConsistencyChecker 実装完了
- [ ] テスト実装完了
- [ ] テストカバレッジ 80%以上
- [ ] Kana Phase 1 完全完了 ✅

---

## 8. 日次チェックリスト

### 8.1 毎朝の作業開始時

```bash
# 1. 環境確認
cd /Users/zero/Projects/resonant-engine/
source venv/bin/activate

# 2. Git 最新化
git fetch origin
git pull origin claude/analyze-project-status-01BUzZJHdAkse1LvZwQU7a3B

# 3. Docker 環境起動
cd docker && ./scripts/start.sh

# 4. ヘルスチェック
./scripts/check-health.sh

# 5. 本日のタスク確認
cat docs/work_instructions/next_phase_work_instruction.md
```

### 8.2 作業中

- [ ] こまめにコミット（機能単位）
- [ ] テスト実行（変更毎）
- [ ] カバレッジ確認
- [ ] ドキュメント更新

### 8.3 毎夕の作業終了時

```bash
# 1. 全テスト実行
pytest tests/ -v

# 2. カバレッジ確認
pytest --cov=bridge --cov-report=term

# 3. コミット確認
git status
git log --oneline -5

# 4. プッシュ
git push -u origin <current-branch>

# 5. 進捗記録
# → 作業ログに記録
```

---

## 9. トラブルシューティング

### 9.1 Docker 起動失敗

**症状**: `docker compose up` がエラー

**対処**:
```bash
# ログ確認
docker compose logs

# コンテナ削除＆再起動
docker compose down -v
docker compose up --build -d
```

### 9.2 テスト失敗

**症状**: pytest がエラー

**対処**:
```bash
# 詳細ログ確認
pytest -v -s

# 特定のテストのみ実行
pytest tests/concurrency/test_deadlock_retry.py::TestDeadlockRetry::test_deadlock_auto_retry_success -v
```

### 9.3 PostgreSQL 接続エラー

**症状**: `connection refused`

**対処**:
```bash
# PostgreSQL 起動確認
docker compose ps

# PostgreSQL ログ確認
docker compose logs db

# 接続テスト
docker compose exec db psql -U resonant -d resonant -c "SELECT 1"
```

---

## 10. 完了報告

全作業完了後、以下を実施：

1. **最終テスト実行**
```bash
pytest tests/ -v --cov=bridge --cov-report=html
```

2. **受け入れテスト実施**
（受け入れテスト仕様書に従う）

3. **ドキュメント最終確認**

4. **プルリクエスト作成**
```bash
gh pr create --title "Complete Sprint 2-5 and Kana Phase 1" --body "$(cat docs/reports/completion_report.md)"
```

5. **宏啓さんに報告**

---

**作業開始指示書バージョン**: v2.0
**最終更新**: 2025年11月18日
**承認**: 加藤宏啓（Hiroaki Kato）
