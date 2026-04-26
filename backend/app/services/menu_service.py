import json
from decimal import Decimal

from ..repositories.dish_repository import DishRepository
from ..core.redis_client import get_redis

MENU_CACHE_KEY = "menu:v10"


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

        base_rows = await self.repo.get_base_menu_items()
        season_rows = await self.repo.get_menu_items_for_active_season()

        merged = {}
        for row in base_rows:
            merged[row["id"]] = dict(row)
        for row in season_rows:
            merged[row["id"]] = dict(row)

        menu = list(merged.values())
        menu.sort(
            key=lambda x: (
                9999 if x.get("category_id") is None else x.get("category_id"),
                9999 if x.get("subcategory_id") is None else x.get("subcategory_id"),
                x.get("id", 0),
            )
        )
        for row in menu:
            opts = row.get("volume_options") or []
            if opts:
                continue
            vm = row.get("volume_ml")
            if vm is not None and vm != "":
                try:
                    row["volume_options"] = [
                        {
                            "id": None,
                            "volume_ml": int(vm),
                            "price": int(row.get("price", 0)),
                            "sort_order": 0,
                            "nutrition_kcal": None,
                            "nutrition_bju": None,
                        }
                    ]
                except (TypeError, ValueError):
                    pass
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

    async def delete_season(self, season_id: int):
        seasons = await self.repo.list_seasons()
        if len(seasons) <= 1:
            return {"ok": False, "reason": "last_season"}

        target = next((s for s in seasons if s["id"] == season_id), None)
        if not target:
            return {"ok": False, "reason": "not_found"}

        if target.get("is_active"):
            replacement = next((s for s in seasons if s["id"] != season_id), None)
            if replacement:
                await self.repo.set_active_season(replacement["id"])

        deleted = await self.repo.delete_season(season_id)
        if not deleted:
            return {"ok": False, "reason": "not_found"}

        await self.clear_menu_cache()
        return {"ok": True}

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