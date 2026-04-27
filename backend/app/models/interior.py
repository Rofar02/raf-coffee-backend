from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class InteriorGallery(BaseModel):
    slug: str = Field(..., min_length=1, max_length=80)
    title: str = Field(..., min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=3000)
    images: List[str] = Field(default_factory=list)
    updated_at: Optional[datetime] = None


class InteriorGalleryUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=160)
    description: Optional[str] = Field(None, max_length=3000)
    images: Optional[List[str]] = None
