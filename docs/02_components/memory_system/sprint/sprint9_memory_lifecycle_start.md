# Sprint 9: Memory Lifecycle Management 作業開始指示書

## 概要

**Sprint**: 9  
**タイトル**: Memory Lifecycle Management  
**期間**: 5日間  
**目標**: メモリのライフサイクル管理機能実装（重要度評価・圧縮・忘却）

---

## Day 1: Database Schema & Importance Scoring

### 目標
- PostgreSQL スキーマ拡張（3テーブル）
- Importance Scorer 実装
- 時間減衰・アクセス強化アルゴリズム実装

### ステップ

#### 1.1 PostgreSQLマイグレーション作成

**ファイル**: `docker/postgres/006_memory_lifecycle_tables.sql`

```sql
-- ========================================
-- Sprint 9: Memory Lifecycle Tables
-- ========================================

-- 1. semantic_memories テーブル拡張
ALTER TABLE semantic_memories
ADD COLUMN IF NOT EXISTS importance_score FLOAT DEFAULT 0.5 CHECK (importance_score >= 0 AND importance_score <= 1),
ADD COLUMN IF NOT EXISTS last_accessed_at TIMESTAMP WITH TIME ZONE,
ADD COLUMN IF NOT EXISTS access_count INTEGER DEFAULT 0 CHECK (access_count >= 0),
ADD COLUMN IF NOT EXISTS decay_applied_at TIMESTAMP WITH TIME ZONE DEFAULT NOW();

-- インデックス追加
CREATE INDEX IF NOT EXISTS idx_semantic_memories_importance ON semantic_memories(importance_score DESC);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_decay ON semantic_memories(decay_applied_at);
CREATE INDEX IF NOT EXISTS idx_semantic_memories_access ON semantic_memories(last_accessed_at);

-- 2. memory_archive テーブル（新規）
CREATE TABLE IF NOT EXISTS memory_archive (
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
    archive_reason VARCHAR(100),
    
    -- 保持期限
    retention_until TIMESTAMP WITH TIME ZONE
);

CREATE INDEX IF NOT EXISTS idx_memory_archive_user_id ON memory_archive(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_archive_original_id ON memory_archive(original_memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_archive_retention ON memory_archive(retention_until);

-- 3. memory_lifecycle_log テーブル（新規）
CREATE TABLE IF NOT EXISTS memory_lifecycle_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    memory_id UUID NOT NULL,
    
    -- イベント情報
    event_type VARCHAR(50) NOT NULL,
    event_details JSONB,
    
    -- スコア変動
    score_before FLOAT,
    score_after FLOAT,
    
    -- タイムスタンプ
    event_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_user ON memory_lifecycle_log(user_id);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_memory ON memory_lifecycle_log(memory_id);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_event ON memory_lifecycle_log(event_type);
CREATE INDEX IF NOT EXISTS idx_memory_lifecycle_log_time ON memory_lifecycle_log(event_at);

-- 既存メモリのスコア初期化
UPDATE semantic_memories
SET importance_score = 0.5
WHERE importance_score IS NULL;
```

**実行**:
```bash
docker exec -i resonant-postgres psql -U resonant_user -d resonant_db < docker/postgres/006_memory_lifecycle_tables.sql
```

#### 1.2 Pydanticモデル作成

**ファイル**: `memory_lifecycle/models.py`

