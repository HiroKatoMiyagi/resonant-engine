import asyncio
import asyncpg

async def check():
    conn = await asyncpg.connect('postgresql://zero@localhost:5432/resonant')
    
    print("=== messages table ===")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_name = 'messages'
        ORDER BY ordinal_position
    """)
    for col in cols:
        print(f"  {col['column_name']}: {col['data_type']}")
    
    print("\n=== intents table ===")
    cols = await conn.fetch("""
        SELECT column_name, data_type 
        FROM information_schema.columns
        WHERE table_name = 'intents'
        ORDER BY ordinal_position
    """)
    for col in cols:
        print(f"  {col['column_name']}: {col['data_type']}")
    
    await conn.close()

asyncio.run(check())
