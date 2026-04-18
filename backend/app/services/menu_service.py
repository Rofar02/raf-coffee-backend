import json
from ..repositories.dish_repository import DishRepository
from ..core.redis_client import get_redis

class MenuService:
    def __init__(self, repo: DishRepository):
        self.repo = repo
        self.redis = get_redis()

    async def get_menu(self):
        # Проверяем кэш
        cached = self.redis.get("menu")
        if cached:
            return json.loads(cached)

        # Кэш пуст — идём в БД
        dishes = await self.repo.get_all()
        self.redis.setex("menu", 300, json.dumps(dishes))
        return dishes