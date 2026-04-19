import redis.asyncio as redis
from .config import get_settings

settings = get_settings()
_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = await redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client

async def close_redis():
    global _redis_client
    if _redis_client:
        await _redis_client.close()