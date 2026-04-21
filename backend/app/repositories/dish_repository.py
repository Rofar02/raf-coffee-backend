import asyncpg
from typing import Any, Dict, List, Optional

from asyncpg.exceptions import UndefinedColumnError, UndefinedTableError


_SQL_WITH_CATEGORIES = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.subcategory_id,
        c.id AS category_id,
        c.name AS category_name,
        s.name AS subcategory_name
    FROM dishes d
    LEFT JOIN subcategories s ON d.subcategory_id = s.id
    LEFT JOIN categories c ON s.category_id = c.id
    ORDER BY
        c.sort_order NULLS LAST,
        c.id NULLS LAST,
        s.sort_order NULLS LAST,
        s.id NULLS LAST,
        d.id
"""

# Старая БД: только dishes (нет categories / subcategories)
_SQL_DISHES_ONLY_WITH_SUBCAT = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.subcategory_id,
        NULL::integer AS category_id,
        NULL::text AS category_name,
        NULL::text AS subcategory_name
    FROM dishes d
    ORDER BY d.id
"""

# Схема без колонки subcategory_id
_SQL_DISHES_MINIMAL = """
    SELECT
        id,
        name,
        price,
        NULL::integer AS weight_grams,
        description,
        calories,
        image_url,
        video_url,
        NULL::integer AS subcategory_id,
        NULL::integer AS category_id,
        NULL::text AS category_name,
        NULL::text AS subcategory_name
    FROM dishes
    ORDER BY id
"""


class DishRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_all(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            last: Optional[Exception] = None
            for sql in (
                _SQL_WITH_CATEGORIES,
                _SQL_DISHES_ONLY_WITH_SUBCAT,
                _SQL_DISHES_MINIMAL,
            ):
                try:
                    rows = await conn.fetch(sql)
                    return [dict(row) for row in rows]
                except (UndefinedTableError, UndefinedColumnError) as e:
                    last = e
                    continue
            if last:
                raise last
            return []

    async def list_subcategories(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(
                    """
                    SELECT s.id, c.name AS category_name, s.name AS subcategory_name
                    FROM subcategories s
                    JOIN categories c ON c.id = s.category_id
                    ORDER BY c.sort_order NULLS LAST, c.id, s.sort_order NULLS LAST, s.id
                    """
                )
                return [dict(row) for row in rows]
            except (UndefinedTableError, UndefinedColumnError):
                return []

    async def create(self, dish_data: dict) -> int:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow("""
                                      INSERT INTO dishes (name, price, weight_grams, description, calories, image_url, video_url, subcategory_id)
                                      VALUES ($1, $2, $3, $4, $5, $6, $7, $8) RETURNING id
                                      """, dish_data['name'], dish_data['price'], dish_data.get('weight_grams'),
                                      dish_data['description'],
                                      dish_data.get('calories'), dish_data.get('image_url'), dish_data.get('video_url'),
                                      dish_data.get('subcategory_id'))
            return row['id']
