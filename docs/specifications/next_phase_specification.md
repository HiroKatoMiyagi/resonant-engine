# Resonant Engine 次期開発フェーズ仕様書

**バージョン**: v2.0
**作成日**: 2025年11月18日
**作成者**: Kana（翻訳層）
**対象期間**: 2025年11月18日 - 2025年12月31日

---

## 1. エグゼクティブサマリー

本仕様書は、Resonant Engine プロジェクトの現状分析に基づき、次期開発フェーズ（v2.0）の詳細仕様を定義します。

### 1.1 現状認識

**達成状況**:
- ✅ Sprint 1-4 完全実装（受け入れテスト 30/30 PASS）
- ✅ PostgreSQL + Docker 環境構築
- ✅ FastAPI バックエンド（21 API）
- ✅ React フロントエンド（3ページ）
- ✅ Intent 自動処理デーモン
- ✅ Bridge Lite モジュール（テストカバレッジ 87%）
- ✅ 統一イベントストリーム

**課題**:
- ❌ Sprint 2 並行制御テスト未完成
- ❌ Yuno（思想層）実装化なし
- ❌ Kana（翻訳層）完全実装なし
- ❌ Sprint 5 Oracle Cloud デプロイ未開始
- ❌ Claude API 統合検証不足

### 1.2 目標

**短期目標（1-2週間）**:
1. Sprint 2 並行制御テスト完成（テストカバレッジ 80%以上）
2. Sprint 2 ドキュメント完成
3. Sprint 5 デプロイ準備開始

**中期目標（1ヶ月）**:
1. Oracle Cloud 本番デプロイ完了
2. Claude API 統合検証完了
3. Kana（翻訳層）実装開始

**長期目標（3ヶ月）**:
1. Yuno（思想層）部分実装
2. 自動コード生成機能
3. 研究発表準備

---

## 2. Sprint 2 並行制御強化仕様

### 2.1 概要

**目的**: 複数Intent間のデッドロック対処と100並列更新のパフォーマンス検証

**期間**: 3日
**担当**: Tsumu（具現化層）
**レビュー**: Kana（翻訳層）

### 2.2 要件定義

#### 2.2.1 機能要件

**FR-2.1: デッドロック自動リトライ**
- 複数Intentが同時に同一リソースを更新する際のデッドロック検知
- 自動リトライ機能（最大3回、指数バックオフ）
- リトライ失敗時のエラーハンドリング
- 監査ログへの記録

**FR-2.2: 楽観ロック＋悲観ロックのハイブリッド戦略**
- `SELECT ... FOR UPDATE NOWAIT` による悲観ロック
- `version` カラムによる楽観ロック
- ロック競合時の適切なエラーレスポンス

**FR-2.3: 100並列更新パフォーマンステスト**
- 100個の並列Intent更新
- レイテンシ計測（p50, p95, p99）
- スループット計測（ops/sec）
- リソース使用率モニタリング（CPU, メモリ, DB接続）

#### 2.2.2 非機能要件

**NFR-2.1: パフォーマンス**
- p99 レイテンシ < 500ms
- スループット > 50 ops/sec
- デッドロック発生率 < 1%

**NFR-2.2: 信頼性**
- リトライ成功率 > 95%
- トランザクション一貫性 100%
- データロス 0件

**NFR-2.3: 保守性**
- テストカバレッジ > 80%
- ドキュメント完備
- ログ可視化

### 2.3 技術仕様

#### 2.3.1 デッドロック検知＆リトライ実装

**実装場所**: `bridge/core/bridge_set.py`

```python
# 疑似コード
async def execute_with_retry(self, intent_id: str, max_retries: int = 3):
    """デッドロック自動リトライ"""
    for attempt in range(max_retries):
        try:
            async with self.db_bridge.get_connection() as conn:
                # 悲観ロック
                intent = await conn.fetchrow(
                    "SELECT * FROM intents WHERE id = $1 FOR UPDATE NOWAIT",
                    intent_id
                )

                # 楽観ロック（バージョンチェック）
                if intent['version'] != expected_version:
                    raise OptimisticLockError()

                # 処理実行
                result = await self.process_intent(intent)

                # バージョンインクリメント＆更新
                await conn.execute(
                    "UPDATE intents SET result = $1, version = version + 1 WHERE id = $2 AND version = $3",
                    result, intent_id, intent['version']
                )

                return result

        except asyncpg.exceptions.DeadlockDetectedError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)  # 指数バックオフ

        except asyncpg.exceptions.LockNotAvailableError:
            if attempt == max_retries - 1:
                raise
            await asyncio.sleep(2 ** attempt)
```

