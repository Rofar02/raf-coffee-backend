from pydantic import BaseModel
from typing import Optional

class Dish(BaseModel):
    id: int
    name: str
    price: int
    description: Optional[str] = None
    calories: Optional[str] = None
    image_url: Optional[str] = None

class DishCreate(BaseModel):
    name: str
    price: int
    description: Optional[str] = None
    calories: Optional[str] = None
    image_url: Optional[str] = None