```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
from datetime import datetime
from uuid import UUID

class MemoryScore(BaseModel):
    """メモリスコア情報"""
    memory_id: UUID
    importance_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime
    last_accessed_at: Optional[datetime] = None
    access_count: int = 0
    decay_applied_at: datetime

class MemoryArchive(BaseModel):
    """アーカイブメモリ"""
    id: Optional[UUID] = None
    user_id: str
    original_memory_id: UUID
    original_content: str
    compressed_summary: str
    compression_method: str = "claude_haiku"
    compressed_at: Optional[datetime] = None
    original_size_bytes: int
    compressed_size_bytes: int
    compression_ratio: float
    final_importance_score: float
    archive_reason: str
    retention_until: Optional[datetime] = None

class LifecycleEvent(BaseModel):
    """ライフサイクルイベント"""
    id: Optional[UUID] = None
    user_id: str
    memory_id: UUID
    event_type: str  # 'score_update', 'compress', 'archive', 'delete'
    event_details: Optional[Dict[str, Any]] = None
    score_before: Optional[float] = None
    score_after: Optional[float] = None
    event_at: Optional[datetime] = None
```

#### 1.3 Importance Scorer実装

**ファイル**: `memory_lifecycle/importance_scorer.py`

```python
import asyncpg
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from .models import MemoryScore, LifecycleEvent

logger = logging.getLogger(__name__)

class ImportanceScorer:
    """メモリ重要度スコアリング"""
    
    # パラメータ
    DECAY_RATE = 0.95  # 週ごとに5%減衰
    BOOST_PER_ACCESS = 0.1  # アクセスごとに+10%
    MAX_SCORE = 1.0
    MIN_SCORE = 0.0
    
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool
    
    def calculate_time_decay(self, created_at: datetime) -> float:
        """
        時間減衰係数計算
        
        Args:
            created_at: 作成日時
            
        Returns:
            float: 減衰係数（0.0 - 1.0）
        """
        weeks_elapsed = (datetime.utcnow() - created_at).days / 7.0
        decay_factor = self.DECAY_RATE ** weeks_elapsed
        return decay_factor
    
    def calculate_access_boost(self, access_count: int) -> float:
        """
        アクセス強化係数計算
        
        Args:
            access_count: アクセス回数
            
        Returns:
            float: 強化係数（>= 1.0）
        """
        boost_factor = 1.0 + (access_count * self.BOOST_PER_ACCESS)
        return boost_factor
    
    def calculate_score(
        self,
        base_score: float,
        created_at: datetime,
        access_count: int
    ) -> float:
        """
        重要度スコア計算
        
        Args:
            base_score: 基本スコア
            created_at: 作成日時
            access_count: アクセス回数
            
        Returns:
            float: 重要度スコア（0.0 - 1.0）
        """
        time_decay = self.calculate_time_decay(created_at)
        access_boost = self.calculate_access_boost(access_count)
        
        score = base_score * time_decay * access_boost
        
        # 0-1の範囲にクリップ
        return max(self.MIN_SCORE, min(self.MAX_SCORE, score))
    
    async def update_memory_score(self, memory_id: str) -> float:
        """
        単一メモリのスコア更新
        
        Args:
            memory_id: メモリID
            
        Returns:
            float: 新しいスコア
        """
        async with self.pool.acquire() as conn:
            # メモリ情報取得
            memory = await conn.fetchrow("""
                SELECT id, user_id, created_at, importance_score, access_count
                FROM semantic_memories
                WHERE id = $1
            """, memory_id)
            
            if not memory:
                raise ValueError(f"Memory not found: {memory_id}")
            
            # 新スコア計算
            old_score = memory['importance_score']
            new_score = self.calculate_score(
                base_score=0.5,  # 基本スコアは固定
                created_at=memory['created_at'],
                access_count=memory['access_count']
            )
            
            # スコア更新
            await conn.execute("""
                UPDATE semantic_memories
                SET importance_score = $1,
                    decay_applied_at = NOW()
                WHERE id = $2
            """, new_score, memory_id)
            
            # ログ記録
            await conn.execute("""
                INSERT INTO memory_lifecycle_log
                    (user_id, memory_id, event_type, score_before, score_after, event_at)
                VALUES ($1, $2, 'score_update', $3, $4, NOW())
            """, memory['user_id'], memory_id, old_score, new_score)
            
            logger.debug(f"Memory {memory_id}: score {old_score:.3f} → {new_score:.3f}")
            
            return new_score
    
    async def update_all_scores(self, user_id: str) -> int:
        """
        全メモリのスコアを一括更新
        
        Args:
            user_id: ユーザーID
            
        Returns:
            int: 更新したメモリ数
        """
        async with self.pool.acquire() as conn:
            memories = await conn.fetch("""
                SELECT id FROM semantic_memories
                WHERE user_id = $1
            """, user_id)
            
            updated_count = 0
            for memory in memories:
                try:
                    await self.update_memory_score(str(memory['id']))
                    updated_count += 1
                except Exception as e:
                    logger.error(f"Failed to update score for {memory['id']}: {e}")
            
            logger.info(f"Updated {updated_count} memory scores for user {user_id}")
            return updated_count
    
    async def boost_on_access(self, memory_id: str):
        """
        アクセス時のスコア強化
        
        Args:
            memory_id: メモリID
        """
        async with self.pool.acquire() as conn:
            # アクセスカウント更新
            await conn.execute("""
                UPDATE semantic_memories
                SET access_count = access_count + 1,
                    last_accessed_at = NOW()
                WHERE id = $1
            """, memory_id)
            
            # スコア再計算
            await self.update_memory_score(memory_id)
```