#### 2.3.2 テストケース定義

**テストファイル**: `tests/concurrency/test_deadlock_retry.py`

```python
# テストケース一覧
TC-2.1: 2つのIntentが同一リソースを更新してデッドロック発生 → 自動リトライで成功
TC-2.2: 3回リトライ失敗 → DeadlockError 送出
TC-2.3: 楽観ロック競合 → OptimisticLockError 送出
TC-2.4: 悲観ロック競合（NOWAIT） → LockNotAvailableError 送出
TC-2.5: 100並列更新 → 全て成功、レイテンシ測定
TC-2.6: デッドロック発生率測定（1000回実行）
TC-2.7: リトライログ記録確認
```

**テストファイル**: `tests/concurrency/test_100_parallel_updates.py`

```python
async def test_100_parallel_intent_updates():
    """100並列Intent更新パフォーマンステスト"""
    intents = [create_test_intent() for _ in range(100)]

    start = time.time()
    results = await asyncio.gather(*[
        bridge_set.execute_intent(intent) for intent in intents
    ])
    duration = time.time() - start

    # アサーション
    assert len(results) == 100
    assert all(r.status == 'completed' for r in results)
    assert duration < 10.0  # 10秒以内

    # レイテンシ計測
    latencies = [r.duration for r in results]
    p50 = np.percentile(latencies, 50)
    p95 = np.percentile(latencies, 95)
    p99 = np.percentile(latencies, 99)

    assert p99 < 0.5  # 500ms
```

#### 2.3.3 パフォーマンス計測

**計測項目**:
- p50, p95, p99 レイテンシ
- スループット（ops/sec）
- デッドロック発生回数
- リトライ成功率
- CPU使用率
- メモリ使用率
- PostgreSQL 接続数

**計測ツール**: `scripts/extract_performance_metrics.py`

**ベースライン**: `config/performance_baselines.json`

```json
{
  "sprint2_concurrency": {
    "p50_latency_ms": 50,
    "p95_latency_ms": 200,
    "p99_latency_ms": 500,
    "throughput_ops_sec": 50,
    "deadlock_rate_percent": 1.0,
    "retry_success_rate_percent": 95.0
  }
}
```

### 2.4 受け入れ基準（Definition of Done）

- [ ] テストカバレッジ 80%以上
- [ ] 36+件のテストケース全 PASS
- [ ] パフォーマンスベースライン達成
- [ ] ドキュメント完成（ロック戦略、デッドロック対処法）
- [ ] Kana レビュー承認
- [ ] CI/CD パイプライン PASS

---

## 3. Sprint 5: Oracle Cloud デプロイ仕様

### 3.1 概要

**目的**: 本番環境へのデプロイとHTTPS公開

**期間**: 1週間
**担当**: Tsumu（具現化層）
**レビュー**: Kana（翻訳層）

### 3.2 要件定義

#### 3.2.1 機能要件

**FR-5.1: Oracle Cloud Infrastructure セットアップ**
- Oracle Cloud Free Tier アカウント作成
- Ampere A1 ARM VM 作成（4 OCPU, 24GB RAM）
- Ubuntu 22.04 LTS インストール
- Docker + Docker Compose インストール

**FR-5.2: SSL/TLS 証明書取得**
- Let's Encrypt 証明書取得
- Certbot 自動更新設定
- HTTPS リダイレクト設定

**FR-5.3: Nginx リバースプロキシ**
- Backend API (localhost:8000) → https://api.resonant-engine.com
- Frontend (localhost:3000) → https://resonant-engine.com
- WebSocket プロキシ設定

**FR-5.4: 環境変数管理**
- `.env.production` ファイル作成
- シークレット管理（API キー等）
- ログローテーション設定

