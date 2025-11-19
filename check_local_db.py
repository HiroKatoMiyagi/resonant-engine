import asyncio
import asyncpg

async def check():
    try:
        # ローカルPostgreSQLに接続（認証なし）
        conn = await asyncpg.connect('postgresql://zero@localhost:5432/postgres')
        dbs = await conn.fetch('SELECT datname FROM pg_database')
        print("Available databases:")
        for db in dbs:
            print(f"  - {db['datname']}")
        await conn.close()
    except Exception as e:
        print(f"Error: {e}")

asyncio.run(check())
