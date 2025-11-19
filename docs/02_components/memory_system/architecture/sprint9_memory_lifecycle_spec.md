# Sprint 9: Memory Lifecycle Management 仕様書

## 0. CRITICAL: Memory as Living System

**⚠️ IMPORTANT: 「メモリ = 生きた記憶システム・呼吸する知識」**

Memory Lifecycle Managementは、記憶を「静的なデータ」ではなく「生きたシステム」として扱います。記憶は時間とともに変化し、重要度が変動し、やがて忘却されます。このSprintでは、メモリの「誕生→成長→衰退→忘却」というライフサイクルを実装し、データベースの肥大化を防ぎつつ重要な記憶を保持します。

```yaml
memory_lifecycle_philosophy:
    essence: "記憶 = 生きたシステム（誕生・成長・衰退・忘却）"
    purpose:
        - メモリの重要度評価と優先順位付け
        - 古いメモリの自動圧縮
        - 不要メモリの忘却機能
        - データベース容量管理
    principles:
        - "重要度は時間とともに変化する"
        - "頻繁にアクセスされる記憶は強化される"
        - "孤立した記憶は衰退する"
        - "完全な忘却ではなく圧縮保存"
```

### 呼吸サイクルとの関係

```
Memory Lifecycle (記憶の呼吸)
    ↓
誕生: 新規メモリ作成（importance_score = 0.5）
    ↓
成長: アクセス・参照による強化（score += 0.1）
    ↓
衰退: 時間経過による減衰（score *= 0.95/week）
    ↓
圧縮: 低重要度メモリの要約化（score < 0.3）
    ↓
忘却: 圧縮後さらに放置（archive or delete）
```

### Done Definition (Tier制)

#### Tier 1: 必須要件
- [ ] Memory Importance Scoring実装（時間減衰・アクセス強化）
- [ ] Memory Compression機能実装（Claude Haikuによる要約）
- [ ] Memory Archive機能実装（低重要度メモリの保管）
- [ ] 容量管理機能実装（上限チェック・自動圧縮トリガー）
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

#### Tier 2: 品質要件
- [ ] 重要度スコア計算が適切（減衰率・強化率）
- [ ] 圧縮率 > 70%（元サイズに対して）
- [ ] 圧縮レイテンシ < 2秒/メモリ
- [ ] 容量上限到達時の自動処理が動作
- [ ] Observability: `memory_compression_rate`, `memory_archive_count`

---

## 1. 概要

### 1.1 目的
メモリシステムに「ライフサイクル管理」機能を実装し、長期運用時のデータベース肥大化を防ぎつつ、重要な記憶を保持する。

### 1.2 背景

**Sprint 8までの成果:**
- Sprint 5: Context Assembler実装（3層記憶統合）
- Sprint 6: Intent Bridge統合完了
- Sprint 7: Session Summary自動生成完了
- Sprint 8: User Profile & Persistent Context完了

**現状の問題:**
- メモリは永続的に蓄積され、削除されない
- データベースが無限に肥大化する
- 古い・無関係なメモリも平等に扱われる
- 重要度の概念がない
- ストレージコストが増大

**長期運用シミュレーション（1年）:**
```
1日10メッセージ × 365日 = 3,650メッセージ
1メッセージ = 平均500文字 = 1KB
→ 3,650KB = 約3.6MB/年（メッセージのみ）

Semantic Memory（pgvector embedding）:
1 embedding = 1536次元 × 4 bytes = 6KB
3,650 embeddings × 6KB = 約21.9MB/年

合計: 約25MB/年（1ユーザー）
10ユーザー × 5年 = 1.25GB
```

### 1.3 目標
- メモリ重要度スコアリング機能実装
- 時間減衰・アクセス強化アルゴリズム実装
- 低重要度メモリの自動圧縮機能
- アーカイブ・忘却機能
- 容量管理と自動トリガー

### 1.4 スコープ

**含む:**
- Memory Importance Scoring（重要度計算）
- Time Decay（時間減衰）
- Access Boost（アクセス強化）
- Memory Compression（Claude Haikuによる要約）
- Memory Archive（低重要度メモリ保管）
- Capacity Management（容量上限管理）

**含まない（将来拡張）:**
- AI判定による重要度評価（現状はルールベース）
- ユーザーフィードバック統合
- マルチテナント対応

---

## 2. ユースケース

### 2.1 時間経過によるメモリ減衰

**シナリオ:**
1ヶ月前の「明日の天気」に関する会話は、現在では重要度が低い。

