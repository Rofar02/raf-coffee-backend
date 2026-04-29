from __future__ import annotations

import asyncio
import smtplib
from email.message import EmailMessage
from typing import Any, Dict, List, Optional, Tuple

from app.core.config import get_settings
from app.repositories.vacancy_repository import VacancyRepository


class VacancyService:
    def __init__(self, repo: VacancyRepository):
        self.repo = repo
        self.settings = get_settings()

    async def get_public_payload(self) -> Dict[str, Any]:
        settings = await self.repo.get_settings()
        enabled = bool(settings.get("show_on_homepage", False))
        vacancies = await self.repo.list_vacancies(only_active=True) if enabled else []
        return {"enabled": enabled, "vacancies": vacancies}

    async def list_vacancies(self) -> List[Dict[str, Any]]:
        return await self.repo.list_vacancies(only_active=False)

    async def create_vacancy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        return await self.repo.create_vacancy(payload)

    async def update_vacancy(self, vacancy_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        return await self.repo.update_vacancy(vacancy_id, payload)

    async def delete_vacancy(self, vacancy_id: int) -> bool:
        return await self.repo.delete_vacancy(vacancy_id)

    async def get_settings(self) -> Dict[str, Any]:
        return await self.repo.get_settings()

    async def update_settings(self, show_on_homepage: bool) -> Dict[str, Any]:
        return await self.repo.update_settings(show_on_homepage)

    async def list_applications(self, limit: int = 200) -> List[Dict[str, Any]]:
        return await self.repo.list_applications(limit=limit)

    async def apply(self, payload: Dict[str, Any]) -> Tuple[Dict[str, Any], bool]:
        vacancy = await self.repo.get_vacancy(int(payload["vacancy_id"]))
        if not vacancy or not vacancy.get("is_active", False):
            raise ValueError("Vacancy not found or inactive")
        app = await self.repo.create_application(payload)
        # SMTP отправка делается синхронно и может заметно тормозить запрос.
        # Чтобы UI не ждал 1-3+ секунды, отправляем письмо "в фоне" и возвращаемся сразу.
        email_sent = False

        async def _fire_and_forget() -> None:
            try:
                await asyncio.to_thread(self._send_application_email, vacancy=vacancy, application=app)
            except Exception:
                # Ошибки email отправки не должны ломать пользовательский UX.
                return

        try:
            asyncio.create_task(_fire_and_forget())
        except RuntimeError:
            # На случай, если этот код вызовут без active event loop.
            try:
                self._send_application_email(vacancy=vacancy, application=app)
            except Exception:
                pass

        return app, email_sent

    def _send_application_email(self, *, vacancy: Dict[str, Any], application: Dict[str, Any]) -> bool:
        smtp_host = (self.settings.SMTP_HOST or "").strip()
        smtp_to = (self.settings.VACANCY_EMAIL_TO or "").strip()
        smtp_from = (self.settings.SMTP_FROM or "").strip()
        if not smtp_host or not smtp_to or not smtp_from:
            return False

        msg = EmailMessage()
        msg["Subject"] = f"Новая заявка на вакансию: {vacancy.get('title', 'Без названия')}"
        msg["From"] = smtp_from
        msg["To"] = smtp_to

        body = [
            "Новая заявка с сайта Raf Coffee",
            "",
            f"Вакансия: {vacancy.get('title')}",
            f"Город/филиал: {vacancy.get('city') or '-'} / {vacancy.get('branch') or '-'}",
            "",
            f"Имя: {application.get('full_name')}",
            f"Телефон: {application.get('phone')}",
            f"Email: {application.get('contact_email') or '-'}",
            f"Telegram: {application.get('contact_telegram') or '-'}",
            "",
            "Комментарий:",
            application.get("message") or "-",
            "",
            f"ID заявки: {application.get('id')}",
        ]
        msg.set_content("\n".join(body))

        try:
            port = int(self.settings.SMTP_PORT or 587)
            use_tls = bool(self.settings.SMTP_USE_TLS)
            user = (self.settings.SMTP_USER or "").strip()
            pwd = self.settings.SMTP_PASSWORD or ""

            with smtplib.SMTP(host=smtp_host, port=port, timeout=10) as client:
                if use_tls:
                    client.starttls()
                if user:
                    client.login(user, pwd)
                client.send_message(msg)
            return True
        except Exception:
            return False
