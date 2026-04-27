from fastapi import APIRouter, Depends, HTTPException

from app.core.database import get_pool
from app.models.vacancy import VacancyApplyRequest, VacancyApplyResponse, VacancyPublicList
from app.repositories.vacancy_repository import VacancyRepository
from app.services.vacancy_service import VacancyService

router = APIRouter(prefix="/api/vacancies", tags=["vacancies"])


@router.get("", response_model=VacancyPublicList)
@router.get("/", response_model=VacancyPublicList)
async def get_vacancies(pool=Depends(get_pool)):
    repo = VacancyRepository(pool)
    service = VacancyService(repo)
    payload = await service.get_public_payload()
    return VacancyPublicList(**payload)


@router.post("/apply", response_model=VacancyApplyResponse)
async def apply_vacancy(body: VacancyApplyRequest, pool=Depends(get_pool)):
    if not body.consent:
        raise HTTPException(status_code=400, detail="Consent is required")
    repo = VacancyRepository(pool)
    service = VacancyService(repo)
    try:
        app, email_sent = await service.apply(body.model_dump())
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VacancyApplyResponse(ok=True, application_id=int(app["id"]), email_sent=email_sent)