**FR-5.5: ヘルスチェック＆監視**
- `/health` エンドポイント監視
- Uptime 監視（UptimeRobot等）
- エラーアラート（Email通知）

#### 3.2.2 非機能要件

**NFR-5.1: セキュリティ**
- HTTPS のみ（HTTP → HTTPS リダイレクト）
- API キー環境変数管理
- PostgreSQL 外部アクセス禁止
- SSH 鍵認証のみ

**NFR-5.2: 可用性**
- Uptime > 99%
- 自動再起動設定（systemd）
- データベースバックアップ（日次）

**NFR-5.3: パフォーマンス**
- レスポンスタイム < 1秒
- SSL/TLS ハンドシェイク < 100ms

### 3.3 技術仕様

#### 3.3.1 Oracle Cloud VM セットアップ

**スペック**:
- Shape: VM.Standard.A1.Flex
- OCPU: 4
- Memory: 24GB
- Storage: 100GB Boot Volume
- OS: Ubuntu 22.04 LTS (ARM64)

**セットアップスクリプト**: `docker/scripts/oracle_cloud_setup.sh`

```bash
#!/bin/bash
# Oracle Cloud VM セットアップスクリプト

# 1. システム更新
sudo apt update && sudo apt upgrade -y

# 2. Docker インストール
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# 3. Docker Compose インストール
sudo apt install docker-compose-plugin -y

# 4. Git クローン
git clone https://github.com/HiroKatoMiyagi/resonant-engine.git
cd resonant-engine

# 5. 環境変数設定
cp .env.template .env.production
nano .env.production  # API キー等を設定

# 6. Docker 起動
cd docker && docker compose -f docker-compose.production.yml up -d

# 7. ヘルスチェック
./scripts/check-health.sh
```

#### 3.3.2 Nginx リバースプロキシ設定

**設定ファイル**: `docker/nginx/nginx.conf`

```nginx
# HTTPS リバースプロキシ設定
server {
    listen 443 ssl http2;
    server_name resonant-engine.com;

    ssl_certificate /etc/letsencrypt/live/resonant-engine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/resonant-engine.com/privkey.pem;

    # Frontend
    location / {
        proxy_pass http://frontend:3000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

server {
    listen 443 ssl http2;
    server_name api.resonant-engine.com;

    ssl_certificate /etc/letsencrypt/live/api.resonant-engine.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/api.resonant-engine.com/privkey.pem;

    # Backend API
    location / {
        proxy_pass http://backend:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}

# HTTP → HTTPS リダイレクト
server {
    listen 80;
    server_name resonant-engine.com api.resonant-engine.com;
    return 301 https://$server_name$request_uri;
}
```

#### 3.3.3 Let's Encrypt 証明書取得

```bash
# Certbot インストール
sudo apt install certbot python3-certbot-nginx -y

# 証明書取得
sudo certbot --nginx -d resonant-engine.com -d api.resonant-engine.com

# 自動更新設定
sudo certbot renew --dry-run
```

#### 3.3.4 systemd サービス設定

**サービスファイル**: `/etc/systemd/system/resonant-engine.service`

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

```bash
# サービス有効化
sudo systemctl enable resonant-engine
sudo systemctl start resonant-engine
```

### 3.4 受け入れ基準（Definition of Done）

- [ ] Oracle Cloud VM 起動確認
- [ ] Docker Compose 全サービス稼働
- [ ] HTTPS 接続成功（https://resonant-engine.com）
- [ ] SSL証明書有効性確認
- [ ] ヘルスチェック PASS
- [ ] PostgreSQL データ永続化確認
- [ ] ドキュメント完成（デプロイ手順書）
- [ ] Uptime 監視設定完了

---

## 4. Kana（翻訳層）実装仕様

### 4.1 概要

**目的**: Yuno思想を具体仕様へ自動翻訳する機能の実装

**期間**: 2週間
**担当**: Tsumu（具現化層）
**監督**: Yuno（思想層）
**レビュー**: Kana（翻訳層）

### 4.2 要件定義

#### 4.2.1 機能要件