### Day 1 成功基準
- [ ] 3つのテーブルがPostgreSQLに作成済み
- [ ] ImportanceScorer がスコア計算可能
- [ ] 単体テスト3件以上作成（時間減衰、アクセス強化、スコア更新）

### Git Commit
```bash
git add docker/postgres/006_memory_lifecycle_tables.sql memory_lifecycle/
git commit -m "Add Sprint 9 Day 1: Memory Lifecycle database schema and Importance Scorer"
```

---

## Day 2: Memory Compression Service実装

### 目標
- Claude Haiku統合
- メモリ圧縮機能実装
- アーカイブ保存機能

### ステップ

#### 2.1 Memory Compression Service実装

**ファイル**: `memory_lifecycle/compression_service.py`

```python
import asyncpg
from typing import Dict, Any, Optional
import anthropic
import logging
import json

from .models import MemoryArchive, LifecycleEvent

logger = logging.getLogger(__name__)

class MemoryCompressionService:
    """メモリ圧縮サービス"""
    
    def __init__(self, pool: asyncpg.Pool, anthropic_api_key: str):
        self.pool = pool
        self.claude = anthropic.Anthropic(api_key=anthropic_api_key)
    
    async def summarize_content(self, content: str) -> str:
        """
        Claude Haikuで内容を要約
        
        Args:
            content: 元コンテンツ
            
        Returns:
            str: 要約文
        """
        try:
            message = self.claude.messages.create(
                model="claude-haiku-3-5-20241022",
                max_tokens=200,
                messages=[{
                    "role": "user",
                    "content": f"""以下の会話内容を1-2文で簡潔に要約してください。
重要な情報（日付、名前、数値など）は必ず残してください。

内容:
{content}

要約:"""
                }]
            )
            
            summary = message.content[0].text.strip()
            logger.debug(f"Summarized: {len(content)} chars → {len(summary)} chars")
            return summary
            
        except Exception as e:
            logger.error(f"Claude Haiku summarization failed: {e}")
            # Fallback: 単純な切り詰め
            return content[:100] + "..." if len(content) > 100 else content
    
    async def compress_memory(
        self,
        memory_id: str,
        reason: str = "low_importance"
    ) -> Dict[str, Any]:
        """
        単一メモリの圧縮
        
        Args:
            memory_id: メモリID
            reason: 圧縮理由
            
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
            
            # 要約生成
            summary = await self.summarize_content(memory['content'])
            
            # サイズ計算
            original_size = len(memory['content'].encode('utf-8'))
            compressed_size = len(summary.encode('utf-8'))
            compression_ratio = (original_size - compressed_size) / original_size if original_size > 0 else 0
            
            # Archive保存
            archive_id = await conn.fetchval("""
                INSERT INTO memory_archive
                    (user_id, original_memory_id, original_content, original_embedding,
                     compressed_summary, compression_method, compressed_at,
                     original_size_bytes, compressed_size_bytes, compression_ratio,
                     final_importance_score, archive_reason)
                VALUES ($1, $2, $3, $4, $5, 'claude_haiku', NOW(), $6, $7, $8, $9, $10)
                RETURNING id
            """, memory['user_id'], memory['id'], memory['content'], 
                memory['embedding'], summary, original_size, compressed_size,
                compression_ratio, memory['importance_score'], reason)
            
            # 元メモリ削除
            await conn.execute("DELETE FROM semantic_memories WHERE id = $1", memory_id)
            
            # ログ記録
            await conn.execute("""
                INSERT INTO memory_lifecycle_log
                    (user_id, memory_id, event_type, event_details, score_before)
                VALUES ($1, $2, 'compress', $3::jsonb, $4)
            """, memory['user_id'], memory['id'],
                json.dumps({
                    "archive_id": str(archive_id),
                    "compression_ratio": compression_ratio,
                    "reason": reason
                }),
                memory['importance_score'])
            
            logger.info(f"Compressed memory {memory_id}: {compression_ratio*100:.1f}% reduction")
            
            return {
                "archive_id": str(archive_id),
                "original_size": original_size,
                "compressed_size": compressed_size,
                "compression_ratio": compression_ratio
            }
    
    async def compress_low_importance_memories(
        self,
        user_id: str,
        threshold: float = 0.3,
        limit: int = 100
    ) -> Dict[str, Any]:
        """
        低重要度メモリの一括圧縮
        
        Args:
            user_id: ユーザーID
            threshold: 重要度閾値（これ以下を圧縮）
            limit: 一度に圧縮する最大数
            
        Returns:
            Dict: 圧縮結果サマリ
        """
        async with self.pool.acquire() as conn:
            # 低重要度メモリ取得
            memories = await conn.fetch("""
                SELECT id, importance_score FROM semantic_memories
                WHERE user_id = $1 AND importance_score < $2
                ORDER BY importance_score ASC
                LIMIT $3
            """, user_id, threshold, limit)
            
            compressed_count = 0
            failed_count = 0
            total_original_size = 0
            total_compressed_size = 0
            
            for memory in memories:
                try:
                    result = await self.compress_memory(
                        str(memory['id']),
                        reason="low_importance"
                    )
                    compressed_count += 1
                    total_original_size += result['original_size']
                    total_compressed_size += result['compressed_size']
                except Exception as e:
                    logger.error(f"Compression failed for {memory['id']}: {e}")
                    failed_count += 1
            
            overall_ratio = (total_original_size - total_compressed_size) / total_original_size if total_original_size > 0 else 0
            
            logger.info(f"Batch compression: {compressed_count} succeeded, {failed_count} failed, {overall_ratio*100:.1f}% reduction")
            
            return {
                "compressed_count": compressed_count,
                "failed_count": failed_count,
                "overall_compression_ratio": overall_ratio,
                "total_original_size": total_original_size,
                "total_compressed_size": total_compressed_size
            }
    
    async def restore_from_archive(self, archive_id: str) -> str:
        """
        アーカイブからメモリを復元
        
        Args:
            archive_id: アーカイブID
            
        Returns:
            str: 復元されたメモリID
        """
        async with self.pool.acquire() as conn:
            # アーカイブ取得
            archive = await conn.fetchrow("""
                SELECT * FROM memory_archive WHERE id = $1
            """, archive_id)
            
            if not archive:
                raise ValueError(f"Archive not found: {archive_id}")
            
            # メモリ復元
            memory_id = await conn.fetchval("""
                INSERT INTO semantic_memories
                    (user_id, content, embedding, importance_score, created_at)
                VALUES ($1, $2, $3, $4, $5)
                RETURNING id
            """, archive['user_id'], archive['original_content'],
                archive['original_embedding'], archive['final_importance_score'],
                archive['compressed_at'])
            
            # アーカイブ削除
            await conn.execute("DELETE FROM memory_archive WHERE id = $1", archive_id)
            
            logger.info(f"Restored memory {memory_id} from archive {archive_id}")
            
            return str(memory_id)
```

