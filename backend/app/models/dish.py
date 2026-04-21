from pydantic import BaseModel, Field
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
    category_name: str
    subcategory_name: str