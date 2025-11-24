# Resonant Engine 使い方ガイド（2025年版）

**最終更新**: 2025-11-24  
**対象バージョン**: Resonant Engine v1.1+  
**対象者**: 開発者・システム利用者

---

## 🚨 重要な注意事項

### 1. 古い情報に注意

**Claude Codeが示した古い使い方（CLIツール中心）は現在非推奨です。**

Resonant Engineは、初期のCLIツール群から**本格的なマイクロサービスアーキテクチャ**に進化しました。

### 2. 開発環境と本番環境の違い

**開発環境（`start-dev.sh`）**:
- ✅ テスト実行・開発用
- ❌ **UIなし（ブラウザアクセス不可）**
- 用途: バックエンド開発、テスト実行

**本番環境（`docker-compose.yml`）**:
- ✅ UI付き（ブラウザアクセス可能）
- ⚠️ **Sprint 1-2時点の機能のみ**
- 用途: UI確認、デモ

詳細は [`CURRENT_STATUS.md`](./CURRENT_STATUS.md) を参照してください。

---

## 📋 目次

1. [Resonant Engineとは](#resonant-engineとは)
2. [環境の選択](#環境の選択)
3. [開発環境の使い方](#開発環境の使い方)
4. [本番環境の使い方](#本番環境の使い方)
5. [基本的な使い方](#基本的な使い方)
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

## 環境の選択

### どちらを使うべきか？

| 目的 | 推奨環境 | 理由 |
|-----|---------|------|
| システムを理解したい | 開発環境 | テストを実行しながら学べる |
| コードを開発したい | 開発環境 | 高速な開発サイクル |
| UIを確認したい | 本番環境 | ブラウザでアクセス可能 |
| デモを見せたい | 本番環境 | 視覚的に分かりやすい |

### 環境比較表

| 項目 | 開発環境 | 本番環境 |
|-----|---------|---------|
| **起動コマンド** | `./docker/scripts/start-dev.sh` | `docker-compose up` |
| **起動時間** | ⚡ 30秒 | 🐢 5-10分（ビルド必要） |
| **UI** | ❌ なし | ✅ あり |
| **ブラウザアクセス** | ❌ 不可 | ✅ 可能 |
| **テスト実行** | ✅ 高速 | ⚠️ 可能だが遅い |
| **最新機能** | ✅ 全て（Sprint 1-11） | ⚠️ Sprint 1-2のみ |
| **用途** | 開発・テスト | UI確認・デモ |

---

## 開発環境の使い方

### 前提条件

- Docker Desktop インストール済み
- Git リポジトリクローン済み

### 起動手順

```bash
# 1. プロジェクトルートに移動
cd /path/to/resonant-engine

# 2. 開発環境起動
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

### ⚠️ 重要: UIはありません

開発環境では**ブラウザでアクセスできません**。以下の方法で操作します：

1. **テスト実行**: `docker exec resonant_dev pytest tests/system/ -v`
2. **データベース操作**: `docker exec resonant_postgres_dev psql -U resonant -d postgres`
3. **Pythonコード実行**: `docker exec -it resonant_dev bash`

---

## 本番環境の使い方

### 起動手順

```bash
# 1. プロジェクトルートに移動
cd /path/to/resonant-engine

# 2. 本番環境起動
cd docker
docker-compose up --build -d
```

### ブラウザでアクセス

起動後、以下のURLにアクセスできます：

| サービス | URL | 説明 |
|---------|-----|------|
| **Frontend** | http://localhost:3000 | React UI |
| **Backend API** | http://localhost:8000 | FastAPI |
| **API Docs** | http://localhost:8000/docs | Swagger UI |

### ⚠️ 重要: 古いUIです

現在のFrontendは**Sprint 1-2時点**のもので、以下の機能は未統合です：

- ❌ Memory Lifecycle（Sprint 9）
- ❌ Choice Preservation（Sprint 10）
- ❌ Contradiction Detection（Sprint 11）
- ❌ Context Assembler（Sprint 5）

**対応済みの機能**:
- ✅ Messages表示・作成
- ✅ Intents表示・作成
- ✅ Specifications表示・作成

### 停止方法

```bash
cd docker
docker-compose down
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

### Q1: `start-dev.sh`で全機能が使えるようになる？

**A: いいえ。テスト実行環境のみです。**

開発環境では：
- ✅ テスト実行
- ✅ データベース操作
- ✅ Pythonコード実行
- ❌ **ブラウザでのUIアクセス（不可）**

UIが必要な場合は、本番環境（`docker-compose up`）を起動してください。

### Q2: ブラウザでアクセスするには？

**A: 本番環境を起動してください。**

```bash
cd docker
docker-compose up --build -d
# http://localhost:3000
```

ただし、現在のFrontendは**Sprint 1-2時点**の機能のみです。

### Q3: 古いCLIツール（utils/record_intent.py等）は使えますか？

**A**: 使えますが、**非推奨**です。

現在のアーキテクチャでは、データベース直接アクセスまたはBridge Servicesの使用を推奨します。古いCLIツールはメンテナンスされていません。

### Q4: どちらの環境を使うべき？

**A**: 目的によって異なります。

- **開発・テスト**: 開発環境（`start-dev.sh`）
- **UI確認・デモ**: 本番環境（`docker-compose up`）

詳細は[環境の選択](#環境の選択)を参照してください。

### Q5: Frontendが古いのはなぜ？

**A**: 開発の優先順位のためです。

現在はバックエンド機能（Memory System, Context Assembler, Contradiction Detection等）の実装を優先しています。Frontend統合はSprint 12以降を予定しています。

### Q6: Claude API Keyはどこで設定？

**A**: `docker/.env.dev`ファイルに設定します。

```bash
ANTHROPIC_API_KEY=sk-ant-api03-your-key-here
```

### Q7: エラーが発生した場合は？

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
- [`CURRENT_STATUS.md`](./CURRENT_STATUS.md) - 現状の詳細
- `docker/README_DEV.md` - トラブルシューティング
- `docs/troubleshooting/` - 既知の問題

### Q8: 本番デプロイはできる？

**A**: 現在は開発中です。

`docker-compose.yml`は「本番環境」という名前ですが、実際は開発中のプロトタイプです。本番デプロイは今後のフェーズで実装予定です。

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

### 初めての方（システム理解）

**推奨**: 開発環境でテストを実行

```bash
# 1. 開発環境起動
./docker/scripts/start-dev.sh

# 2. テスト実行（システムの動作を確認）
docker exec resonant_dev pytest tests/system/ -v

# 3. データベース確認
docker exec resonant_postgres_dev psql -U resonant -d postgres -c "\dt"

# 4. ドキュメント読む
# - CURRENT_STATUS.md（現状理解）
# - docker/README_DEV.md（開発環境詳細）
```

### UIを見たい方

**推奨**: 本番環境を起動

```bash
# 1. 本番環境起動（5-10分かかります）
cd docker
docker-compose up --build -d

# 2. ブラウザでアクセス
# Frontend: http://localhost:3000
# API Docs: http://localhost:8000/docs

# 注意: Sprint 1-2時点の機能のみです
```

### 開発者の方

**推奨**: 開発環境 + ドキュメント熟読

```bash
# 1. 開発環境起動
./docker/scripts/start-dev.sh

# 2. 必読ドキュメント
# - docker/README_DEV.md
# - docs/test_specs/system_test_specification_20251123.md
# - docs/reports/system_test_v3.7_complete_success_report_20251124.md

# 3. テストコードを読む
# tests/system/
# tests/contradiction/

# 4. 実装を確認
# bridge/
# memory_store/
# context_assembler/
```

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
| 2025-11-24 | 1.1.0 | 開発環境と本番環境の違いを明確化、UIアクセス方法を追記 |
| 2025-11-24 | 1.0.0 | 初版作成（古いCLI中心の説明を刷新） |

---

**作成者**: Kiro AI Assistant  
**レビュー**: 必要に応じて更新  
**次回更新予定**: Sprint 12完了時

---

## 🔗 クイックリンク

### 必読ドキュメント

- **[現状報告](./CURRENT_STATUS.md)** - 開発環境と本番環境の違いを詳しく説明
- **[開発環境ガイド](../../docker/README_DEV.md)** - Docker環境の詳細
- **[テスト仕様書](../test_specs/system_test_specification_20251123.md)** - 総合テストの仕様
- **[最新レポート](../reports/system_test_v3.7_complete_success_report_20251124.md)** - テスト完全成功レポート

### その他

- [プロジェクトルート](../../README.md)
- [アーキテクチャ](../output/resonant_total_architecture_yuno_hiroaki_full_2025-11-07.md)
- [Sprint別レポート](../reports/)
