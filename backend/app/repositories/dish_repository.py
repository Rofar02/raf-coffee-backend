import asyncpg
from collections import defaultdict
from typing import Any, Dict, List, Optional

from asyncpg.exceptions import UndefinedColumnError, UndefinedTableError


_SQL_WITH_CATEGORIES = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
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
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
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
        NULL::integer AS volume_ml,
        description,
        calories,
        image_url,
        video_url,
        TRUE AS is_base_menu,
        NULL::integer AS subcategory_id,
        NULL::integer AS category_id,
        NULL::text AS category_name,
        NULL::text AS subcategory_name
    FROM dishes
    ORDER BY id
"""

_DISH_BY_ID_WITH_CATEGORIES = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
        d.subcategory_id,
        c.id AS category_id,
        c.name AS category_name,
        s.name AS subcategory_name
    FROM dishes d
    LEFT JOIN subcategories s ON d.subcategory_id = s.id
    LEFT JOIN categories c ON s.category_id = c.id
    WHERE d.id = $1
"""

_DISH_BY_ID_NO_JOIN = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
        d.subcategory_id,
        NULL::integer AS category_id,
        NULL::text AS category_name,
        NULL::text AS subcategory_name
    FROM dishes d
    WHERE d.id = $1
"""

_SQL_ACTIVE_SEASON_MENU = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
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

_SQL_BASE_MENU_WITH_CATEGORIES = """
    SELECT
        d.id,
        d.name,
        d.price,
        d.weight_grams,
        d.volume_ml,
        d.description,
        d.calories,
        d.image_url,
        d.video_url,
        d.is_base_menu,
        d.subcategory_id,
        c.id AS category_id,
        c.name AS category_name,
        s.name AS subcategory_name
    FROM dishes d
    LEFT JOIN subcategories s ON d.subcategory_id = s.id
    LEFT JOIN categories c ON s.category_id = c.id
    WHERE d.is_base_menu = TRUE
    ORDER BY
        c.sort_order NULLS LAST,
        c.id NULLS LAST,
        s.sort_order NULLS LAST,
        s.id NULLS LAST,
        d.id