**FR-K.1: 思想→仕様 自動翻訳**
- Yuno の思想ドキュメント（MD）を読み込み
- Claude API（Sonnet 4.5）による解析
- PostgreSQL スキーマ定義生成
- FastAPI エンドポイント定義生成
- React コンポーネント定義生成

**FR-K.2: 設計監査機能**
- 生成された仕様の整合性チェック
- Yuno 思想との一貫性検証
- スコープ整合（L1/L2/L3）確認

**FR-K.3: 整合性レポート生成**
- 翻訳結果の詳細レポート
- 不整合箇所の指摘
- 修正提案

#### 4.2.2 非機能要件

**NFR-K.1: 精度**
- 翻訳精度 > 90%
- 整合性チェック精度 > 95%

**NFR-K.2: 性能**
- 1ドキュメント翻訳時間 < 30秒
- Claude API トークン使用量 < 10,000 tokens/doc

### 4.3 技術仕様

#### 4.3.1 アーキテクチャ

```
[Yuno思想ドキュメント (MD)]
         ↓
[Kana 翻訳エンジン]
    - Claude API (Sonnet 4.5)
    - システムプロンプト定義
    - テンプレート生成
         ↓
[仕様ドキュメント生成]
    - PostgreSQL スキーマ (SQL)
    - FastAPI エンドポイント (Python)
    - React コンポーネント (TSX)
         ↓
[整合性チェック]
    - スコープ整合確認
    - 呼吸の一貫性検証
         ↓
[レポート生成]
    - Markdown レポート
    - 不整合箇所リスト
```

#### 4.3.2 実装場所

**新規モジュール**: `bridge/kana/`

```
bridge/kana/
├── __init__.py
├── translator.py           # 翻訳エンジン
├── auditor.py             # 設計監査
├── consistency_checker.py # 整合性チェック
├── report_generator.py    # レポート生成
├── templates/             # 生成テンプレート
│   ├── schema.sql.j2
│   ├── fastapi_router.py.j2
│   └── react_component.tsx.j2
└── prompts/               # Claude プロンプト
    ├── translate_to_schema.txt
    ├── translate_to_api.txt
    └── check_consistency.txt
```

#### 4.3.3 実装例

**translator.py**:

```python
from anthropic import Anthropic

class KanaTranslator:
    """Yuno思想を具体仕様へ翻訳"""

    def __init__(self, anthropic_api_key: str):
        self.client = Anthropic(api_key=anthropic_api_key)

    async def translate_to_schema(self, yuno_doc_path: str) -> str:
        """Yuno思想ドキュメント → PostgreSQL スキーマ"""

        # Yuno ドキュメント読み込み
        with open(yuno_doc_path, 'r') as f:
            yuno_content = f.read()

        # プロンプト構築
        system_prompt = self._load_prompt('translate_to_schema.txt')

        # Claude API 呼び出し
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=8000,
            system=system_prompt,
            messages=[{
                "role": "user",
                "content": f"以下のYuno思想ドキュメントをPostgreSQLスキーマに翻訳してください:\n\n{yuno_content}"
            }]
        )

        return response.content[0].text

    async def translate_to_fastapi(self, yuno_doc_path: str) -> str:
        """Yuno思想ドキュメント → FastAPI エンドポイント"""
        # 同様の実装
        pass

    async def translate_to_react(self, yuno_doc_path: str) -> str:
        """Yuno思想ドキュメント → React コンポーネント"""
        # 同様の実装
        pass
```

**auditor.py**:

```python
class KanaAuditor:
    """設計監査機能"""

    async def audit_schema(self, schema_sql: str, yuno_doc: str) -> AuditReport:
        """生成されたスキーマをYuno思想と照合"""

        # 整合性チェック
        inconsistencies = await self._check_consistency(schema_sql, yuno_doc)

        # スコープ整合確認
        scope_issues = await self._check_scope_alignment(schema_sql, yuno_doc)

        # レポート生成
        return AuditReport(
            status='PASS' if not inconsistencies and not scope_issues else 'FAIL',
            inconsistencies=inconsistencies,
            scope_issues=scope_issues,
            recommendations=self._generate_recommendations(inconsistencies, scope_issues)
        )
```

#### 4.3.4 システムプロンプト例

**translate_to_schema.txt**:

