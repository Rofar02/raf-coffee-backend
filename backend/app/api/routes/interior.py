from fastapi import APIRouter, Depends

from app.core.database import get_pool
from app.models.interior import InteriorGallery
from app.repositories.interior_repository import InteriorRepository

router = APIRouter(prefix="/api/interior", tags=["interior"])


@router.get("", response_model=list[InteriorGallery])
@router.get("/", response_model=list[InteriorGallery])
async def get_interiors(pool=Depends(get_pool)):
    repo = InteriorRepository(pool)
    return await repo.list_all()