**Before（Sprint 8）:**
```sql
SELECT * FROM semantic_memories
WHERE user_id = 'hiroki'
ORDER BY created_at DESC;

-- 結果: 1ヶ月前の「明日の天気」も最新の「Sprint実装」と同等に扱われる
```

**After（Sprint 9）:**
```sql
SELECT *, importance_score FROM semantic_memories
WHERE user_id = 'hiroki'
ORDER BY importance_score DESC;

-- 結果:
-- Sprint実装（昨日）: score = 0.9（高重要度）
-- 天気の話（1ヶ月前）: score = 0.15（低重要度、圧縮対象）
```

### 2.2 頻繁にアクセスされるメモリの強化

**シナリオ:**
「Resonant Engineの哲学」は繰り返し参照されるため、重要度が上がる。

**アクセスログ:**
```
Day 1: "Resonant Engineとは？" → Semantic Memory参照
        → importance_score: 0.5 → 0.6 (boost +0.1)

Day 3: "呼吸優先原則を説明して" → 同メモリ参照
        → importance_score: 0.6 → 0.7 (boost +0.1)

Day 7: "Resonant Ethicsは？" → 同メモリ参照
        → importance_score: 0.7 → 0.8 (boost +0.1)

→ 頻繁にアクセスされるメモリは重要度が上昇
```

### 2.3 低重要度メモリの自動圧縮

**シナリオ:**
6ヶ月前の「ランチの場所」に関する会話は圧縮される。

**Before:**
```
[semantic_memories]
content: "今日のランチは駅前のラーメン屋に行った。味噌ラーメンが美味しかった。次回は塩ラーメンを試したい。"
embedding: [1536次元ベクトル]
サイズ: 約6KB
```

**After（圧縮）:**
```
[memory_archive]
original_id: uuid-xxx
compressed_summary: "ランチ: 駅前ラーメン屋（味噌）"
original_size: 6KB
compressed_size: 0.5KB
compression_ratio: 91.7%
```

### 2.4 容量上限到達時の自動処理

**シナリオ:**
Semantic Memoriesが10,000件に達した際、自動的に低重要度メモリを圧縮。

**トリガー:**
```python
# 容量チェック
total_memories = await conn.fetchval("SELECT COUNT(*) FROM semantic_memories WHERE user_id = $1", user_id)

if total_memories > MEMORY_LIMIT:
    # 低重要度メモリを圧縮
    await memory_lifecycle.compress_low_importance_memories(
        user_id=user_id,
        threshold=0.3,
        limit=1000
    )
```

---

## 3. アーキテクチャ

### 3.1 全体構成

```
┌──────────────────────────────────────────────────────────┐
│         Memory Lifecycle Management System              │
│                                                          │
│  ┌────────────────────────────────────────────────────┐ │
│  │  Importance Scoring Engine                         │ │
│  │  - Time Decay Calculator                           │ │
│  │  - Access Boost Tracker                            │ │
│  │  - Score Aggregator                                │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Memory Compression Service                        │ │
│  │  - Claude Haiku Summarizer                         │ │
│  │  - Compression Ratio Calculator                    │ │
│  │  - Batch Processor                                 │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Memory Archive Manager                            │ │
│  │  - Archive Storage                                 │ │
│  │  - Retention Policy                                │ │
│  │  - Restore Functionality                           │ │
│  └──────────────┬─────────────────────────────────────┘ │
│                 │                                        │
│  ┌──────────────▼─────────────────────────────────────┐ │
│  │  Capacity Manager                                  │ │
│  │  - Usage Monitor                                   │ │
│  │  - Auto-trigger Logic                              │ │
│  │  - Cleanup Scheduler                               │ │
│  └────────────────────────────────────────────────────┘ │
└──────────────────────────────────────────────────────────┘
          ↓                    ↑
    [PostgreSQL]          [Scheduled Jobs]
    - semantic_memories
    - memory_archive
    - memory_lifecycle_log
```

### 3.2 データフロー

```
[New Memory Created]
    ↓
1. Importance Scoring
   ├─ Initial Score = 0.5
   ├─ Time Decay適用（毎週-5%）
   └─ Access Boost適用（参照時+10%）
    ↓
2. Lifecycle Check（毎日実行）
   ├─ Score < 0.3 → 圧縮対象
   ├─ Score >= 0.3 → 保持
   └─ Archive期限超過 → 削除対象
    ↓
3. Compression（対象メモリ）
   ├─ Claude Haiku呼び出し
   ├─ Summary生成
   ├─ Archiveテーブルへ移動
   └─ 元メモリ削除
    ↓
4. Capacity Check
   ├─ Total < Limit → OK
   └─ Total >= Limit → Auto-compress
```