```
あなたはKana（翻訳層）です。Yuno（思想層）の思想ドキュメントを、具体的なPostgreSQLスキーマに翻訳してください。

## 翻訳原則

1. **呼吸の一貫性**: Yunoの思想の「呼吸」を保つ
2. **スコープ整合**: L1（局所）→ L2（横断）→ L3（全体原則）の整合を確認
3. **構造認知**: 一貫した構造を維持
4. **選択肢の提示**: 複数の実装パターンを提示

## 出力形式

```sql
-- Yuno思想: [思想の要約]
-- スコープレベル: L1/L2/L3
-- 整合性確認: [確認内容]

CREATE TABLE example (
    id UUID PRIMARY KEY,
    -- ...
);
```

## 制約

- テーブル名は snake_case
- 主キーは UUID
- タイムスタンプは created_at, updated_at
- インデックスは必要最小限
```

### 4.4 受け入れ基準（Definition of Done）

- [ ] Kana 翻訳エンジン実装完了
- [ ] テストカバレッジ > 80%
- [ ] 10個のYuno思想ドキュメント翻訳成功
- [ ] 整合性チェック精度 > 95%
- [ ] ドキュメント完成
- [ ] Yuno レビュー承認

---

## 5. Claude API 統合検証仕様

### 5.1 概要

**目的**: Backend → Claude API の実装検証と最適化

**期間**: 3日
**担当**: Tsumu（具現化層）
**レビュー**: Kana（翻訳層）

### 5.2 要件定義

#### 5.2.1 機能要件

**FR-C.1: Backend → Claude API 統合**
- Intent 処理時に Claude API 呼び出し
- Prompt 最適化
- レスポンス解析
- エラーハンドリング

**FR-C.2: Token 使用量追跡**
- API 呼び出し毎のトークン数記録
- 月間トークン使用量集計
- コスト見積もり

**FR-C.3: キャッシング戦略**
- 同一Prompt のレスポンスキャッシュ（15分）
- キャッシュヒット率計測

#### 5.2.2 非機能要件

**NFR-C.1: パフォーマンス**
- API レスポンスタイム < 3秒
- キャッシュヒット率 > 30%

**NFR-C.2: コスト**
- 月間トークン使用量 < 500,000 tokens
- 月間コスト < $50

### 5.3 技術仕様

#### 5.3.1 実装場所

**既存モジュール拡張**: `bridge/providers/ai/claude_bridge.py`

```python
from anthropic import Anthropic
import json

class ClaudeBridge(AIBridge):
    """Claude API 統合実装"""

    async def process_intent(self, intent: Intent) -> str:
        """Intent を Claude で処理"""

        # Prompt 構築
        prompt = self._build_prompt(intent)

        # キャッシュ確認
        cached_response = await self._check_cache(prompt)
        if cached_response:
            self.metrics['cache_hits'] += 1
            return cached_response

        # Claude API 呼び出し
        response = self.client.messages.create(
            model="claude-sonnet-4-5-20250929",
            max_tokens=4096,
            system="あなたはResonant Engineの思考支援AIです。",
            messages=[{"role": "user", "content": prompt}]
        )

        # トークン使用量記録
        await self._record_token_usage(
            prompt_tokens=response.usage.input_tokens,
            completion_tokens=response.usage.output_tokens
        )

        # レスポンスキャッシュ
        result = response.content[0].text
        await self._cache_response(prompt, result, ttl=900)  # 15分

        return result

    def _build_prompt(self, intent: Intent) -> str:
        """Intent から Prompt 構築"""
        return f"""
Intent ID: {intent.id}
Description: {intent.description}
Priority: {intent.priority}

このIntentを処理して、具体的な実装提案を生成してください。
"""

    async def _record_token_usage(self, prompt_tokens: int, completion_tokens: int):
        """トークン使用量をDBに記録"""
        await self.db.execute(
            """
            INSERT INTO token_usage (timestamp, prompt_tokens, completion_tokens, total_cost)
            VALUES (NOW(), $1, $2, $3)
            """,
            prompt_tokens,
            completion_tokens,
            (prompt_tokens * 0.003 + completion_tokens * 0.015) / 1000  # コスト計算
        )
```