### Day 2 成功基準
- [ ] Claude Haiku統合完了
- [ ] メモリ圧縮が動作（単一・一括）
- [ ] アーカイブ保存・復元機能動作

### Git Commit
```bash
git add memory_lifecycle/compression_service.py
git commit -m "Add Sprint 9 Day 2: Memory Compression Service with Claude Haiku"
```

---

## Day 3: Capacity Manager & Scheduler実装

### 目標
- 容量管理機能実装
- 自動トリガーロジック
- スケジュールジョブ実装

### ステップ

#### 3.1 Capacity Manager実装

**ファイル**: `memory_lifecycle/capacity_manager.py`

```python
import asyncpg
from typing import Dict, Any
import logging

from .compression_service import MemoryCompressionService
from .importance_scorer import ImportanceScorer

logger = logging.getLogger(__name__)

class CapacityManager:
    """容量管理"""
    
    # 容量制限
    MEMORY_LIMIT = 10000  # メモリ上限
    AUTO_COMPRESS_THRESHOLD = 0.9  # 90%で自動圧縮
    COMPRESSION_BATCH_SIZE = 1000  # 一度に圧縮する数
    
    def __init__(
        self,
        pool: asyncpg.Pool,
        compression_service: MemoryCompressionService,
        scorer: ImportanceScorer
    ):
        self.pool = pool
        self.compression_service = compression_service
        self.scorer = scorer
    
    async def get_memory_usage(self, user_id: str) -> Dict[str, Any]:
        """
        メモリ使用状況取得
        
        Args:
            user_id: ユーザーID
            
        Returns:
            Dict: 使用状況
        """
        async with self.pool.acquire() as conn:
            # アクティブメモリ数
            active_count = await conn.fetchval("""
                SELECT COUNT(*) FROM semantic_memories WHERE user_id = $1
            """, user_id)
            
            # アーカイブ数
            archive_count = await conn.fetchval("""
                SELECT COUNT(*) FROM memory_archive WHERE user_id = $1
            """, user_id)
            
            # 合計サイズ（概算）
            total_size = await conn.fetchval("""
                SELECT SUM(LENGTH(content)) FROM semantic_memories WHERE user_id = $1
            """, user_id) or 0
            
            usage_ratio = active_count / self.MEMORY_LIMIT
            
            return {
                "active_count": active_count,
                "archive_count": archive_count,
                "total_count": active_count + archive_count,
                "usage_ratio": usage_ratio,
                "total_size_bytes": total_size,
                "limit": self.MEMORY_LIMIT
            }
    
    async def check_and_manage(self, user_id: str) -> Dict[str, Any]:
        """
        容量チェックと自動管理
        
        Args:
            user_id: ユーザーID
            
        Returns:
            Dict: 管理結果
        """
        usage = await self.get_memory_usage(user_id)
        
        if usage['usage_ratio'] < self.AUTO_COMPRESS_THRESHOLD:
            logger.info(f"Memory usage {usage['usage_ratio']*100:.1f}% - OK")
            return {"action": "none", "usage": usage}
        
        logger.warning(f"Memory usage {usage['usage_ratio']*100:.1f}% - triggering auto-compress")
        
        # 1. スコア更新
        updated_count = await self.scorer.update_all_scores(user_id)
        logger.info(f"Updated {updated_count} scores")
        
        # 2. 低重要度メモリ圧縮
        compress_result = await self.compression_service.compress_low_importance_memories(
            user_id=user_id,
            threshold=0.3,
            limit=self.COMPRESSION_BATCH_SIZE
        )
        
        # 3. 使用状況再取得
        new_usage = await self.get_memory_usage(user_id)
        
        return {
            "action": "auto_compress",
            "old_usage": usage,
            "new_usage": new_usage,
            "compress_result": compress_result
        }
```

