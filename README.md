# Raf Coffee

Backend API для меню кофейни (FastAPI, PostgreSQL, Redis).

## Запуск через Docker

Из корня репозитория:

```bash
docker compose up --build
```

- API: http://localhost:8000  
- Документация: http://localhost:8000/docs  
- Проверка: `GET /ping`

При **первом** создании тома PostgreSQL выполняется `backend/sql/init.sql` (таблица `dishes`). Если том уже был без этой схемы, выполните вручную `backend/sql/init.sql` и при необходимости `backend/sql/migrate_add_subcategory_id.sql`, либо удалите том `postgres_data` и поднимите заново.

Переменные окружения backend:

| Переменная     | Описание |
|----------------|----------|
| `DATABASE_URL` | Строка подключения к PostgreSQL |
| `REDIS_URL`    | Строка подключения к Redis |
| `ADMIN_TOKEN`  | Секрет для заголовка `X-Admin-Token` на админ-роутах |

В `docker-compose.yml` заданы значения по умолчанию для локальной разработки; для продакшена задайте свои секреты (в т.ч. `ADMIN_TOKEN`).

## Локальная разработка без Docker

1. Python 3.12+, установите зависимости: `poetry install` (из каталога `backend`).
2. Поднимите PostgreSQL и Redis (или используйте только compose для БД).
3. Скопируйте `backend/.env.example` в `backend/.env` и поправьте значения.
4. Выполните SQL из `backend/sql/init.sql` в вашей базе.
5. Запуск: `uvicorn app.main:app --reload` из каталога `backend`.

## Админ API

`POST /admin/dishes` — заголовок `X-Admin-Token: <ADMIN_TOKEN>`, тело JSON по схеме блюда (см. `/docs`).
