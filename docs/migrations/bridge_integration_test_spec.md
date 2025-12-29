# Bridge統合移行テスト仕様書

**作成日**: 2025-12-29  
**作成者**: Kana (Claude Opus 4.5)  
**実行者**: Kiro (Claude Sonnet 4.5)  
**関連文書**: `bridge_integration_migration_spec.md`

---

## 1. テスト概要

### 1.1 目的

`bridge/`から`backend/app/`への移行が正しく行われたことを検証する。

### 1.2 テスト環境

| 項目 | 値 |
|------|-----|
| OS | macOS |
| Python | 3.11+ |
| Docker | Docker Desktop |
| DB | PostgreSQL 15 (pgvector) |
| プロジェクトパス | `/Users/zero/Projects/resonant-engine` |

### 1.3 前提条件

- Docker環境が起動している
- 移行前の状態でテストがパスしている
- `.env`ファイルが正しく設定されている

---

## 2. テストカテゴリ

| カテゴリ | 説明 | 優先度 |
|---------|------|--------|
| スモークテスト | 基本的な動作確認 | 必須 |
| APIテスト | 全エンドポイントの動作確認 | 必須 |
| インポートテスト | モジュールのインポート確認 | 必須 |
| 統合テスト | 機能間連携の確認 | 重要 |
| 回帰テスト | 既存テストの実行 | 重要 |

---

## 3. フェーズ別テスト仕様

### 3.1 フェーズ1: 準備（ディレクトリ作成）

#### テスト1.1: ディレクトリ構造確認

**目的**: 必要なディレクトリが作成されていること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine

# ディレクトリ存在確認
ls -la backend/app/services/
ls -la backend/app/services/intent/
ls -la backend/app/services/memory/
ls -la backend/app/services/contradiction/
ls -la backend/app/services/semantic/
ls -la backend/app/services/realtime/
ls -la backend/app/services/dashboard/
ls -la backend/app/services/shared/
ls -la backend/app/integrations/
```

**期待結果**:
- 全てのディレクトリが存在する
- 各ディレクトリに`__init__.py`が存在する

**成功基準**: 全ディレクトリが存在し、`__init__.py`がある

---

### 3.2 フェーズ2: 共通モジュール移行

#### テスト2.1: sharedモジュールインポート確認

**目的**: 共通モジュールが正しくインポートできること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate

python -c "
from app.services.shared.constants import IntentStatusEnum, PhilosophicalActor
from app.services.shared.exceptions import DiffValidationError, InvalidStatusError
from app.services.shared.errors import ConcurrencyConflictError
print('✅ shared imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ shared imports successful`が表示される

#### テスト2.2: integrationsモジュールインポート確認

**目的**: 外部連携モジュールが正しくインポートできること

**手順**:
```bash
python -c "
from app.integrations.claude import ClaudeClient
from app.integrations.openai import OpenAIClient
from app.integrations.audit_logger import AuditLogger
print('✅ integrations imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ integrations imports successful`が表示される

#### テスト2.3: API動作確認（スモークテスト）

**目的**: 移行後もAPIが動作すること

**手順**:
```bash
curl -s http://localhost:8000/health | jq .
```

**期待結果**:
```json
{
  "status": "healthy",
  "database": "connected"
}
```

**成功基準**: statusがhealthyであること

---

### 3.3 フェーズ3: サービス移行

#### テスト3.1: contradictionサービスインポート確認

**目的**: 矛盾検出サービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.contradiction.detector import ContradictionDetector
from app.services.contradiction.models import ContradictionType, Severity
detector = ContradictionDetector()
print(f'✅ ContradictionDetector created: {detector}')
"
```

**期待結果**: ContradictionDetectorインスタンスが作成される

**成功基準**: エラーなしでインスタンス作成

#### テスト3.2: contradiction API動作確認

**目的**: 矛盾検出APIが動作すること

**手順**:
```bash
# 未解決の矛盾を取得
curl -s "http://localhost:8000/api/v1/contradiction/pending?user_id=test_user" | jq .