#### 3.2 Scheduler実装

**ファイル**: `memory_lifecycle/scheduler.py`

```python
import asyncpg
from typing import List
import logging
from datetime import datetime, timedelta

from .importance_scorer import ImportanceScorer
from .capacity_manager import CapacityManager
from .compression_service import MemoryCompressionService

logger = logging.getLogger(__name__)

class LifecycleScheduler:
    """ライフサイクルスケジューラー"""
    
    def __init__(
        self,
        pool: asyncpg.Pool,
        scorer: ImportanceScorer,
        capacity_manager: CapacityManager
    ):
        self.pool = pool
        self.scorer = scorer
        self.capacity_manager = capacity_manager
    
    async def get_all_users(self) -> List[str]:
        """全ユーザーID取得"""
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT DISTINCT user_id FROM semantic_memories
            """)
            return [row['user_id'] for row in rows]
    
    async def daily_maintenance(self):
        """日次メンテナンス"""
        logger.info("=== Daily Lifecycle Maintenance Started ===")
        
        users = await self.get_all_users()
        logger.info(f"Processing {len(users)} users")
        
        for user_id in users:
            try:
                # 1. スコア更新
                updated = await self.scorer.update_all_scores(user_id)
                logger.info(f"User {user_id}: updated {updated} scores")
                
                # 2. 容量チェック＆管理
                result = await self.capacity_manager.check_and_manage(user_id)
                logger.info(f"User {user_id}: {result['action']}")
                
            except Exception as e:
                logger.error(f"Maintenance failed for user {user_id}: {e}")
        
        logger.info("=== Daily Lifecycle Maintenance Completed ===")
    
    async def cleanup_expired_archives(self, retention_days: int = 90):
        """期限切れアーカイブのクリーンアップ"""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        async with self.pool.acquire() as conn:
            deleted = await conn.execute("""
                DELETE FROM memory_archive
                WHERE retention_until IS NOT NULL
                  AND retention_until < $1
            """, cutoff_date)
            
            logger.info(f"Deleted {deleted} expired archives")
```

