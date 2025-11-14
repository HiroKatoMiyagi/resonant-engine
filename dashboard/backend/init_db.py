#!/usr/bin/env python3
"""
PostgreSQLデータベース初期化スクリプト
schema.sqlを読み込んでテーブルを作成
"""
import asyncio
import asyncpg
from pathlib import Path
from dotenv import load_dotenv
import os

# 環境変数読み込み
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

# デフォルトのDB接続情報
DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://resonant:password@localhost:5432/resonant")

async def init_database():
    """データベースを初期化"""
    print(f"🔄 Connecting to database: {DATABASE_URL}")
    
    try:
        # データベース接続
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ Connected to PostgreSQL")
        
        # schema.sqlを読み込み
        schema_file = Path(__file__).parent / "schema.sql"
        print(f"📄 Reading schema from: {schema_file}")
        
        with open(schema_file, "r", encoding="utf-8") as f:
            schema_sql = f.read()
        
        # スキーマを適用
        print("🔨 Applying schema...")
        await conn.execute(schema_sql)
        print("✅ Schema applied successfully")
        
        # テーブル一覧を確認
        tables = await conn.fetch("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print("\n📊 Created tables:")
        for table in tables:
            print(f"  - {table['table_name']}")
        
        await conn.close()
        print("\n✅ Database initialization completed")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(init_database())
