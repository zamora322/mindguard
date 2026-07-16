import asyncpg
from typing import AsyncGenerator
from app.core.config import settings

# Global connection pool
db_pool: asyncpg.Pool | None = None

async def connect_to_db() -> None:
    global db_pool
    if not db_pool:
        try:
            db_pool = await asyncpg.create_pool(
                dsn=settings.DATABASE_URL,
                min_size=1,
                max_size=10
            )
            print("Successfully created PostgreSQL connection pool.")
        except Exception as e:
            print(f"Error creating connection pool: {e}")
            raise e

async def close_db_connection() -> None:
    global db_pool
    if db_pool:
        await db_pool.close()
        print("PostgreSQL connection pool closed.")

async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    global db_pool
    if not db_pool:
        raise Exception("Database connection pool is not initialized.")
    
    async with db_pool.acquire() as connection:
        yield connection