### Day 3 成功基準
- [ ] CapacityManager が容量チェック・自動圧縮可能
- [ ] Scheduler が日次メンテナンス実行可能
- [ ] 期限切れアーカイブ削除機能動作

### Git Commit
```bash
git add memory_lifecycle/capacity_manager.py memory_lifecycle/scheduler.py
git commit -m "Add Sprint 9 Day 3: Capacity Manager and Lifecycle Scheduler"
```

---

## Day 4: Retrieval Orchestrator & Context Assembler統合

### 目標
- Retrieval Orchestratorでスコアベース取得
- Context Assemblerでアクセスブースト統合

### ステップ

#### 4.1 Retrieval Orchestrator拡張

**ファイル**: `retrieval/orchestrator.py` (変更)

```python
# 既存実装に追加
from memory_lifecycle.importance_scorer import ImportanceScorer

class RetrievalOrchestrator:
    def __init__(
        self,
        memory_repo: MemoryRepository,
        scorer: Optional[ImportanceScorer] = None  # ← NEW
    ):
        self.memory_repo = memory_repo
        self.scorer = scorer  # ← NEW
    
    async def retrieve_semantic_memories(
        self,
        query_text: str,
        user_id: str,
        limit: int = 5,
        use_importance_score: bool = True  # ← NEW
    ) -> List[Dict[str, Any]]:
        """
        Semantic Memory取得（重要度スコア統合版）
        
        Args:
            query_text: クエリテキスト
            user_id: ユーザーID
            limit: 取得件数
            use_importance_score: スコアベースランキング有効化
            
        Returns:
            List: Semantic Memories
        """
        # ベクトル検索
        memories = await self.memory_repo.search_memories(
            query_text=query_text,
            user_id=user_id,
            limit=limit * 2  # スコアフィルタリング用に多めに取得
        )
        
        if use_importance_score and self.scorer:
            # 重要度スコアでソート
            memories.sort(
                key=lambda m: m.get('importance_score', 0.5),
                reverse=True
            )
            memories = memories[:limit]
            
            # アクセスブースト適用
            for memory in memories:
                try:
                    await self.scorer.boost_on_access(str(memory['id']))
                except Exception as e:
                    logger.warning(f"Boost failed for {memory['id']}: {e}")
        
        return memories
```