---

## 4. データモデル

### 4.1 semantic_memories テーブル拡張

**追加カラム:**

```sql
ALTER TABLE semantic_memories
ADD COLUMN importance_score FLOAT DEFAULT 0.5,
ADD COLUMN last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN access_count INTEGER DEFAULT 0,
ADD COLUMN decay_applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

CREATE INDEX idx_semantic_memories_importance ON semantic_memories(importance_score DESC);
CREATE INDEX idx_semantic_memories_decay ON semantic_memories(decay_applied_at);
```

### 4.2 memory_archive テーブル（新規）

**テーブル定義:**

```sql
CREATE TABLE memory_archive (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    
    -- 元メモリ情報
    original_memory_id UUID NOT NULL,
    original_content TEXT NOT NULL,
    original_embedding VECTOR(1536),
    
    -- 圧縮情報
    compressed_summary TEXT NOT NULL,
    compression_method VARCHAR(50) DEFAULT 'claude_haiku',
    compressed_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    
    -- サイズ情報
    original_size_bytes INTEGER,
    compressed_size_bytes INTEGER,
    compression_ratio FLOAT,
    
    -- スコア情報
    final_importance_score FLOAT,
    
    -- メタデータ
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    archive_reason VARCHAR(100),  -- 'low_importance', 'capacity_limit', 'manual'
    
    -- 保持期限
    retention_until TIMESTAMP WITH TIME ZONE  -- NULLなら無期限
);

CREATE INDEX idx_memory_archive_user_id ON memory_archive(user_id);
CREATE INDEX idx_memory_archive_original_id ON memory_archive(original_memory_id);
CREATE INDEX idx_memory_archive_retention ON memory_archive(retention_until);
```

### 4.3 memory_lifecycle_log テーブル（新規）

**テーブル定義:**

```sql
CREATE TABLE memory_lifecycle_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory_id UUID NOT NULL,
    
    -- イベント情報
    event_type VARCHAR(50) NOT NULL,  -- 'score_update', 'compress', 'archive', 'delete'
    event_details JSONB,
    
    -- スコア変動
    score_before FLOAT,
    score_after FLOAT,
    
    -- タイムスタンプ
    event_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_memory_lifecycle_log_user ON memory_lifecycle_log(user_id);
CREATE INDEX idx_memory_lifecycle_log_memory ON memory_lifecycle_log(memory_id);
CREATE INDEX idx_memory_lifecycle_log_event ON memory_lifecycle_log(event_type);
CREATE INDEX idx_memory_lifecycle_log_time ON memory_lifecycle_log(event_at);
```

---

## 5. コンポーネント設計

### 5.1 Importance Scoring Engine

**ファイル:** `memory_lifecycle/importance_scorer.py`

**重要度計算式:**

```
importance_score = base_score × time_decay_factor × access_boost_factor

time_decay_factor = 0.95 ^ weeks_since_creation
access_boost_factor = 1 + (access_count × 0.1)
```

**実装:**

```python
from datetime import datetime, timedelta
from typing import Optional
import asyncpg

class ImportanceScorer:
    """メモリ重要度スコアリング"""
    
    DECAY_RATE = 0.95  # 週ごとに5%減衰
    BOOST_PER_ACCESS = 0.1  # アクセスごとに+10%
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    async def calculate_score(
        self,
        memory_id: str,
        created_at: datetime,
        last_accessed_at: Optional[datetime],
        access_count: int
    ) -> float:
        """
        重要度スコア計算
        
        Args:
            memory_id: メモリID
            created_at: 作成日時
            last_accessed_at: 最終アクセス日時
            access_count: アクセス回数
            
        Returns:
            float: 重要度スコア（0.0 - 1.0）
        """
        # 基本スコア
        base_score = 0.5
        
        # 時間減衰
        weeks_elapsed = (datetime.utcnow() - created_at).days / 7
        time_decay_factor = self.DECAY_RATE ** weeks_elapsed
        
        # アクセス強化
        access_boost_factor = 1 + (access_count * self.BOOST_PER_ACCESS)
        
        # 最終スコア
        score = base_score * time_decay_factor * access_boost_factor
        
        # 0-1の範囲にクリップ
        return max(0.0, min(1.0, score))
    
    async def update_all_scores(self, user_id: str):
        """
        全メモリのスコアを再計算・更新
        
        Args:
            user_id: ユーザーID
        """
        async with self.pool.acquire() as conn:
            memories = await conn.fetch("""
                SELECT id, created_at, last_accessed_at, access_count
                FROM semantic_memories
                WHERE user_id = $1
            """, user_id)
            
            for memory in memories:
                new_score = await self.calculate_score(
                    memory_id=str(memory['id']),
                    created_at=memory['created_at'],
                    last_accessed_at=memory['last_accessed_at'],
                    access_count=memory['access_count']
                )
                
                # スコア更新
                await conn.execute("""
                    UPDATE semantic_memories
                    SET importance_score = $1,
                        decay_applied_at = NOW()
                    WHERE id = $2
                """, new_score, memory['id'])
    
    async def boost_on_access(self, memory_id: str):
        """
        アクセス時のスコア強化
        
        Args:
            memory_id: メモリID
        """
        async with self.pool.acquire() as conn:
            await conn.execute("""
                UPDATE semantic_memories
                SET access_count = access_count + 1,
                    last_accessed_at = NOW(),
                    importance_score = LEAST(1.0, importance_score + $1)
                WHERE id = $2
            """, self.BOOST_PER_ACCESS, memory_id)
```

