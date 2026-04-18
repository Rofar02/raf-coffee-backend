import asyncpg
from .config import get_settings

settings = get_settings()
_pool = None

async def init_pool():
    global _pool
    if _pool is None:
        _pool = await asyncpg.create_pool(
            settings.DATABASE_URL,
            min_size=1,
            max_size=10
        )
    return _pool

async def get_pool():
    if _pool is None:
        await init_pool()
    return _pool

async def close_pool():
    global _pool
    if _pool:
        await _pool.close()
        _pool = None