### Day 4 成功基準
- [ ] Retrieval Orchestratorがスコアベース取得可能
- [ ] アクセス時に自動的にスコアブースト
- [ ] Context Assembler統合テスト成功

### Git Commit
```bash
git add retrieval/orchestrator.py
git commit -m "Add Sprint 9 Day 4: Integrate Importance Scoring with Retrieval"
```

---

## Day 5: テスト & ドキュメント

### 目標
- 単体テスト・統合テスト作成
- E2Eテスト
- 運用ドキュメント

### ステップ

#### 5.1 単体テスト

**ファイル**: `tests/memory_lifecycle/test_importance_scorer.py`

```python
import pytest
from datetime import datetime, timedelta
from memory_lifecycle.importance_scorer import ImportanceScorer

def test_time_decay_calculation():
    """時間減衰計算テスト"""
    scorer = ImportanceScorer(None)
    
    # 1週間経過
    created_at = datetime.utcnow() - timedelta(weeks=1)
    decay = scorer.calculate_time_decay(created_at)
    assert 0.94 < decay < 0.96  # 約0.95
    
    # 4週間経過
    created_at = datetime.utcnow() - timedelta(weeks=4)
    decay = scorer.calculate_time_decay(created_at)
    assert 0.80 < decay < 0.82  # 約0.95^4 = 0.81

def test_access_boost_calculation():
    """アクセス強化計算テスト"""
    scorer = ImportanceScorer(None)
    
    # アクセス0回
    boost = scorer.calculate_access_boost(0)
    assert boost == 1.0
    
    # アクセス5回
    boost = scorer.calculate_access_boost(5)
    assert boost == 1.5  # 1 + (5 * 0.1)

def test_score_calculation():
    """スコア計算テスト"""
    scorer = ImportanceScorer(None)
    
    # 新規メモリ（1週間前、アクセス0）
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.utcnow() - timedelta(weeks=1),
        access_count=0
    )
    assert 0.47 < score < 0.48  # 0.5 * 0.95
    
    # 頻繁アクセスメモリ（1週間前、アクセス5回）
    score = scorer.calculate_score(
        base_score=0.5,
        created_at=datetime.utcnow() - timedelta(weeks=1),
        access_count=5
    )
    assert 0.71 < score < 0.72  # 0.5 * 0.95 * 1.5
```

**ファイル**: `tests/memory_lifecycle/test_compression.py`

```python
@pytest.mark.asyncio
async def test_memory_compression(db_pool, anthropic_api_key):
    """メモリ圧縮テスト"""
    service = MemoryCompressionService(db_pool, anthropic_api_key)
    
    # テストメモリ作成
    async with db_pool.acquire() as conn:
        memory_id = await conn.fetchval("""
            INSERT INTO semantic_memories (user_id, content, importance_score)
            VALUES ('test_user', $1, 0.2)
            RETURNING id
        """, "これは非常に長い会話のテストです。" * 20)
    
    # 圧縮実行
    result = await service.compress_memory(str(memory_id))
    
    # 検証
    assert result['compression_ratio'] > 0.5  # 50%以上圧縮
    assert result['original_size'] > result['compressed_size']
    
    # アーカイブ確認
    async with db_pool.acquire() as conn:
        archive = await conn.fetchrow("""
            SELECT * FROM memory_archive WHERE id = $1
        """, result['archive_id'])
        
        assert archive is not None
        assert len(archive['compressed_summary']) < len(archive['original_content'])
```

