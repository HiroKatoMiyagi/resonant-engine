
import asyncio
import os
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy import text
from backend.app.services.memory.database import Base

# DB Configuration
DB_USER = os.getenv("POSTGRES_USER", "resonant")
DB_PASS = os.getenv("POSTGRES_PASSWORD", "ResonantEngine2025SecurePass!")
DB_HOST = os.getenv("POSTGRES_HOST", "localhost")
DB_PORT = os.getenv("POSTGRES_PORT", "5432")
DB_NAME = os.getenv("POSTGRES_DB", "resonant_dashboard")

DATABASE_URL = f"postgresql+asyncpg://{DB_USER}:{DB_PASS}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

async def reset_schema():
    print(f"Connecting to {DATABASE_URL}")
    engine = create_async_engine(DATABASE_URL, echo=True)
    
    async with engine.begin() as conn:
        print("Dropping tables...")
        # Order implies foreign key dependencies reversely
        tables = [
            "snapshots", "breathing_cycles", "choice_points", "agent_contexts", 
            "resonances", "intents", "sessions", "memory_queries",
            "semantic_memories", "memory_archive", "memory_lifecycle_log" 
        ]
        for table in tables:
            try:
                await conn.execute(text(f"DROP TABLE IF EXISTS {table} CASCADE"))
                print(f"Dropped {table}")
            except Exception as e:
                print(f"Drop error for {table}: {e}")

        print("Creating new tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("Tables created.")

    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(reset_schema())
