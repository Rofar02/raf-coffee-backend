import json
from decimal import Decimal

from ..repositories.dish_repository import DishRepository
from ..core.redis_client import get_redis

MENU_CACHE_KEY = "menu:v3"


def _json_default(obj):
    if isinstance(obj, Decimal):
        return int(obj) if obj % 1 == 0 else float(obj)
    raise TypeError(f"Object of type {type(obj)} is not JSON serializable")


class MenuService:
    def __init__(self, repo: DishRepository):
        self.repo = repo
        self.redis = None  # временно

    async def get_redis(self):
        if self.redis is None:
            self.redis = await get_redis()
        return self.redis

    async def get_menu(self):
        redis = await self.get_redis()
        cached = await redis.get(MENU_CACHE_KEY)
        if cached:
            return json.loads(cached)

        rows = await self.repo.get_menu_items_for_active_season()
        menu = [dict(row) for row in rows]
        await redis.setex(MENU_CACHE_KEY, 300, json.dumps(menu, default=_json_default))
        return menu

    async def add_dish(self, dish_data: dict):
        dish_id = await self.repo.create(dish_data)
        await self.clear_menu_cache()
        return dish_id

    async def update_dish(self, dish_id: int, dish_data: dict):
        updated = await self.repo.update(dish_id, dish_data)
        if updated:
            await self.clear_menu_cache()
        return updated

    async def delete_dish(self, dish_id: int):
        deleted = await self.repo.delete(dish_id)
        if deleted:
            await self.clear_menu_cache()
        return deleted

    async def clear_menu_cache(self):
        redis = await self.get_redis()
        await redis.delete(MENU_CACHE_KEY)
        await redis.delete("menu")

    async def list_seasons(self):
        return await self.repo.list_seasons()

    async def create_season(self, season_data: dict):
        created = await self.repo.create_season(season_data)
        if created.get("is_active"):
            await self.repo.set_active_season(created["id"])
        await self.clear_menu_cache()
        return created

    async def update_season(self, season_id: int, payload: dict):
        updated = await self.repo.update_season(season_id, payload)
        if updated:
            await self.clear_menu_cache()
        return updated

    async def set_active_season(self, season_id: int):
        ok = await self.repo.set_active_season(season_id)
        if ok:
            await self.clear_menu_cache()
        return ok

    async def list_dishes_by_season(self, season_id: int):
        return await self.repo.list_dishes_by_season(season_id)

    async def attach_dish_to_season(self, season_id: int, dish_id: int, sort_order: int = 0, is_visible: bool = True):
        ok = await self.repo.attach_dish_to_season(season_id, dish_id, sort_order=sort_order, is_visible=is_visible)
        if ok:
            await self.clear_menu_cache()
        return ok

    async def detach_dish_from_season(self, season_id: int, dish_id: int):
        ok = await self.repo.detach_dish_from_season(season_id, dish_id)
        if ok:
            await self.clear_menu_cache()
        return ok