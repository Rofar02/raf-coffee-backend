import asyncpg
from typing import List, Dict, Any

class DishRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_all(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch("""
                                    SELECT id, name, price, description, calories, image_url, video_url, subcategory_id
                                    FROM dishes
                                    ORDER BY id
                                    """)
            return [dict(row) for row in rows]

    async def create(self, dish_data: dict) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                                      INSERT INTO dishes (name, price, description, calories, image_url, video_url, subcategory_id)
                                      VALUES ($1, $2, $3, $4, $5, $6, $7) RETURNING id
                                      """, dish_data['name'], dish_data['price'], dish_data['description'],
                                      dish_data.get('calories'), dish_data.get('image_url'), dish_data.get('video_url'),
                                      dish_data.get('subcategory_id'))
            return row['id']