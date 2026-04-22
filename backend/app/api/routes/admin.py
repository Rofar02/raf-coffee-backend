from pathlib import Path
from typing import List
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from app.core.database import get_pool
from app.repositories.dish_repository import DishRepository
from app.services.menu_service import MenuService
from app.models.dish import (
    DishCreate,
    Dish,
    DishUpdate,
    MenuItem,
    Season,
    SeasonCreate,
    SeasonUpdate,
    SeasonDishLink,
    SubcategoryOption,
)
from app.core.auth import verify_admin_token

router = APIRouter(prefix="/admin", tags=["admin"])
_UPLOADS_DIR = Path("static") / "uploads"
_ALLOWED_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp", "image/gif"}
_ALLOWED_VIDEO_TYPES = {"video/mp4", "video/webm", "video/quicktime"}
_EXT_BY_CONTENT_TYPE = {
    "image/jpeg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
    "image/gif": ".gif",
    "video/mp4": ".mp4",
    "video/webm": ".webm",
    "video/quicktime": ".mov",
}


class SeasonDishAttachPayload(BaseModel):
    sort_order: int = 0
    is_visible: bool = True


@router.get("/subcategories", response_model=List[SubcategoryOption])
async def list_subcategories(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    return await repo.list_subcategories()


@router.post("/dishes")
async def add_dish(
    dish: DishCreate,
    season_id: int | None = None,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    data = dish.model_dump()
    dish_id = await service.add_dish(data)
    if season_id is not None:
        await service.attach_dish_to_season(season_id=season_id, dish_id=dish_id)
    return Dish(id=dish_id, **data)


@router.get("/dishes", response_model=List[MenuItem])
async def list_dishes(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    return await repo.get_all()


@router.put("/dishes/{dish_id}", response_model=Dish)
async def update_dish(
    dish_id: int,
    dish: DishUpdate,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    data = dish.model_dump()
    updated = await service.update_dish(dish_id, data)
    if not updated:
        raise HTTPException(status_code=404, detail="Dish not found")
    return Dish(id=dish_id, **data)


@router.delete("/dishes/{dish_id}")
async def delete_dish(
    dish_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    deleted = await service.delete_dish(dish_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Dish not found")
    return {"ok": True, "deleted_id": dish_id}


@router.get("/seasons", response_model=List[Season])
async def list_seasons(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    return await service.list_seasons()


@router.post("/seasons", response_model=Season)
async def create_season(
    season: SeasonCreate,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    created = await service.create_season(season.model_dump())
    return Season(**created)


@router.put("/seasons/{season_id}", response_model=Season)
async def update_season(
    season_id: int,
    season: SeasonUpdate,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    updated = await service.update_season(season_id, season.model_dump(exclude_none=True))
    if not updated:
        raise HTTPException(status_code=404, detail="Season not found")
    return Season(**updated)


@router.post("/seasons/{season_id}/activate")
async def activate_season(
    season_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    ok = await service.set_active_season(season_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Season not found")
    return {"ok": True, "active_season_id": season_id}


@router.get("/seasons/{season_id}/dishes", response_model=List[MenuItem])
async def list_season_dishes(
    season_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    return await service.list_dishes_by_season(season_id)


@router.post("/seasons/{season_id}/dishes/{dish_id}", response_model=SeasonDishLink)
async def attach_dish_to_season(
    season_id: int,
    dish_id: int,
    payload: SeasonDishAttachPayload = SeasonDishAttachPayload(),
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    ok = await service.attach_dish_to_season(
        season_id=season_id,
        dish_id=dish_id,
        sort_order=payload.sort_order,
        is_visible=payload.is_visible,
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Season or dish not found")
    return SeasonDishLink(
        season_id=season_id,
        dish_id=dish_id,
        sort_order=payload.sort_order,
        is_visible=payload.is_visible,
    )


@router.delete("/seasons/{season_id}/dishes/{dish_id}")
async def detach_dish_from_season(
    season_id: int,
    dish_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    ok = await service.detach_dish_from_season(season_id=season_id, dish_id=dish_id)
    if not ok:
        raise HTTPException(status_code=404, detail="Season-dish link not found")
    return {"ok": True, "season_id": season_id, "dish_id": dish_id}


@router.post("/upload")
async def upload_media(
    file: UploadFile = File(...),
    _: str = Depends(verify_admin_token),
):
    content_type = (file.content_type or "").lower()
    if content_type in _ALLOWED_IMAGE_TYPES:
        kind = "images"
        ext = _EXT_BY_CONTENT_TYPE[content_type]
    elif content_type in _ALLOWED_VIDEO_TYPES:
        kind = "videos"
        ext = _EXT_BY_CONTENT_TYPE[content_type]
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type")

    target_dir = _UPLOADS_DIR / kind
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid4().hex}{ext}"
    target_path = target_dir / filename

    payload = await file.read()
    if not payload:
        raise HTTPException(status_code=400, detail="Empty file")
    if len(payload) > 60 * 1024 * 1024:
        raise HTTPException(status_code=413, detail="File too large")

    target_path.write_bytes(payload)
    return {"url": f"/static/uploads/{kind}/{filename}", "content_type": content_type}