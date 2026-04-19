import json
from ..repositories.dish_repository import DishRepository
from ..core.redis_client import get_redis

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
        cached = await redis.get("menu")
        if cached:
            return json.loads(cached)

        rows = await self.repo.get_all()
        menu = [dict(row) for row in rows]
        await redis.setex("menu", 300, json.dumps(menu))
        return menu

    async def add_dish(self, dish_data: dict):
        dish_id = await self.repo.create(dish_data)
        redis = await self.get_redis()
        await redis.delete("menu")
        return dish_id