"""


def _normalize_volume_options(raw: Any) -> List[Dict[str, Any]]:
    if not raw:
        return []
    out: List[Dict[str, Any]] = []
    for i, o in enumerate(raw):
        if not isinstance(o, dict):
            continue
        try:
            vm = o.get("volume_ml")
            pr = o.get("price")
            if vm is None or pr is None:
                continue
            out.append(
                {
                    "volume_ml": int(vm),
                    "price": int(pr),
                    "sort_order": int(o.get("sort_order", i)),
                }
            )
        except (TypeError, ValueError):
            continue
    return out


class DishRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_dish_by_id(self, dish_id: int) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            last: Optional[Exception] = None
            for sql in (_DISH_BY_ID_WITH_CATEGORIES, _DISH_BY_ID_NO_JOIN):
                try:
                    row = await conn.fetchrow(sql, dish_id)
                    if not row:
                        return None
                    out = [dict(row)]
                    await self._enrich_dishes_with_volume_options(out)
                    return out[0]
                except (UndefinedTableError, UndefinedColumnError) as e:
                    last = e
                    continue
            if last:
                raise last
            return None

    async def _enrich_dishes_with_volume_options(self, rows: List[Dict[str, Any]]) -> None:
        if not rows:
            return
        ids = [r["id"] for r in rows if r.get("id") is not None]
        if not ids:
            for r in rows:
                r["volume_options"] = []
            return
        opts = []
        try:
            async with self.pool.acquire() as conn:
                opts = await conn.fetch(
                    """
                    SELECT id, dish_id, volume_ml, price, sort_order
                    FROM dish_volume_options
                    WHERE dish_id = ANY($1::int[])
                    ORDER BY sort_order, volume_ml, id
                    """,
                    ids,
                )
        except UndefinedTableError:
            for r in rows:
                r["volume_options"] = []
            return
        by_dish: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
        for o in opts:
            by_dish[o["dish_id"]].append(
                {
                    "id": o["id"],
                    "volume_ml": o["volume_ml"],
                    "price": o["price"],
                    "sort_order": o["sort_order"],
                }
            )
        for r in rows:
            r["volume_options"] = by_dish.get(r["id"], [])

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
                    out = [dict(row) for row in rows]
                    await self._enrich_dishes_with_volume_options(out)
                    return out
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
                out = [dict(row) for row in rows]
                await self._enrich_dishes_with_volume_options(out)
                return out
            except (UndefinedTableError, UndefinedColumnError):
                return await self.get_all()

    async def _delete_volume_options(self, conn, dish_id: int) -> None:
        try:
            await conn.execute("DELETE FROM dish_volume_options WHERE dish_id = $1", dish_id)
        except UndefinedTableError:
            pass

    async def _insert_volume_options(self, conn, dish_id: int, options: List[Dict[str, Any]]) -> None:
        if not options:
            return
        for o in options:
            await conn.execute(
                """
                INSERT INTO dish_volume_options (dish_id, volume_ml, price, sort_order)
                VALUES ($1, $2, $3, $4)
                """,
                dish_id,
                o["volume_ml"],
                o["price"],
                o["sort_order"],
            )

    async def create(self, dish_data: dict) -> int:
        data = dict(dish_data)
        opts = _normalize_volume_options(data.pop("volume_options", None) or [])
        if opts:
            data["price"] = min(x["price"] for x in opts)
            data["volume_ml"] = None
        async with self.pool.acquire() as conn:
            try:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        """
                        INSERT INTO dishes (name, price, weight_grams, volume_ml, description, calories, image_url, video_url, is_base_menu, subcategory_id)
                        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id
                        """,
                        data["name"],
                        data["price"],
                        data.get("weight_grams"),
                        data.get("volume_ml"),
                        data.get("description"),
                        data.get("calories"),
                        data.get("image_url"),
                        data.get("video_url"),
                        data.get("is_base_menu", True),
                        data.get("subcategory_id"),
                    )
                    dish_id = row["id"]
                    if opts:
                        await self._insert_volume_options(conn, dish_id, opts)
                    return dish_id
            except UndefinedTableError:
                row = await conn.fetchrow(
                    """
                    INSERT INTO dishes (name, price, weight_grams, volume_ml, description, calories, image_url, video_url, is_base_menu, subcategory_id)
                    VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10) RETURNING id
                    """,
                    data["name"],
                    data["price"],
                    data.get("weight_grams"),
                    data.get("volume_ml"),
                    data.get("description"),
                    data.get("calories"),
                    data.get("image_url"),
                    data.get("video_url"),
                    data.get("is_base_menu", True),
                    data.get("subcategory_id"),
                )
                return row["id"]

    async def update(self, dish_id: int, dish_data: dict) -> bool:
        data = dict(dish_data)
        opts = _normalize_volume_options(data.pop("volume_options", None) or [])
        if opts:
            data["price"] = min(x["price"] for x in opts)
            data["volume_ml"] = None
        async with self.pool.acquire() as conn:
            try:
                async with conn.transaction():
                    row = await conn.fetchrow(
                        """
                        UPDATE dishes
                        SET
                            name = $2,
                            price = $3,
                            weight_grams = $4,
                            volume_ml = $5,
                            description = $6,
                            calories = $7,
                            image_url = $8,
                            video_url = $9,
                            is_base_menu = $10,
                            subcategory_id = $11
                        WHERE id = $1
                        RETURNING id
                        """,
                        dish_id,
                        data["name"],
                        data["price"],
                        data.get("weight_grams"),
                        data.get("volume_ml"),
                        data.get("description"),
                        data.get("calories"),
                        data.get("image_url"),
                        data.get("video_url"),
                        data.get("is_base_menu", True),
                        data.get("subcategory_id"),
                    )
                    if row is None:
                        return False
                    await self._delete_volume_options(conn, dish_id)
                    if opts:
                        await self._insert_volume_options(conn, dish_id, opts)
                    return True
            except UndefinedTableError:
                row = await conn.fetchrow(
                    """
                    UPDATE dishes
                    SET
                        name = $2,
                        price = $3,
                        weight_grams = $4,
                        volume_ml = $5,
                        description = $6,
                        calories = $7,
                        image_url = $8,
                        video_url = $9,
                        is_base_menu = $10,
                        subcategory_id = $11
                    WHERE id = $1
                    RETURNING id
                    """,
                    dish_id,
                    data["name"],
                    data["price"],
                    data.get("weight_grams"),
                    data.get("volume_ml"),
                    data.get("description"),
                    data.get("calories"),
                    data.get("image_url"),
                    data.get("video_url"),
                    data.get("is_base_menu", True),
                    data.get("subcategory_id"),
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

    async def delete_season(self, season_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM menu_seasons WHERE id = $1", season_id)
            return result.endswith("1")

    async def list_dishes_by_season(self, season_id: int) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    d.id,
                    d.name,
                    d.price,
                    d.weight_grams,
                    d.volume_ml,
                    d.description,
                    d.calories,
                    d.image_url,
                    d.video_url,
                    d.is_base_menu,
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
            out = [dict(row) for row in rows]
            await self._enrich_dishes_with_volume_options(out)
            return out

    async def get_base_menu_items(self) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            try:
                rows = await conn.fetch(_SQL_BASE_MENU_WITH_CATEGORIES)
                out = [dict(row) for row in rows]
                await self._enrich_dishes_with_volume_options(out)
                return out
            except (UndefinedTableError, UndefinedColumnError):
                # Совместимость со старыми БД без is_base_menu: считаем все базовыми.
                return await self.get_all()

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