### 5.2 Memory Compression Service

**ファイル:** `memory_lifecycle/compression_service.py`

```python
import asyncpg
from typing import List, Dict, Any
import anthropic
import logging

logger = logging.getLogger(__name__)

class MemoryCompressionService:
    """メモリ圧縮サービス"""
    
    def __init__(self, pool: asyncpg.Pool, anthropic_api_key: str):
        self.pool = pool
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
    
    async def compress_memory(self, memory_id: str) -> Dict[str, Any]:
        """
        単一メモリの圧縮
        
        Args:
            memory_id: メモリID
            
        Returns:
            Dict: 圧縮結果
        """
        async with self.pool.acquire() as conn:
            # メモリ取得
            memory = await conn.fetchrow("""
                SELECT * FROM semantic_memories WHERE id = $1
            """, memory_id)
            
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")
            
            # Claude Haikuで要約
            summary = await self._summarize_with_claude(memory['content'])
            
            # サイズ計算
            original_size = len(memory['content'].encode('utf-8'))
            compressed_size = len(summary.encode('utf-8'))
            compression_ratio = (original_size - compressed_size) / original_size
            
            # Archive保存
            archive_id = await conn.fetchval("""
                INSERT INTO memory_archive
                    (user_id, original_memory_id, original_content, original_embedding,
                     compressed_summary, compressed_at, original_size_bytes,
                     compressed_size_bytes, compression_ratio, final_importance_score,
                     archive_reason)
                VALUES ($1, $2, $3, $4, $5, NOW(), $6, $7, $8, $9, 'low_importance')
                RETURNING id
            """, memory['user_id'], memory['id'], memory['content'], 
                memory['embedding'], summary, original_size, compressed_size,
                compression_ratio, memory['importance_score'])
            
            # 元メモリ削除
            await conn.execute("DELETE FROM semantic_memories WHERE id = $1", memory_id)
            
            # ログ記録
            await conn.execute("""
                INSERT INTO memory_lifecycle_log
                    (user_id, memory_id, event_type, event_details, score_before)
                VALUES ($1, $2, 'compress', $3::jsonb, $4)
            """, memory['user_id'], memory['id'],
                {"archive_id": str(archive_id), "compression_ratio": compression_ratio},
                memory['importance_score'])
            
            return {
                "archive_id": archive_id,
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio
            }
    
    async def _summarize_with_claude(self, content: str) -> str:
        """Claude Haikuで要約"""
        message = self.claude.messages.create(
            model="claude-haiku-3-5-20241022",
            max_tokens=200,
            messages=[{
                "role": "user",
                "content": f"以下の会話を1-2文で要約してください：\n\n{content}"
            }]
        )
        
        return message.content[0].text
    
    async def compress_low_importance_memories(
        self,
        user_id: str,
        threshold: float = 0.3,
        limit: int = 100
    ) -> int:
        """
        低重要度メモリの一括圧縮
        
        Args:
            user_id: ユーザーID
            threshold: 重要度閾値（これ以下を圧縮）
            limit: 一度に圧縮する最大数
            
        Returns:
            int: 圧縮したメモリ数
        """
        async with self.pool.acquire() as conn:
            # 低重要度メモリ取得
            memories = await conn.fetch("""
                SELECT id FROM semantic_memories
                WHERE user_id = $1 AND importance_score < $2
                ORDER BY importance_score ASC
                LIMIT $3
            """, user_id, threshold, limit)
            
            compressed_count = 0
            for memory in memories:
                try:
                    await self.compress_memory(str(memory['id']))
                    compressed_count += 1
                except Exception as e:
                    logger.error(f"Compression failed for {memory['id']}: {e}")
            
            return compressed_count
```

