from fastapi import APIRouter, Depends
from typing import List
from ....core.database import get_pool
from ....repositories.dish_repository import DishRepository
from ....services.menu_service import MenuService
from ....models.dish import Dish

router = APIRouter(prefix="/menu", tags=["menu"])

@router.get("/", response_model=List[Dish])
async def get_menu(pool=Depends(get_pool)):
    repo = DishRepository(pool)
    service = MenuService(repo)
    return await service.get_menu()