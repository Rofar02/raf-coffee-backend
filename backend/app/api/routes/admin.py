from pathlib import Path
import re
from typing import List
import unicodedata
from uuid import uuid4

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from pydantic import BaseModel
from app.core.database import get_pool
from app.repositories.dish_repository import DishRepository
from app.services.menu_service import MenuService
from app.models.dish import (
    CategoryItem,
    DishCreate,
    Dish,
    DishUpdate,
    MenuItem,
    Season,
    SeasonCreate,
    SeasonUpdate,
    SeasonDishLink,
    SubcategoryCreateBody,
    SubcategoryOption,
    SubcategoryUpdateBody,
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

_CYR_TO_LAT = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d", "е": "e", "ё": "e", "ж": "zh",
    "з": "z", "и": "i", "й": "y", "к": "k", "л": "l", "м": "m", "н": "n", "о": "o",
    "п": "p", "р": "r", "с": "s", "т": "t", "у": "u", "ф": "f", "х": "h", "ц": "ts",
    "ч": "ch", "ш": "sh", "щ": "sch", "ъ": "", "ы": "y", "ь": "", "э": "e", "ю": "yu", "я": "ya",
}


class SeasonDishAttachPayload(BaseModel):
    sort_order: int = 0
    is_visible: bool = True


def _slugify(value: str) -> str:
    raw = (value or "").strip().lower()
    translit = "".join(_CYR_TO_LAT.get(ch, ch) for ch in raw)
    normalized = unicodedata.normalize("NFKD", translit).encode("ascii", "ignore").decode("ascii")
    slug = re.sub(r"[^a-z0-9]+", "-", normalized).strip("-")
    return slug or "season"


@router.get("/subcategories", response_model=List[SubcategoryOption])
async def list_subcategories(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    return await repo.list_subcategories()


@router.get("/categories", response_model=List[CategoryItem])
async def list_categories(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    rows = await repo.list_categories()
    return [CategoryItem(**r) for r in rows]


@router.post("/flush-menu-cache")
async def admin_flush_menu_cache(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    """Сбрасывает Redis-кеш публичного меню. Нужен после ручного SQL в PostgreSQL (кэш иначе до 5 мин)."""
    repo = DishRepository(pool)
    service = MenuService(repo)
    await service.clear_menu_cache()
    return {"ok": True}


@router.post("/subcategories", response_model=SubcategoryOption)
async def create_subcategory(
    body: SubcategoryCreateBody,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    cat = await repo.get_category_by_id(body.category_id)
    if not cat:
        raise HTTPException(status_code=400, detail="Category not found")
    row = await repo.create_subcategory(body.category_id, body.name, body.sort_order)
    return SubcategoryOption(**row)


@router.put("/subcategories/{subcategory_id}", response_model=SubcategoryOption)
async def update_subcategory(
    subcategory_id: int,
    body: SubcategoryUpdateBody,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    data = body.model_dump(exclude_none=True)
    if not data:
        raise HTTPException(status_code=400, detail="No fields to update")
    if data.get("category_id") is not None:
        cat = await repo.get_category_by_id(int(data["category_id"]))
        if not cat:
            raise HTTPException(status_code=400, detail="Category not found")
    ok = await repo.update_subcategory(
        subcategory_id,
        data.get("category_id"),
        data.get("name"),
        data.get("sort_order"),
    )
    if not ok:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    out = await repo.get_subcategory_by_id(subcategory_id)
    if not out:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return SubcategoryOption(**out)


@router.delete("/subcategories/{subcategory_id}")
async def delete_subcategory(
    subcategory_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    deleted = await repo.delete_subcategory(subcategory_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Subcategory not found")
    return {"ok": True, "deleted_id": subcategory_id}


@router.post("/dishes", response_model=MenuItem)
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
    out = await repo.get_dish_by_id(dish_id)
    if not out:
        raise HTTPException(status_code=500, detail="Dish not found after create")
    return MenuItem(**out)


@router.get("/dishes", response_model=List[MenuItem])
async def list_dishes(
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    return await repo.get_all()


@router.put("/dishes/{dish_id}", response_model=MenuItem)
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
    out = await repo.get_dish_by_id(dish_id)
    if not out:
        raise HTTPException(status_code=404, detail="Dish not found")
    return MenuItem(**out)


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
    payload = season.model_dump()
    existing = await service.list_seasons()
    existing_slugs = {str(row.get("slug") or "").strip().lower() for row in existing}

    base_slug = _slugify(payload.get("slug") or payload.get("name") or "season")
    final_slug = base_slug
    idx = 2
    while final_slug in existing_slugs:
        final_slug = f"{base_slug}-{idx}"
        idx += 1
    payload["slug"] = final_slug

    created = await service.create_season(payload)
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


@router.delete("/seasons/{season_id}")
async def delete_season(
    season_id: int,
    _: str = Depends(verify_admin_token),
    pool=Depends(get_pool),
):
    repo = DishRepository(pool)
    service = MenuService(repo)
    result = await service.delete_season(season_id)
    if not result.get("ok"):
        reason = result.get("reason")
        if reason == "last_season":
            raise HTTPException(status_code=400, detail="Cannot delete last season")
        raise HTTPException(status_code=404, detail="Season not found")
    return {"ok": True, "deleted_season_id": season_id}


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