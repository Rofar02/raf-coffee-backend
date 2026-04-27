from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class VacancyBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=160)
    city: Optional[str] = Field(None, max_length=120)
    branch: Optional[str] = Field(None, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: bool = True
    sort_order: int = Field(0, ge=0, le=9999)


class VacancyCreate(VacancyBase):
    pass


class VacancyUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=160)
    city: Optional[str] = Field(None, max_length=120)
    branch: Optional[str] = Field(None, max_length=160)
    description: Optional[str] = Field(None, max_length=2000)
    is_active: Optional[bool] = None
    sort_order: Optional[int] = Field(None, ge=0, le=9999)


class Vacancy(VacancyBase):
    id: int
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class VacancySettings(BaseModel):
    show_on_homepage: bool = False


class VacancySettingsUpdate(BaseModel):
    show_on_homepage: bool


class VacancyPublicList(BaseModel):
    enabled: bool
    vacancies: List[Vacancy] = Field(default_factory=list)


class VacancyApplyRequest(BaseModel):
    vacancy_id: int = Field(..., ge=1)
    full_name: str = Field(..., min_length=2, max_length=160)
    phone: str = Field(..., min_length=5, max_length=40)
    contact_email: Optional[str] = Field(None, max_length=254)
    contact_telegram: Optional[str] = Field(None, max_length=120)
    message: Optional[str] = Field(None, max_length=3000)
    consent: bool = Field(...)


class VacancyApplyResponse(BaseModel):
    ok: bool
    application_id: int
    email_sent: bool


class VacancyApplication(BaseModel):
    id: int
    vacancy_id: int
    vacancy_title: Optional[str] = None
    full_name: str
    phone: str
    contact_email: Optional[str] = None
    contact_telegram: Optional[str] = None
    message: Optional[str] = None
    status: str = "new"
    created_at: datetime