# 矛盾チェック
curl -s -X POST http://localhost:8000/api/v1/contradiction/check \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "test_user",
    "new_intent": {
      "intent_id": "test-001",
      "intent_type": "FEATURE_REQUEST",
      "content": "Use SQLite for database",
      "tech_stack": ["SQLite"]
    }
  }' | jq .
```

**期待結果**: 
- 200 OKレスポンス
- JSONレスポンスが返る

**成功基準**: HTTPステータス200、有効なJSON

#### テスト3.3: memoryサービスインポート確認

**目的**: メモリサービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.memory.service import MemoryService
from app.services.memory.repositories import ChoicePointRepository
from app.services.memory.choice_engine import ChoiceQueryEngine
print('✅ memory imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ memory imports successful`が表示される

#### テスト3.4: memory API動作確認

**目的**: メモリ関連APIが動作すること

**手順**:
```bash
# Choice Points取得
curl -s "http://localhost:8000/api/choice-points?user_id=test_user" | jq .

# Memory Lifecycle状態取得
curl -s "http://localhost:8000/api/v1/memory/lifecycle/status?user_id=test_user" | jq .
```

**期待結果**: 200 OKレスポンス

**成功基準**: HTTPステータス200

#### テスト3.5: semanticサービスインポート確認

**目的**: セマンティックサービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.semantic.extractor import SemanticExtractor
from app.services.semantic.inferencer import SemanticInferencer
from app.services.semantic.constructor import SemanticConstructor
print('✅ semantic imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ semantic imports successful`が表示される

#### テスト3.6: realtimeサービスインポート確認

**目的**: リアルタイムサービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.realtime.event_distributor import EventDistributor
from app.services.realtime.websocket_manager import WebSocketManager
print('✅ realtime imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ realtime imports successful`が表示される

#### テスト3.7: dashboardサービスインポート確認

**目的**: ダッシュボードサービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.dashboard.service import DashboardService
from app.services.dashboard.repository import PostgresDashboardRepository
print('✅ dashboard imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ dashboard imports successful`が表示される

#### テスト3.8: intentサービスインポート確認

**目的**: Intentサービスが正しくインポートできること

**手順**:
```bash
python -c "
from app.services.intent.bridge_set import BridgeSet
from app.services.intent.reeval import ReEvalClient
from app.services.intent.ai_bridge import AIBridge
from app.services.intent.data_bridge import DataBridge
from app.services.intent.feedback_bridge import FeedbackBridge
print('✅ intent imports successful')
"
```

**期待結果**: エラーなしで出力される

**成功基準**: `✅ intent imports successful`が表示される

#### テスト3.9: 全API動作確認

**目的**: 全APIエンドポイントが動作すること

**手順**:
```bash
#!/bin/bash
# test_all_apis.sh

BASE_URL="http://localhost:8000"

endpoints=(
  "GET /health"
  "GET /api/messages"
  "GET /api/intents"
  "GET /api/specifications"
  "GET /api/notifications"
  "GET /api/v1/contradiction/pending?user_id=test"
  "GET /api/choice-points?user_id=test"
  "GET /api/v1/memory/lifecycle/status?user_id=test"
  "GET /api/v1/dashboard/overview"
)

for endpoint in "${endpoints[@]}"; do
  method=$(echo $endpoint | cut -d' ' -f1)
  path=$(echo $endpoint | cut -d' ' -f2)
  
  status=$(curl -s -o /dev/null -w "%{http_code}" -X $method "${BASE_URL}${path}")
  
  if [ "$status" -eq 200 ]; then
    echo "✅ $method $path → $status"
  else
    echo "❌ $method $path → $status"
  fi
done
```

**期待結果**: 全エンドポイントが200を返す

**成功基準**: 全て✅が表示される

---

### 3.4 フェーズ4: Factory削除とDI移行

#### テスト4.1: dependenciesインポート確認

**目的**: DI設定が正しく動作すること

**手順**:
```bash
python -c "
from app.dependencies import (
    get_contradiction_detector,
    get_dashboard_service,
    get_claude_client,
    get_audit_logger
)
detector = get_contradiction_detector()
print(f'✅ DI working: {type(detector).__name__}')
"
```

**期待結果**: DetectorインスタンスがDI経由で取得できる

**成功基準**: エラーなしでインスタンス取得

#### テスト4.2: BridgeFactory参照がないこと

**目的**: BridgeFactoryへの参照が残っていないこと

**手順**:
```bash
grep -r "BridgeFactory" backend/app/ --include="*.py" | grep -v __pycache__ || echo "✅ No BridgeFactory references"
grep -r "bridge.factory" backend/app/ --include="*.py" | grep -v __pycache__ || echo "✅ No bridge.factory imports"
```

**期待結果**: 参照が見つからない

**成功基準**: `✅ No BridgeFactory references`が表示される

---

### 3.5 フェーズ5: 不要ファイル削除

#### テスト5.1: bridgeディレクトリが削除されていること

**目的**: `bridge/`ディレクトリが存在しないこと

**手順**:
```bash
if [ -d "/Users/zero/Projects/resonant-engine/bridge" ]; then
  echo "❌ bridge/ still exists"
else
  echo "✅ bridge/ deleted"
fi
```

**期待結果**: `✅ bridge/ deleted`が表示される

**成功基準**: bridge/ディレクトリが存在しない

#### テスト5.2: bridge参照がないこと

**目的**: コード内にbridge参照が残っていないこと

**手順**:
```bash
grep -r "from bridge" backend/app/ --include="*.py" | grep -v __pycache__ || echo "✅ No bridge imports in backend/app/"
grep -r "import bridge" backend/app/ --include="*.py" | grep -v __pycache__ || echo "✅ No bridge imports in backend/app/"
```

**期待結果**: 参照が見つからない

**成功基準**: 両方とも✅が表示される

---

### 3.6 フェーズ6: Dockerfile更新

#### テスト6.1: Dockerビルド成功

**目的**: Dockerイメージがビルドできること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose build backend --no-cache 2>&1 | tail -20
```

**期待結果**: ビルドが成功する

**成功基準**: エラーなしでビルド完了

#### テスト6.2: Dockerコンテナ起動

**目的**: コンテナが正常に起動すること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine/docker
docker compose up -d backend
sleep 10
docker ps | grep resonant_backend
docker logs resonant_backend --tail 20
```

**期待結果**: 
- コンテナがUp状態
- ログにエラーがない

**成功基準**: `resonant_backend`がUp (healthy)

#### テスト6.3: Docker環境でのAPI動作

**目的**: Docker環境でAPIが動作すること

**手順**:
```bash
curl -s http://localhost:8000/health | jq .
curl -s http://localhost:8000/api/messages | jq .
curl -s http://localhost:8000/api/intents | jq .
```

**期待結果**: 全て200 OKでJSONが返る

**成功基準**: 全APIが正常応答

---

### 3.7 フェーズ7: テスト更新

#### テスト7.1: 既存テスト実行（contradiction）

**目的**: contradiction関連のテストがパスすること

**手順**:
```bash
cd /Users/zero/Projects/resonant-engine
source venv/bin/activate
pytest tests/contradiction/ -v --tb=short 2>&1 | tail -30
```

**期待結果**: テストがパスする

**成功基準**: 80%以上のテストがパス

#### テスト7.2: 既存テスト実行（memory）

**目的**: memory関連のテストがパスすること

**手順**:
```bash
pytest tests/memory/ -v --tb=short 2>&1 | tail -30
```

**期待結果**: テストがパスする

**成功基準**: 80%以上のテストがパス

#### テスト7.3: システムテスト実行

**目的**: システムテストがパスすること

**手順**:
```bash
# Docker環境でテスト実行
docker exec resonant_dev pytest tests/system/ -v --tb=short 2>&1 | tail -50

# または、ローカルで
pytest tests/system/ -v --tb=short 2>&1 | tail -50
```

**期待結果**: テストがパスする

**成功基準**: 80%以上のテストがパス

#### テスト7.4: 全テスト実行（回帰テスト）

**目的**: 全体的なテストカバレッジを確認

**手順**:
```bash
pytest tests/ -v --tb=short -q 2>&1 | tail -50
```

**期待結果**: 大部分のテストがパス

**成功基準**: 70%以上のテストがパス（移行による影響を考慮）

---

## 4. 最終検証テスト

### 4.1 エンドツーエンドテスト

**目的**: ユーザーシナリオが動作すること

**手順**:

```bash
#!/bin/bash
# e2e_test.sh

BASE_URL="http://localhost:8000"

echo "=== E2E Test Start ==="

# 1. メッセージ作成
echo "1. Creating message..."
MSG_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/messages" \
  -H "Content-Type: application/json" \
  -d '{"user_id": "e2e_test", "content": "E2E Test Message", "message_type": "user"}')
MSG_ID=$(echo $MSG_RESPONSE | jq -r '.id')
echo "   Created message: $MSG_ID"

# 2. Intent作成
echo "2. Creating intent..."
INTENT_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/intents" \
  -H "Content-Type: application/json" \
  -d '{"intent_text": "E2E Test Intent", "intent_type": "FEATURE_REQUEST", "priority": 50}')
INTENT_ID=$(echo $INTENT_RESPONSE | jq -r '.id')
echo "   Created intent: $INTENT_ID"

# 3. 矛盾チェック
echo "3. Checking contradiction..."
CONTRA_RESPONSE=$(curl -s -X POST "${BASE_URL}/api/v1/contradiction/check" \
  -H "Content-Type: application/json" \
  -d '{
    "user_id": "e2e_test",
    "new_intent": {
      "intent_id": "e2e-test-001",
      "intent_type": "FEATURE_REQUEST",
      "content": "Use PostgreSQL",
      "tech_stack": ["PostgreSQL"]
    }
  }')
echo "   Contradiction check: $(echo $CONTRA_RESPONSE | jq -r '.contradictions | length') found"

# 4. メッセージ一覧取得
echo "4. Fetching messages..."
MSG_LIST=$(curl -s "${BASE_URL}/api/messages")
MSG_COUNT=$(echo $MSG_LIST | jq -r '.total')
echo "   Total messages: $MSG_COUNT"

# 5. Intent一覧取得
echo "5. Fetching intents..."
INTENT_LIST=$(curl -s "${BASE_URL}/api/intents")
INTENT_COUNT=$(echo $INTENT_LIST | jq -r '.total')
echo "   Total intents: $INTENT_COUNT"

echo "=== E2E Test Complete ==="
```

**期待結果**: 全ステップが成功する

**成功基準**: エラーなしで完了

### 4.2 フロントエンド動作確認

**目的**: ブラウザからの操作が正常に動作すること

**手順**:
1. http://localhost:3000 にアクセス
2. メッセージページでメッセージが表示されること
3. Intentページでインテントが表示されること
4. 矛盾検出ページが表示されること

**期待結果**: 全ページが正常に表示される

**成功基準**: 
- メッセージが表示される
- Intentが表示される
- エラーが表示されない

---

## 5. テスト結果記録テンプレート

```markdown
# Bridge統合移行テスト結果

**実行日**: YYYY-MM-DD
**実行者**: Kiro

## フェーズ1: 準備
| テスト | 結果 | 備考 |
|--------|------|------|
| 1.1 ディレクトリ構造確認 | ✅/❌ | |

## フェーズ2: 共通モジュール移行
| テスト | 結果 | 備考 |
|--------|------|------|
| 2.1 sharedインポート | ✅/❌ | |
| 2.2 integrationsインポート | ✅/❌ | |
| 2.3 APIスモークテスト | ✅/❌ | |

## フェーズ3: サービス移行
| テスト | 結果 | 備考 |
|--------|------|------|
| 3.1 contradictionインポート | ✅/❌ | |
| 3.2 contradiction API | ✅/❌ | |
| 3.3 memoryインポート | ✅/❌ | |
| 3.4 memory API | ✅/❌ | |
| 3.5 semanticインポート | ✅/❌ | |
| 3.6 realtimeインポート | ✅/❌ | |
| 3.7 dashboardインポート | ✅/❌ | |
| 3.8 intentインポート | ✅/❌ | |
| 3.9 全API動作確認 | ✅/❌ | |

## フェーズ4: Factory削除
| テスト | 結果 | 備考 |
|--------|------|------|
| 4.1 DIインポート | ✅/❌ | |
| 4.2 BridgeFactory参照なし | ✅/❌ | |

## フェーズ5: 不要ファイル削除
| テスト | 結果 | 備考 |
|--------|------|------|
| 5.1 bridge/削除確認 | ✅/❌ | |
| 5.2 bridge参照なし | ✅/❌ | |

## フェーズ6: Dockerfile更新
| テスト | 結果 | 備考 |
|--------|------|------|
| 6.1 Dockerビルド | ✅/❌ | |
| 6.2 コンテナ起動 | ✅/❌ | |
| 6.3 Docker API動作 | ✅/❌ | |

## フェーズ7: テスト更新
| テスト | 結果 | 備考 |
|--------|------|------|
| 7.1 contradictionテスト | ✅/❌ | X/Y passed |
| 7.2 memoryテスト | ✅/❌ | X/Y passed |
| 7.3 システムテスト | ✅/❌ | X/Y passed |
| 7.4 全テスト | ✅/❌ | X/Y passed |

## 最終検証
| テスト | 結果 | 備考 |
|--------|------|------|
| E2Eテスト | ✅/❌ | |
| フロントエンド確認 | ✅/❌ | |

## 総合結果
- **成功**: X/Y テスト
- **失敗**: X テスト
- **判定**: 合格/不合格
```

---

## 6. トラブルシューティング

### 6.1 インポートエラー

**症状**: `ModuleNotFoundError: No module named 'app.services.xxx'`

**対処**:
1. `__init__.py`が存在するか確認
2. PYTHONPATHを確認: `export PYTHONPATH=/Users/zero/Projects/resonant-engine/backend:$PYTHONPATH`
3. venvがアクティベートされているか確認

### 6.2 循環インポート

**症状**: `ImportError: cannot import name 'XXX' from partially initialized module`

**対処**:
1. 遅延インポートを使用（関数内でimport）
2. TYPE_CHECKINGを使用:
   ```python
   from typing import TYPE_CHECKING
   if TYPE_CHECKING:
       from app.services.xxx import YYY
   ```

### 6.3 APIエラー

**症状**: `500 Internal Server Error`

**対処**:
1. ログ確認: `docker logs resonant_backend --tail 50`
2. インポートパスを確認
3. 依存関係を確認

### 6.4 Dockerビルドエラー

**症状**: `COPY failed: file not found`

**対処**:
1. Dockerfileのパスを確認
2. docker-compose.ymlのcontextを確認
3. .dockerignoreを確認

---

## 7. 成功基準サマリー

| フェーズ | 必須条件 |
|---------|---------|
| フェーズ1 | 全ディレクトリが存在 |
| フェーズ2 | shared, integrations インポート成功 |
| フェーズ3 | 全サービスインポート成功、全API 200 OK |
| フェーズ4 | DI動作、BridgeFactory参照なし |
| フェーズ5 | bridge/削除、参照なし |
| フェーズ6 | Dockerビルド・起動成功 |
| フェーズ7 | テスト80%以上パス |
| **最終** | E2E成功、フロントエンド動作 |

---

**テスト仕様書作成完了**

この仕様書に従ってKiroがテストを実行してください。
