from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional


class VolumeOptionIn(BaseModel):
    """Вариант объёма при создании/редактировании (без id)."""

    volume_ml: int = Field(..., ge=0, le=2000)
    price: int = Field(..., ge=0)
    sort_order: int = Field(0, ge=0, le=9999)
    nutrition_kcal: Optional[str] = None
    nutrition_bju: Optional[str] = None


class VolumeOption(BaseModel):
    """Сохранённый вариант (отдаётся в API)."""

    id: Optional[int] = None
    volume_ml: int = Field(..., ge=0, le=2000)
    price: int = Field(..., ge=0)
    sort_order: int = Field(0, ge=0, le=9999)
    nutrition_kcal: Optional[str] = None
    nutrition_bju: Optional[str] = None


class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0)
    weight_grams: Optional[int] = Field(None, ge=0, le=99999, title="Вес порции, г")
    volume_ml: Optional[int] = Field(None, ge=0, le=2000, title="Объём напитка, мл (один вариант, если нет списка)")
    description: Optional[str] = Field(None, max_length=1000)
    calories: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    is_base_menu: bool = True
    subcategory_id: Optional[int] = None


class DishCreate(DishBase):
    volume_options: Optional[List[VolumeOptionIn]] = None
    image_urls: Optional[List[str]] = None


class DishUpdate(DishBase):
    volume_options: Optional[List[VolumeOptionIn]] = None
    image_urls: Optional[List[str]] = None


class Dish(DishBase):
    id: int
    volume_options: List[VolumeOption] = Field(default_factory=list)
    image_urls: List[str] = Field(default_factory=list, description="Все URL фото по порядку; первый == image_url")


class MenuItem(Dish):
    """Ответ GET /menu: блюдо с названиями категории и подкатегории (из JOIN)."""

    category_id: Optional[int] = None
    category_name: Optional[str] = None
    subcategory_name: Optional[str] = None


class SubcategoryOption(BaseModel):
    """Справочник для админ-формы: подкатегория внутри категории."""

    id: int
    category_id: int
    category_name: str
    subcategory_name: str
    sort_order: int = 0


class CategoryItem(BaseModel):
    id: int
    name: str
    sort_order: int


class SubcategoryCreateBody(BaseModel):
    category_id: int = Field(..., ge=1)
    name: str = Field(..., min_length=1, max_length=200)
    sort_order: int = Field(0, ge=0, le=9999)


class SubcategoryUpdateBody(BaseModel):
    category_id: Optional[int] = Field(None, ge=1)
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    sort_order: Optional[int] = Field(None, ge=0, le=9999)


class SeasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    sort_order: int = Field(0, ge=0, le=9999)


class SeasonCreate(SeasonBase):
    is_active: bool = False


class SeasonUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=120)
    slug: Optional[str] = Field(None, min_length=1, max_length=120)
    sort_order: Optional[int] = Field(None, ge=0, le=9999)


class Season(BaseModel):
    id: int
    name: str
    slug: str
    is_active: bool
    sort_order: int
    created_at: Optional[datetime] = None


class SeasonDishLink(BaseModel):
    season_id: int
    dish_id: int
    sort_order: int = 0
    is_visible: bool = True
