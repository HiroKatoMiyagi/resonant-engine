"""
システムテスト用共通フィクスチャとヘルパー関数

このモジュールには、システムテスト全体で使用される共通のヘルパー関数が含まれています。
"""
import os
import uuid
import json
import asyncpg
from datetime import datetime, timezone, timedelta
from typing import Optional, Dict, Any
from urllib.parse import quote_plus


# 環境変数から接続情報を取得
def get_db_dsn() -> str:
    """データベース接続文字列を取得"""
    user = os.getenv("POSTGRES_USER", "resonant")
    password = os.getenv("POSTGRES_PASSWORD")
    db = os.getenv("POSTGRES_DB", "postgres")
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = os.getenv("POSTGRES_PORT", "5432")
    
    if not password:
        raise ValueError("POSTGRES_PASSWORD environment variable is not set")
    
    # パスワードをURLエンコード
    password_encoded = quote_plus(password)
    
    return f"postgresql://{user}:{password_encoded}@{host}:{port}/{db}"


async def create_test_pool() -> asyncpg.Pool:
    """
    テスト用DB接続プールを作成
    
    Returns:
        asyncpg.Pool: データベース接続プール
    """
    host = os.getenv("POSTGRES_HOST", "postgres")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    user = os.getenv("POSTGRES_USER", "resonant")
    password = os.getenv("POSTGRES_PASSWORD")
    database = os.getenv("POSTGRES_DB", "postgres")
    
    if not password:
        raise ValueError("POSTGRES_PASSWORD environment variable is not set")
    
    pool = await asyncpg.create_pool(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        min_size=1,
        max_size=5
    )
    return pool


async def create_test_intent(
    pool: Optional[asyncpg.Pool] = None,
    user_id: str = "test_user",
    source: str = "KANA",
    intent_type: str = "FEATURE_REQUEST",
    content: str = "Test intent",
    status: str = "PENDING",
    created_at: Optional[datetime] = None,
    **kwargs
) -> str:
    """
    テスト用Intentを作成
    
    Args:
        pool: データベース接続プール（Noneの場合は新規作成）
        user_id: ユーザーID
        source: Intent のソース
        intent_type: Intent のタイプ
        content: Intent の内容
        status: Intent のステータス
        created_at: 作成日時
        **kwargs: その他のカラム値
    
    Returns:
        str: 作成されたIntent ID
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    intent_id = str(uuid.uuid4())
    if created_at is None:
        created_at = datetime.now(timezone.utc)
    
    try:
        async with pool.acquire() as conn:
            await conn.execute("""
                INSERT INTO intents (id, source, type, content, status, user_id, created_at, data)
                VALUES ($1, $2, $3, $4, $5, $6, $7, $8)
            """,
                uuid.UUID(intent_id),
                source,
                intent_type,
                content,
                status,
                user_id,
                created_at,
                json.dumps(kwargs.get("data", {}))
            )
        return intent_id
    finally:
        if should_close:
            await pool.close()


async def delete_test_intent(
    intent_id: str,
    pool: Optional[asyncpg.Pool] = None
) -> None:
    """
    テスト用Intentを削除
    
    Args:
        intent_id: 削除するIntent ID
        pool: データベース接続プール（Noneの場合は新規作成）
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM intents WHERE id = $1",
                uuid.UUID(intent_id)
            )
    finally:
        if should_close:
            await pool.close()


async def create_test_messages(
    user_id: str,
    count: int = 5,
    pool: Optional[asyncpg.Pool] = None
) -> list[str]:
    """
    テスト用メッセージを複数作成
    
    Args:
        user_id: ユーザーID
        count: 作成するメッセージ数
        pool: データベース接続プール（Noneの場合は新規作成）
    
    Returns:
        list[str]: 作成されたメッセージIDのリスト
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    message_ids = []
    
    try:
        async with pool.acquire() as conn:
            for i in range(count):
                message_id = str(uuid.uuid4())
                await conn.execute("""
                    INSERT INTO messages (id, user_id, content, message_type, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    uuid.UUID(message_id),
                    user_id,
                    f"テストメッセージ {i+1}",
                    "USER",
                    datetime.now(timezone.utc)
                )
                message_ids.append(message_id)
        
        return message_ids
    finally:
        if should_close:
            await pool.close()


async def delete_test_messages(
    user_id: str,
    pool: Optional[asyncpg.Pool] = None
) -> None:
    """
    テスト用メッセージを削除
    
    Args:
        user_id: ユーザーID
        pool: データベース接続プール（Noneの場合は新規作成）
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    try:
        async with pool.acquire() as conn:
            await conn.execute(
                "DELETE FROM messages WHERE user_id = $1",
                user_id
            )
    finally:
        if should_close:
            await pool.close()


async def create_test_choice_points(
    user_id: str,
    count: int = 3,
    pool: Optional[asyncpg.Pool] = None
) -> list[str]:
    """
    テスト用Choice Pointを複数作成
    
    Args:
        user_id: ユーザーID
        count: 作成するChoice Point数
        pool: データベース接続プール（Noneの場合は新規作成）
    
    Returns:
        list[str]: 作成されたChoice Point IDのリスト
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    choice_point_ids = []
    
    try:
        async with pool.acquire() as conn:
            for i in range(count):
                choice_point_id = str(uuid.uuid4())
                choices = [
                    {"id": "option_a", "description": f"選択肢A-{i}"},
                    {"id": "option_b", "description": f"選択肢B-{i}"}
                ]
                
                await conn.execute("""
                    INSERT INTO choice_points (id, user_id, question, choices, created_at)
                    VALUES ($1, $2, $3, $4, $5)
                """,
                    uuid.UUID(choice_point_id),
                    user_id,
                    f"テスト質問 {i+1}",
                    json.dumps(choices),
                    datetime.now(timezone.utc)
                )
                choice_point_ids.append(choice_point_id)
        
        return choice_point_ids
    finally:
        if should_close:
            await pool.close()


async def cleanup_test_data(
    user_id: str,
    pool: Optional[asyncpg.Pool] = None
) -> None:
    """
    テストユーザーに関連する全データをクリーンアップ
    
    Args:
        user_id: ユーザーID
        pool: データベース接続プール（Noneの場合は新規作成）
    """
    should_close = False
    if pool is None:
        pool = await create_test_pool()
        should_close = True
    
    try:
        async with pool.acquire() as conn:
            # 各テーブルからテストデータを削除
            await conn.execute("DELETE FROM messages WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM intents WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM choice_points WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM contradictions WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM memories WHERE user_id = $1", user_id)
            await conn.execute("DELETE FROM sessions WHERE user_id = $1", user_id)
    finally:
        if should_close:
            await pool.close()


# API テスト用のベースURL
def get_api_base_url() -> str:
    """API のベースURLを取得"""
    host = os.getenv("API_HOST", "localhost")
    port = os.getenv("API_PORT", "8000")
    return f"http://{host}:{port}"
