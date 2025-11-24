# Resonant Engine 使い方ガイド（2025年版）

**最終更新**: 2025-11-24  
**対象バージョン**: Resonant Engine v1.1+  
**対象者**: 開発者・システム利用者

---

## 🚨 重要な注意事項

**Claude Codeが示した古い使い方（CLIツール中心）は現在非推奨です。**

Resonant Engineは、初期のCLIツール群から**本格的なマイクロサービスアーキテクチャ**に進化しました。

---

## 📋 目次

1. [Resonant Engineとは](#resonant-engineとは)
2. [現在のアーキテクチャ](#現在のアーキテクチャ)
3. [開発環境の起動](#開発環境の起動)
4. [基本的な使い方](#基本的な使い方)
5. [API経由でのアクセス](#api経由でのアクセス)
6. [テスト実行](#テスト実行)
7. [よくある質問](#よくある質問)

---

## Resonant Engineとは

Resonant Engineは、**AIがシステム開発の経過を継続的に理解し、開発を支援するための基盤**です。

### 主要機能

1. **Intent Management**: 開発意図の記録と追跡
2. **Memory System**: セマンティックメモリとライフサイクル管理
3. **Context Assembly**: AIへの最適なコンテキスト提供
4. **Contradiction Detection**: 矛盾検出と整合性維持
5. **Choice Preservation**: 意思決定履歴の保存

### アーキテクチャの進化

```
v1.0 (2024)
├─ CLIツール中心
├─ utils/record_intent.py
└─ utils/trace_events.py
    ↓
v1.1 (2025)
├─ マイクロサービスアーキテクチャ
├─ FastAPI Backend
├─ PostgreSQL + pgvector
├─ Docker Compose環境
└─ 総合テストスイート（49テスト）
```

---

## 現在のアーキテクチャ

### システム構成

```
┌─────────────────────────────────────────────────────────┐
│                    Resonant Engine                       │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐ │
│  │   Backend    │  │   Bridge     │  │   Frontend   │ │
│  │   (FastAPI)  │  │   Services   │  │   (React)    │ │
│  └──────┬───────┘  └──────┬───────┘  └──────────────┘ │
│         │                  │                            │
│         └──────────┬───────┘                            │
│                    │                                    │
│         ┌──────────▼───────────┐                       │
│         │   PostgreSQL 15      │                       │
│         │   + pgvector         │                       │
│         └──────────────────────┘                       │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 主要コンポーネント

| コンポーネント | 役割 | ポート |
|--------------|------|--------|
| **backend/** | FastAPI REST API | 8000 |
| **bridge/** | ビジネスロジック層 | - |
| **memory_store/** | メモリ管理 | - |
| **context_assembler/** | コンテキスト組み立て | - |
| **retrieval/** | 検索オーケストレーション | - |
| **PostgreSQL** | データベース | 5432 |

---

## 開発環境の起動

### 前提条件

- Docker Desktop インストール済み
- Git リポジトリクローン済み

### 起動手順

```bash
# 1. プロジェクトルートに移動
cd /path/to/resonant-engine

# 2. 開発環境起動スクリプト実行
./docker/scripts/start-dev.sh
```

または手動で：

```bash
cd docker
docker-compose -f docker-compose.dev.yml --env-file .env.dev up -d
```

### 起動確認

```bash
# コンテナ状態確認
docker ps | grep resonant

# 期待される出力:
# resonant_dev          Up (healthy)
# resonant_postgres_dev Up (healthy)
```

### ヘルスチェック

```bash
# データベース接続確認
docker exec resonant_postgres_dev pg_isready -U resonant -d postgres

# 開発コンテナ確認
docker exec resonant_dev python --version
# Python 3.11.14
```

---

## 基本的な使い方

### 1. データベース操作

#### テーブル一覧確認

```bash
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\dt"
```

**主要テーブル**:
- `messages` - メッセージ管理
- `intents` - Intent管理
- `specifications` - 仕様書管理
- `semantic_memories` - セマンティックメモリ
- `choice_points` - 選択履歴
- `contradictions` - 矛盾検出レコード

#### データ確認

```bash
# Intentの確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "
SELECT id, intent_type, status, created_at 
FROM intents 
ORDER BY created_at DESC 
LIMIT 5;
"

# メモリの確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "
SELECT id, memory_type, content, importance_score 
FROM semantic_memories 
ORDER BY created_at DESC 
LIMIT 5;
"
```

### 2. Python APIの使用

開発コンテナ内でPythonコードを実行：

```bash
# コンテナ内に入る
docker exec -it resonant_dev bash

# Pythonインタラクティブシェル
python
```

#### Intent作成例

```python
import asyncio
import asyncpg

async def create_intent():
    # データベース接続
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user='resonant',
        password='ResonantEngine2025SecurePass!',
        database='postgres'
    )
    
    # Intent作成
    intent_id = await conn.fetchval("""
        INSERT INTO intents (
            user_id, intent_type, content, status
        ) VALUES ($1, $2, $3, $4)
        RETURNING id
    """, 'user_001', 'development', 'Add user authentication', 'pending')
    
    print(f"Created Intent ID: {intent_id}")
    
    await conn.close()

# 実行
asyncio.run(create_intent())
```

#### メモリ検索例

```python
import asyncio
import asyncpg

async def search_memories():
    conn = await asyncpg.connect(
        host='postgres',
        port=5432,
        user='resonant',
        password='ResonantEngine2025SecurePass!',
        database='postgres'
    )
    
    # セマンティック検索（ベクトル類似度）
    query_embedding = [0.1] * 1536  # 実際はOpenAI APIで生成
    
    results = await conn.fetch("""
        SELECT 
            id, 
            content, 
            memory_type,
            importance_score,
            1 - (embedding <=> $1::vector) as similarity
        FROM semantic_memories
        WHERE user_id = $2
        ORDER BY embedding <=> $1::vector
        LIMIT 5
    """, str(query_embedding), 'user_001')
    
    for row in results:
        print(f"Memory: {row['content'][:50]}... (similarity: {row['similarity']:.3f})")
    
    await conn.close()

asyncio.run(search_memories())
```

### 3. Bridge Servicesの使用

```python
# KanaAIBridge（Claude API統合）
from bridge.providers.ai.kana_ai_bridge import KanaAIBridge
import asyncio

async def use_ai_bridge():
    bridge = KanaAIBridge()
    
    result = await bridge.process_intent({
        'intent_type': 'query',
        'content': 'What is the current system status?',
        'context': {}
    })
    
    print(f"AI Response: {result['response']}")

asyncio.run(use_ai_bridge())
```

---

## API経由でのアクセス

### FastAPI Backend（開発中）

現在、FastAPI Backendは実装済みですが、開発環境では直接Pythonコードまたはデータベースアクセスを推奨します。

#### API起動（オプション）

```bash
cd backend
docker-compose up --build -d
```

#### エンドポイント

- `GET /api/intents` - Intent一覧
- `POST /api/intents` - Intent作成
- `GET /api/messages` - メッセージ一覧
- `GET /api/specifications` - 仕様書一覧

#### Swagger UI

http://localhost:8000/docs

---

## テスト実行

### 総合テスト（推奨）

```bash
# 全49テスト実行
docker exec resonant_dev pytest tests/system/ -v

# 期待結果: 49 passed, 0 skipped, 0 failed
```

### カテゴリ別テスト

```bash
# データベーステスト
docker exec resonant_dev pytest tests/system/test_db_connection.py -v

# APIテスト
docker exec resonant_dev pytest tests/system/test_api.py -v

# AIブリッジテスト
docker exec resonant_dev pytest tests/system/test_ai.py -v

# メモリシステムテスト
docker exec resonant_dev pytest tests/system/test_memory.py -v

# 矛盾検出テスト
docker exec resonant_dev pytest tests/system/test_contradiction.py -v

# E2Eテスト
docker exec resonant_dev pytest tests/system/test_e2e.py -v
```

### Sprint別テスト

```bash
# Sprint 11: 矛盾検出
docker exec resonant_dev pytest tests/contradiction/ -v

# Sprint 10: Choice Preservation
docker exec resonant_dev pytest tests/memory/ -v

# Sprint 5: Context Assembler
docker exec resonant_dev pytest tests/acceptance/test_sprint5_context_assembler.py -v
```

---

## よくある質問

### Q1: 古いCLIツール（utils/record_intent.py等）は使えますか？

**A**: 使えますが、**非推奨**です。現在のアーキテクチャでは、データベース直接アクセスまたはBridge Servicesの使用を推奨します。

古いCLIツールは、初期プロトタイプの遺産として残っていますが、メンテナンスされていません。

### Q2: どのファイルから始めればいいですか？

**A**: 用途によって異なります：

- **システム理解**: `docs/01_getting_started/USAGE_GUIDE.md`（このファイル）
- **開発環境**: `docker/README_DEV.md`
- **テスト実行**: `docs/test_specs/system_test_specification_20251123.md`
- **アーキテクチャ**: `docs/output/resonant_total_architecture_yuno_hiroaki_full_2025-11-07.md`

### Q3: Frontend（React）はどこにありますか？

**A**: `frontend/`ディレクトリに存在しますが、現在は**バックエンド開発が優先**されています。

フロントエンドは、Sprint 1-2で基本実装されましたが、その後のSprint（3-11）ではバックエンド機能の拡充に注力しています。

### Q4: 本番環境へのデプロイ方法は？

**A**: 現在は**開発環境のみ**サポートしています。本番デプロイは今後のフェーズで実装予定です。

### Q5: Claude API Keyはどこで設定しますか？

**A**: `docker/.env.dev`ファイルに設定します：

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Q6: エラーが発生した場合は？

**A**: トラブルシューティング手順：

1. ログ確認
```bash
docker logs resonant_dev
docker logs resonant_postgres_dev
```

2. 環境リセット
```bash
cd docker
docker-compose -f docker-compose.dev.yml down -v
./scripts/start-dev.sh
```

3. ドキュメント参照
- `docker/README_DEV.md` - トラブルシューティングセクション
- `docs/troubleshooting/` - 既知の問題

---

## 📚 関連ドキュメント

### 必読ドキュメント

1. **開発環境**: `docker/README_DEV.md`
2. **テスト仕様**: `docs/test_specs/system_test_specification_20251123.md`
3. **アーキテクチャ**: `docs/output/resonant_total_architecture_yuno_hiroaki_full_2025-11-07.md`

### Sprint別ドキュメント

- Sprint 1-4: PostgreSQL Dashboard実装
- Sprint 5: Context Assembler
- Sprint 6: Intent Bridge
- Sprint 7-9: Memory Lifecycle
- Sprint 10: Choice Preservation
- Sprint 11: Contradiction Detection

詳細は`docs/02_components/`および`docs/reports/`を参照。

---

## 🎯 次のステップ

### 初めての方

1. ✅ 開発環境を起動
2. ✅ テストを実行して動作確認
3. ✅ データベースを確認
4. ✅ サンプルコードを実行

### 開発者の方

1. ✅ `docker/README_DEV.md`を熟読
2. ✅ テストコードを読んで理解
3. ✅ Bridge Servicesのコードを確認
4. ✅ 新機能の実装開始

### システム管理者の方

1. ✅ Docker環境の理解
2. ✅ PostgreSQLマイグレーションの確認
3. ✅ ヘルスチェックの設定
4. ✅ 監視・ログ収集の検討

---

## 🆘 サポート

問題が発生した場合：

1. このガイドの「よくある質問」を確認
2. `docker/README_DEV.md`のトラブルシューティングを確認
3. ログを確認: `docker logs resonant_dev`
4. 環境をリセット: `docker-compose down -v && ./scripts/start-dev.sh`

---

## 📝 変更履歴

| 日付 | バージョン | 変更内容 |
|------|-----------|---------|
| 2025-11-24 | 1.0.0 | 初版作成（古いCLI中心の説明を刷新） |

---

**作成者**: Kiro AI Assistant  
**レビュー**: 必要に応じて更新  
**次回更新予定**: Sprint 12完了時

---

## 🔗 クイックリンク

- [プロジェクトルート](../../README.md)
- [開発環境ガイド](../../docker/README_DEV.md)
- [テスト仕様書](../test_specs/system_test_specification_20251123.md)
- [最新レポート](../reports/system_test_v3.7_complete_success_report_20251124.md)
