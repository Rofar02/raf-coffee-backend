from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional

class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0)
    weight_grams: Optional[int] = Field(None, ge=0, le=99999, title="Вес порции, г")
    description: Optional[str] = Field(None, max_length=1000)
    calories: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    subcategory_id: Optional[int] = None

class DishCreate(DishBase):
    pass


class DishUpdate(DishBase):
    pass

class Dish(DishBase):
    id: int


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


class SeasonBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    slug: str = Field(..., min_length=1, max_length=120)
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