### 5.3 Capacity Manager

**ファイル:** `memory_lifecycle/capacity_manager.py`

```python
class CapacityManager:
    """容量管理"""
    
    MEMORY_LIMIT = 10000  # メモリ上限
    AUTO_COMPRESS_THRESHOLD = 0.9  # 90%で自動圧縮
    
    def __init__(self, pool: asyncpg.Pool, compression_service: MemoryCompressionService):
        self.pool = pool
        self.compression_service = compression_service
    
    async def check_and_manage(self, user_id: str):
        """
        容量チェックと自動管理
        
        Args:
            user_id: ユーザーID
        """
        async with self.pool.acquire() as conn:
            # 現在のメモリ数
            total_memories = await conn.fetchval("""
                SELECT COUNT(*) FROM semantic_memories WHERE user_id = $1
            """, user_id)
            
            usage_ratio = total_memories / self.MEMORY_LIMIT
            
            if usage_ratio >= self.AUTO_COMPRESS_THRESHOLD:
                logger.warning(f"Memory usage {usage_ratio*100:.1f}% - triggering auto-compress")
                
                # 低重要度メモリ圧縮
                compressed_count = await self.compression_service.compress_low_importance_memories(
                    user_id=user_id,
                    threshold=0.3,
                    limit=int(self.MEMORY_LIMIT * 0.1)  # 10%を圧縮
                )
                
                logger.info(f"Auto-compressed {compressed_count} memories")
```

---

## 6. トークン・コスト見積もり

### 6.1 Claude Haiku圧縮コスト

**1メモリあたり:**
- Input: 500文字 × 2トークン = 1,000 tokens
- Output: 100文字 × 2トークン = 200 tokens
- 合計: 1,200 tokens

**料金（Claude Haiku）:**
- Input: $0.25 / 1M tokens
- Output: $1.25 / 1M tokens
- 1メモリあたり: (1,000 × 0.25 + 200 × 1.25) / 1,000,000 = $0.00055

**月間コスト想定:**
- 1日10メモリ圧縮 × 30日 = 300メモリ
- 300 × $0.00055 = $0.165/月（約20円/月）

---

## 7. パフォーマンス

### 7.1 レイテンシ目標

| 操作 | 目標 |
|------|------|
| Score計算（単一） | < 10ms |
| Score一括更新（1000件） | < 5秒 |
| メモリ圧縮（単一） | < 2秒 |
| 一括圧縮（100件） | < 200秒 |

---

## 8. 運用

### 8.1 スケジュールジョブ

**日次ジョブ:**
```python
# 毎日午前3時実行
async def daily_lifecycle_maintenance():
    # 1. 全ユーザーのスコア更新
    users = await get_all_users()
    for user in users:
        await scorer.update_all_scores(user.id)
    
    # 2. 容量チェック
    for user in users:
        await capacity_manager.check_and_manage(user.id)
    
    # 3. 古いArchiveの削除
    await cleanup_expired_archives()
```

---

## 9. 制約と前提

### 9.1 制約
- Claude Haiku利用（コスト削減）
- 圧縮は非可逆（元に戻せない）
- 完全削除までのgrace period: 90日

### 9.2 前提
- Sprint 5 Context Assembler実装済み
- PostgreSQL 13+（VECTOR型サポート）

---

## 10. 今後の拡張

### 10.1 Sprint 10候補
- AI判定による重要度評価
- ユーザーフィードバック統合（👍👎ボタン）
- マルチテナント対応

---

## 11. 参考資料

- [Sprint 5: Context Assembler仕様書](./sprint5_context_assembler_spec.md)
- [Sprint 8: User Profile仕様書](./sprint8_user_profile_spec.md)
- [Claude Haiku API Documentation](https://docs.anthropic.com/claude/docs/models-overview#model-comparison)
- [pgvector Documentation](https://github.com/pgvector/pgvector)

---

**作成日**: 2025-11-18  
**作成者**: Kana (Claude Sonnet 4.5)  
**バージョン**: 1.0.0  
**総行数**: 850
