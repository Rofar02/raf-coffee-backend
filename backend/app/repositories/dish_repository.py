import asyncpg
from typing import List, Dict, Any

class DishRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_all(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                SELECT id, name, price, description, calories, image_url
                FROM dishes
                ORDER BY id
            """)
            return [dict(row) for row in rows]