#### 5.2 E2Eテスト

**ファイル**: `tests/integration/test_memory_lifecycle_e2e.py`

```python
@pytest.mark.asyncio
async def test_full_lifecycle_flow(db_pool, anthropic_api_key):
    """完全ライフサイクルフローテスト"""
    # セットアップ
    scorer = ImportanceScorer(db_pool)
    compression_service = MemoryCompressionService(db_pool, anthropic_api_key)
    capacity_manager = CapacityManager(db_pool, compression_service, scorer)
    
    user_id = "test_user"
    
    # 1. 低重要度メモリ10件作成
    async with db_pool.acquire() as conn:
        for i in range(10):
            await conn.execute("""
                INSERT INTO semantic_memories (user_id, content, importance_score, created_at)
                VALUES ($1, $2, 0.2, NOW() - INTERVAL '30 days')
            """, user_id, f"古い会話 {i}")
    
    # 2. スコア更新
    updated = await scorer.update_all_scores(user_id)
    assert updated == 10
    
    # 3. 低重要度メモリ圧縮
    result = await compression_service.compress_low_importance_memories(
        user_id=user_id,
        threshold=0.3,
        limit=5
    )
    
    assert result['compressed_count'] == 5
    assert result['overall_compression_ratio'] > 0.5
    
    # 4. アーカイブ確認
    async with db_pool.acquire() as conn:
        archive_count = await conn.fetchval("""
            SELECT COUNT(*) FROM memory_archive WHERE user_id = $1
        """, user_id)
        
        assert archive_count == 5
```

### Day 5 成功基準
- [ ] 単体テスト15件以上作成・全件PASS
- [ ] E2Eテスト成功
- [ ] 運用ドキュメント完成

### Git Commit
```bash
git add tests/ docs/
git commit -m "Add Sprint 9 Day 5: Tests and operational documentation"
```

---

## 最終確認

### チェックリスト

**Tier 1: 必須要件**
- [ ] Memory Importance Scoring実装（時間減衰・アクセス強化）
- [ ] Memory Compression機能実装（Claude Haikuによる要約）
- [ ] Memory Archive機能実装（低重要度メモリの保管）
- [ ] 容量管理機能実装（上限チェック・自動圧縮トリガー）
- [ ] 15 件以上の単体/統合テストが作成され、CI で緑

**Tier 2: 品質要件**
- [ ] 重要度スコア計算が適切（減衰率・強化率）
- [ ] 圧縮率 > 70%（元サイズに対して）
- [ ] 圧縮レイテンシ < 2秒/メモリ
- [ ] 容量上限到達時の自動処理が動作
- [ ] Observability: `memory_compression_rate`, `memory_archive_count`

### 最終コミット

```bash
git add .
git commit -m "Complete Sprint 9: Memory Lifecycle Management

- PostgreSQL schema with 3 new tables (memory_archive, memory_lifecycle_log) and semantic_memories extension
- Importance Scoring Engine with time decay and access boost
- Memory Compression Service with Claude Haiku integration
- Capacity Manager with auto-trigger logic
- Lifecycle Scheduler for daily maintenance
- 15+ unit and integration tests
- Compression ratio: > 70% average"

git push -u origin claude/add-conversation-memory-017fnuDD9kLAQh58XR9AKmwB
```

---

**作成日**: 2025-11-18  
**作成者**: Kana (Claude Sonnet 4.5)  
**総行数**: 905
