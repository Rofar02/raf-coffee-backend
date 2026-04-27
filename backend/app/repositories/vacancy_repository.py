from typing import Any, Dict, List, Optional

import asyncpg


class VacancyRepository:
    def __init__(self, pool: asyncpg.Pool):
        self.pool = pool

    async def get_settings(self) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT show_on_homepage
                FROM vacancy_settings
                WHERE id = 1
                """
            )
            if row:
                return dict(row)
            row = await conn.fetchrow(
                """
                INSERT INTO vacancy_settings (id, show_on_homepage)
                VALUES (1, FALSE)
                ON CONFLICT (id) DO UPDATE SET id = EXCLUDED.id
                RETURNING show_on_homepage
                """
            )
            return dict(row)

    async def update_settings(self, show_on_homepage: bool) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO vacancy_settings (id, show_on_homepage)
                VALUES (1, $1)
                ON CONFLICT (id) DO UPDATE SET show_on_homepage = EXCLUDED.show_on_homepage
                RETURNING show_on_homepage
                """,
                show_on_homepage,
            )
            return dict(row)

    async def list_vacancies(self, *, only_active: bool = False) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            if only_active:
                rows = await conn.fetch(
                    """
                    SELECT id, title, city, branch, description, is_active, sort_order, created_at, updated_at
                    FROM vacancies
                    WHERE is_active = TRUE
                    ORDER BY sort_order, id
                    """
                )
            else:
                rows = await conn.fetch(
                    """
                    SELECT id, title, city, branch, description, is_active, sort_order, created_at, updated_at
                    FROM vacancies
                    ORDER BY sort_order, id
                    """
                )
            return [dict(r) for r in rows]

    async def create_vacancy(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO vacancies (title, city, branch, description, is_active, sort_order)
                VALUES ($1, $2, $3, $4, $5, $6)
                RETURNING id, title, city, branch, description, is_active, sort_order, created_at, updated_at
                """,
                payload["title"],
                payload.get("city"),
                payload.get("branch"),
                payload.get("description"),
                payload.get("is_active", True),
                payload.get("sort_order", 0),
            )
            return dict(row)

    async def update_vacancy(self, vacancy_id: int, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                UPDATE vacancies
                SET
                    title = COALESCE($2, title),
                    city = COALESCE($3, city),
                    branch = COALESCE($4, branch),
                    description = COALESCE($5, description),
                    is_active = COALESCE($6, is_active),
                    sort_order = COALESCE($7, sort_order),
                    updated_at = NOW()
                WHERE id = $1
                RETURNING id, title, city, branch, description, is_active, sort_order, created_at, updated_at
                """,
                vacancy_id,
                payload.get("title"),
                payload.get("city"),
                payload.get("branch"),
                payload.get("description"),
                payload.get("is_active"),
                payload.get("sort_order"),
            )
            return dict(row) if row else None

    async def delete_vacancy(self, vacancy_id: int) -> bool:
        async with self.pool.acquire() as conn:
            result = await conn.execute("DELETE FROM vacancies WHERE id = $1", vacancy_id)
            return result.endswith("1")

    async def get_vacancy(self, vacancy_id: int) -> Optional[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                SELECT id, title, city, branch, description, is_active, sort_order, created_at, updated_at
                FROM vacancies
                WHERE id = $1
                """,
                vacancy_id,
            )
            return dict(row) if row else None

    async def create_application(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        async with self.pool.acquire() as conn:
            row = await conn.fetchrow(
                """
                INSERT INTO vacancy_applications
                    (vacancy_id, full_name, phone, contact_email, contact_telegram, message, status)
                VALUES ($1, $2, $3, $4, $5, $6, 'new')
                RETURNING id, vacancy_id, full_name, phone, contact_email, contact_telegram, message, status, created_at
                """,
                payload["vacancy_id"],
                payload["full_name"],
                payload["phone"],
                payload.get("contact_email"),
                payload.get("contact_telegram"),
                payload.get("message"),
            )
            return dict(row)

    async def list_applications(self, limit: int = 200) -> List[Dict[str, Any]]:
        async with self.pool.acquire() as conn:
            rows = await conn.fetch(
                """
                SELECT
                    va.id,
                    va.vacancy_id,
                    v.title AS vacancy_title,
                    va.full_name,
                    va.phone,
                    va.contact_email,
                    va.contact_telegram,
                    va.message,
                    va.status,
                    va.created_at
                FROM vacancy_applications va
                LEFT JOIN vacancies v ON v.id = va.vacancy_id
                ORDER BY va.created_at DESC, va.id DESC
                LIMIT $1
                """,
                limit,
            )
            return [dict(r) for r in rows]
