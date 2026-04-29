from pathlib import Path
from uuid import uuid4
from typing import Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile

from app.core.database import get_pool
from app.models.vacancy import VacancyApplyRequest, VacancyApplyResponse, VacancyPublicList
from app.repositories.vacancy_repository import VacancyRepository
from app.services.vacancy_service import VacancyService

router = APIRouter(prefix="/api/vacancies", tags=["vacancies"])
_VACANCY_RESUME_DIR = Path("static") / "uploads" / "resumes"
_MAX_RESUME_SIZE_BYTES = 10 * 1024 * 1024


@router.get("", response_model=VacancyPublicList)
@router.get("/", response_model=VacancyPublicList)
async def get_vacancies(pool=Depends(get_pool)):
    repo = VacancyRepository(pool)
    service = VacancyService(repo)
    payload = await service.get_public_payload()
    return VacancyPublicList(**payload)


@router.post("/apply", response_model=VacancyApplyResponse)
async def apply_vacancy(
    vacancy_id: int = Form(...),
    full_name: str = Form(...),
    phone: str = Form(...),
    contact_email: Optional[str] = Form(None),
    contact_telegram: Optional[str] = Form(None),
    message: Optional[str] = Form(None),
    consent: bool = Form(...),
    resume_pdf: Optional[UploadFile] = File(None),
    pool=Depends(get_pool),
):
    body = VacancyApplyRequest(
        vacancy_id=vacancy_id,
        full_name=full_name,
        phone=phone,
        contact_email=(contact_email or None),
        contact_telegram=(contact_telegram or None),
        message=(message or None),
        consent=consent,
    )
    if not body.consent:
        raise HTTPException(status_code=400, detail="Consent is required")

    payload = body.model_dump()
    if resume_pdf and (resume_pdf.filename or "").strip():
        filename = (resume_pdf.filename or "").strip()
        if not filename.lower().endswith(".pdf"):
            raise HTTPException(status_code=400, detail="Resume must be a PDF file")

        content = await resume_pdf.read()
        if not content:
            raise HTTPException(status_code=400, detail="Resume file is empty")
        if len(content) > _MAX_RESUME_SIZE_BYTES:
            raise HTTPException(status_code=413, detail="Resume file too large (max 10MB)")

        if not content.startswith(b"%PDF-"):
            raise HTTPException(status_code=400, detail="Invalid PDF file")

        _VACANCY_RESUME_DIR.mkdir(parents=True, exist_ok=True)
        stored_name = f"{uuid4().hex}.pdf"
        stored_path = _VACANCY_RESUME_DIR / stored_name
        stored_path.write_bytes(content)
        resume_url = f"/static/uploads/resumes/{stored_name}"

        base_message = (payload.get("message") or "").strip()
        resume_line = f"Резюме PDF: {resume_url}"
        payload["message"] = f"{base_message}\n\n{resume_line}" if base_message else resume_line

    repo = VacancyRepository(pool)
    service = VacancyService(repo)
    try:
        app, email_sent = await service.apply(payload)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return VacancyApplyResponse(ok=True, application_id=int(app["id"]), email_sent=email_sent)