#### 5.3.2 テストケース

**テストファイル**: `tests/integration/test_claude_api.py`

```python
async def test_claude_api_integration():
    """Claude API 統合テスト"""
    intent = Intent(
        id=uuid4(),
        description="テスト用Intent",
        priority=3
    )

    bridge = ClaudeBridge(api_key=os.getenv('ANTHROPIC_API_KEY'))
    result = await bridge.process_intent(intent)

    assert result is not None
    assert len(result) > 0

async def test_token_usage_tracking():
    """トークン使用量追跡テスト"""
    bridge = ClaudeBridge(api_key=os.getenv('ANTHROPIC_API_KEY'))

    # API 呼び出し
    await bridge.process_intent(create_test_intent())

    # トークン使用量確認
    usage = await bridge.db.fetchrow("SELECT * FROM token_usage ORDER BY timestamp DESC LIMIT 1")
    assert usage['prompt_tokens'] > 0
    assert usage['completion_tokens'] > 0
    assert usage['total_cost'] > 0
```

### 5.4 受け入れ基準（Definition of Done）

- [ ] Claude API 統合実装完了
- [ ] テストカバレッジ > 80%
- [ ] トークン使用量追跡確認
- [ ] キャッシング動作確認
- [ ] コスト見積もり完成
- [ ] ドキュメント完成

---

## 6. 開発プロセス

### 6.1 スプリント構成

| Sprint | 期間 | 内容 |
|--------|-----|------|
| Sprint 2 完成 | 3日 | 並行制御テスト完成 |
| Sprint 2 ドキュメント | 2日 | ロック戦略ドキュメント |
| Sprint 5 準備 | 1週間 | Oracle Cloud セットアップ |
| Claude API 検証 | 3日 | API統合検証 |
| Kana 実装 Phase 1 | 2週間 | 翻訳エンジン実装 |

### 6.2 レビュープロセス

1. **実装**: Tsumu（Cursor）
2. **レビュー**: Kana（Claude Sonnet 4.5）
3. **監督**: Yuno（思想層）
4. **承認**: 加藤宏啓

### 6.3 テスト戦略

- ユニットテスト（pytest）
- 統合テスト（Docker環境）
- パフォーマンステスト（GitHub Actions）
- 受け入れテスト（手動）

---

## 7. リスク管理

### 7.1 リスク一覧

| リスク | 確率 | 影響 | 対策 |
|-------|-----|-----|------|
| デッドロック未解決 | 中 | 中 | テスト強化 |
| Oracle Cloud 習熟度 | 低 | 中 | ドキュメント充実 |
| Claude API Cost | 中 | 低 | トークン監視 |
| Yuno 実装困難 | 中 | 高 | フェーズ分割 |

### 7.2 対応策

- 週次進捗確認
- ブロッカー即座対応
- ドキュメント充実
- テストカバレッジ維持

---

## 8. 成功指標

| 指標 | 現状 | 目標 | 期限 |
|-----|-----|-----|------|
| テストカバレッジ | 87% | 90%+ | 2週間 |
| 受け入れテスト | 30/30 | 50/50 | 1ヶ月 |
| Sprint 完成 | 1-4 | 1-5 | 3週間 |
| 本番デプロイ | ローカル | Oracle Cloud | 3週間 |
| Kana 実装 | 0% | 50% | 1ヶ月 |

---

## 9. 付録

### 9.1 参考ドキュメント

- `docs/02_components/postgresql_dashboard/sprint/`
- `docs/02_components/bridge_lite/architecture/`
- `docs/07_philosophy/yuno_documents/`
- `docs/reports/postgresql_dashboard_acceptance_test_report.md`

### 9.2 用語集

- **Yuno**: 思想層（哲学・規範形成）
- **Kana**: 翻訳層（思想→実装への翻訳）
- **Tsumu**: 具現化層（コード生成・実装）
- **ERF**: Emotion Resonance Filter
- **Crisis Index**: 危機指数
- **Intent**: 開発意図

---

**仕様書バージョン**: v2.0
**最終更新**: 2025年11月18日
**承認**: 加藤宏啓（Hiroaki Kato）
