#!/usr/bin/env python3
"""
PostgreSQL接続テストとテーブル確認
"""
import asyncio
import asyncpg
from pathlib import Path
from dotenv import load_dotenv
import os

# 環境変数読み込み
ROOT = Path(__file__).parent.parent.parent
load_dotenv(ROOT / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "postgresql://resonant@localhost:5432/resonant")

async def test_database():
    """データベース接続テスト"""
    print("=" * 60)
    print("PostgreSQL 接続テスト")
    print("=" * 60)
    print(f"\n📡 接続先: {DATABASE_URL}\n")
    
    try:
        # 接続
        conn = await asyncpg.connect(DATABASE_URL)
        print("✅ PostgreSQL接続成功\n")
        
        # テーブル一覧
        tables = await conn.fetch("""
            SELECT table_name, 
                   (SELECT COUNT(*) FROM information_schema.columns 
                    WHERE table_schema = 'public' AND table_name = t.table_name) as column_count
            FROM information_schema.tables t
            WHERE table_schema = 'public'
            ORDER BY table_name
        """)
        
        print("📊 テーブル一覧:")
        for table in tables:
            print(f"  ✓ {table['table_name']:20s} ({table['column_count']} カラム)")
        
        # 各テーブルの詳細
        print("\n📋 テーブル詳細:")
        for table in tables:
            columns = await conn.fetch("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_schema = 'public' AND table_name = $1
                ORDER BY ordinal_position
            """, table['table_name'])
            
            print(f"\n  {table['table_name']}:")
            for col in columns:
                nullable = "NULL可" if col['is_nullable'] == 'YES' else "NOT NULL"
                print(f"    - {col['column_name']:20s} {col['data_type']:15s} {nullable}")
        
        # インデックス確認
        indexes = await conn.fetch("""
            SELECT indexname, tablename
            FROM pg_indexes
            WHERE schemaname = 'public'
            ORDER BY tablename, indexname
        """)
        
        print(f"\n🔍 インデックス一覧 ({len(indexes)}個):")
        for idx in indexes:
            print(f"  ✓ {idx['tablename']:20s} → {idx['indexname']}")
        
        await conn.close()
        
        print("\n" + "=" * 60)
        print("✅ すべてのテスト完了")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ エラー: {e}")
        raise

if __name__ == "__main__":
    asyncio.run(test_database())
