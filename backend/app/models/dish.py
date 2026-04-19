from pydantic import BaseModel, Field
from typing import Optional

class DishBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    price: int = Field(..., ge=0)
    description: Optional[str] = Field(None, max_length=1000)
    calories: Optional[str] = None
    image_url: Optional[str] = None
    video_url: Optional[str] = None
    subcategory_id: Optional[int] = None

class DishCreate(DishBase):
    pass

class Dish(DishBase):
    id: int