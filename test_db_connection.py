import asyncio
import asyncpg
import os

async def test_connection():
    try:
        conn = await asyncpg.connect(
            host='postgres',
            port=5432,
            user='resonant',
            password=os.getenv('POSTGRES_PASSWORD'),
            database='postgres'
        )
        result = await conn.fetchval('SELECT 1')
        await conn.close()
        print(f'✅ Connection successful! Result: {result}')
        print(f'Password used: {os.getenv("POSTGRES_PASSWORD")}')
    except Exception as e:
        print(f'❌ Connection failed: {e}')
        print(f'Password: {os.getenv("POSTGRES_PASSWORD")}')

asyncio.run(test_connection())
