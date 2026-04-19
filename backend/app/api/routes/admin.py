from fastapi import APIRouter, Depends
from app.core.database import get_pool
from app.repositories.dish_repository import DishRepository
from app.services.menu_service import MenuService
from app.models.dish import DishCreate, Dish
from app.core.auth import verify_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])

@router.post("/dishes", dependencies=[Depends(verify_admin_token)])
async def add_dish(dish: DishCreate, pool=Depends(get_pool)):
    repo = DishRepository(pool)
    service = MenuService(repo)
    data = dish.model_dump()
    dish_id = await service.add_dish(data)
    return Dish(id=dish_id, **data)