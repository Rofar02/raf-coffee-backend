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

_SQL_ACTIVE_SEASON_MENU = """
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
    FROM season_dishes sd
    JOIN menu_seasons ms ON ms.id = sd.season_id AND ms.is_active = TRUE
    JOIN dishes d ON d.id = sd.dish_id
    LEFT JOIN subcategories s ON d.subcategory_id = s.id
    LEFT JOIN categories c ON s.category_id = c.id
    WHERE sd.is_visible = TRUE
    ORDER BY
        c.sort_order NULLS LAST,
        c.id NULLS LAST,
        s.sort_order NULLS LAST,
        s.id NULLS LAST,
        sd.sort_order NULLS LAST,
        d.id
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
                    SELECT s.id, c.id AS category_id, c.name AS category_name, s.name AS subcategory_name
                    FROM subcategories s
                    JOIN categories c ON c.id = s.category_id
                    ORDER BY c.sort_order NULLS LAST, c.id, s.sort_order NULLS LAST, s.id
                    """
                )
                return [dict(row) for row in rows]
            except (UndefinedTableError, UndefinedColumnError):
                return []

    async def get_menu_items_for_active_season(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(_SQL_ACTIVE_SEASON_MENU)
                return [dict(row) for row in rows]
            except (UndefinedTableError, UndefinedColumnError):
                return await self.get_all()

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

    async def update(self, dish_id: int, dish_data: dict) -> bool:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE dishes
                SET
                    name = $2,
                    price = $3,
                    weight_grams = $4,
                    description = $5,
                    calories = $6,
                    image_url = $7,
                    video_url = $8,
                    subcategory_id = $9
                WHERE id = $1
                RETURNING id
                """,
                dish_id,
                dish_data["name"],
                dish_data["price"],
                dish_data.get("weight_grams"),
                dish_data.get("description"),
                dish_data.get("calories"),
                dish_data.get("image_url"),
                dish_data.get("video_url"),
                dish_data.get("subcategory_id"),
            )
            return row is not None

    async def delete(self, dish_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM dishes WHERE id = $1", dish_id)
            return result.endswith("1")

    async def list_seasons(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT id, name, slug, is_active, sort_order, created_at
                FROM menu_seasons
                ORDER BY sort_order, id
                """
            )
            return [dict(row) for row in rows]

    async def create_season(self, season_data: dict) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO menu_seasons (name, slug, is_active, sort_order)
                VALUES ($1, $2, $3, $4)
                RETURNING id, name, slug, is_active, sort_order, created_at
                """,
                season_data["name"],
                season_data["slug"],
                season_data.get("is_active", False),
                season_data.get("sort_order", 0),
            )
            return dict(row)

    async def update_season(self, season_id: int, payload: dict) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE menu_seasons
                SET
                    name = COALESCE($2, name),
                    slug = COALESCE($3, slug),
                    sort_order = COALESCE($4, sort_order)
                WHERE id = $1
                RETURNING id, name, slug, is_active, sort_order, created_at
                """,
                season_id,
                payload.get("name"),
                payload.get("slug"),
                payload.get("sort_order"),
            )
            return dict(row) if row else None

    async def set_active_season(self, season_id: int) -> bool:
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM menu_seasons WHERE id = $1)", season_id)
            if not exists:
                return False
            await conn.execute("UPDATE menu_seasons SET is_active = FALSE WHERE is_active = TRUE")
            await conn.execute("UPDATE menu_seasons SET is_active = TRUE WHERE id = $1", season_id)
            return True

    async def list_dishes_by_season(self, season_id: int) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
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
                    s.name AS subcategory_name,
                    sd.sort_order AS season_sort_order,
                    sd.is_visible AS season_visible
                FROM season_dishes sd
                JOIN dishes d ON d.id = sd.dish_id
                LEFT JOIN subcategories s ON d.subcategory_id = s.id
                LEFT JOIN categories c ON s.category_id = c.id
                WHERE sd.season_id = $1
                ORDER BY
                    c.sort_order NULLS LAST,
                    c.id NULLS LAST,
                    s.sort_order NULLS LAST,
                    s.id NULLS LAST,
                    sd.sort_order NULLS LAST,
                    d.id
                """,
                season_id,
            )
            return [dict(row) for row in rows]

    async def attach_dish_to_season(
        self,
        season_id: int,
        dish_id: int,
        sort_order: int = 0,
        is_visible: bool = True,
    ) -> bool:
        async with self.pool.acquire() as conn:
            exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM dishes WHERE id = $1)", dish_id)
            season_exists = await conn.fetchval("SELECT EXISTS(SELECT 1 FROM menu_seasons WHERE id = $1)", season_id)
            if not exists or not season_exists:
                return False
            await conn.execute(
                """
                INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
                VALUES ($1, $2, $3, $4)
                ON CONFLICT (season_id, dish_id)
                DO UPDATE SET sort_order = EXCLUDED.sort_order, is_visible = EXCLUDED.is_visible
                """,
                season_id,
                dish_id,
                sort_order,
                is_visible,
            )
            return True

    async def detach_dish_from_season(self, season_id: int, dish_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute(
                "DELETE FROM season_dishes WHERE season_id = $1 AND dish_id = $2",
                season_id,
                dish_id,
            )
            return result.endswith("1")
