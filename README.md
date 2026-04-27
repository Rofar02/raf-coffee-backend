# Raf Coffee

Backend API для меню кофейни (FastAPI, PostgreSQL, Redis) и статическая витрина меню во **`frontend/`**.

## Запуск через Docker

Из корня репозитория:

```bash
docker compose up --build
```

- **Сайт (nginx + HTML):** http://localhost:8080 — главная; **меню:** /menu; **админка:** /admin; **документы:** /privacy, /terms (токен админки = `ADMIN_TOKEN` из compose). Старые URL `*.html` редиректят на «чистые». JSON меню: `GET /api/menu/`; админ-API: `/admin/...`; `/static/...` — как раньше.  
  Если в Chrome видите `ERR_CONNECTION_REFUSED`, откройте **http://127.0.0.1:8080** (на Windows иногда `localhost` уходит в IPv6, а порт проброшен только на IPv4).

После `docker compose up` дождитесь, пока **backend** станет healthy (фронт стартует только после этого). Проверка: в браузере откройте http://127.0.0.1:8000/ping — должен быть JSON `{"status":"ok",...}`.
- **API напрямую:** http://localhost:8000  
- Документация: http://localhost:8000/docs (через фронт также: http://localhost:8080/docs)  
- Проверка: `GET /ping`

### Фронтенд без Docker

Стили Tailwind собираются один раз после правок разметки/классов:

```bash
cd frontend && npm install && npm run build:css
```

В репозитории уже лежит сгенерированный `frontend/dist/styles.css` — для Docker достаточно `compose up`.

Шрифт бренда: положите файлы в `frontend/assets/fonts/` (имена по умолчанию — `Rafchik-Regular.woff2` или `.ttf`, см. `frontend/src/rafchik-fonts.css`), затем снова `npm run build:css` не обязателен — пути в CSS уже абсолютные `/assets/fonts/...`.

Цвета интерфейса взяты с бренд-шкалы (MATCHA `#809671`, ALMOND `#E5E0D8`, PISTACHE `#B3B792`, CHAI `#D2AB80`, CAROB `#725C3A`, VANILLA `#E5D2B8`); в Tailwind доступны как `coffee-*` и как `brand-matcha`, `brand-carob` и т.д. Референс скопирован в `frontend/assets/brand-colors-ref.jpg`.

Поднимите API (`uvicorn` в `backend/`), откройте страницу через **http://** (например `npx serve frontend` или тот же nginx локально). Файл `index.html` с диска (`file://`) к API не подключается — либо `http://localhost:8080` после compose, либо `<meta name="api-base" content="http://127.0.0.1:8000">` и статический сервер (CORS в `main.py` уже настроен).

При **первом** создании тома PostgreSQL выполняется `backend/sql/init.sql` (таблицы; категории **Кухня** и **Напитки** без демо-рубрик; один базовый сезон). Рубрики добавляете в админке.

Уже есть данные, но нужны новые рубрики: выполните в БД `backend/sql/reseed_menu_categories.sql` (связи блюд с подкатегориями обнулятся — выставите заново в админке) или пересоздайте том `postgres_data`.

Колонка **веса порции** (`weight_grams`): для существующей БД выполните `backend/sql/migrate_add_weight_grams.sql` (или пересоздайте том — в `init.sql` колонка уже есть).

Вакансии/отклики для существующей БД: выполните `backend/sql/migrate_add_vacancies.sql`.

Переменные окружения backend:

| Переменная     | Описание |
|----------------|----------|
| `DATABASE_URL` | Строка подключения к PostgreSQL |
| `REDIS_URL`    | Строка подключения к Redis |
| `ADMIN_TOKEN`  | Секрет для заголовка `X-Admin-Token` на админ-роутах |
| `SMTP_HOST` / `SMTP_PORT` / `SMTP_USER` / `SMTP_PASSWORD` | SMTP для отправки откликов по вакансиям |
| `SMTP_FROM` | Адрес отправителя писем по вакансиям |
| `VACANCY_EMAIL_TO` | Куда отправлять отклики по вакансиям |
| `SMTP_USE_TLS` | Использовать STARTTLS (`true/false`) |

В `docker-compose.yml` заданы значения по умолчанию для локальной разработки; для продакшена задайте свои секреты (в т.ч. `ADMIN_TOKEN`).

## Локальная разработка без Docker

1. Python 3.12+, установите зависимости: `poetry install` (из каталога `backend`).
2. Поднимите PostgreSQL и Redis (или используйте только compose для БД).
3. Скопируйте `backend/.env.example` в `backend/.env` и поправьте значения.
4. Выполните SQL из `backend/sql/init.sql` в вашей базе.
5. Запуск: `uvicorn app.main:app --reload` из каталога `backend`.

## Админ API

`POST /admin/dishes` — заголовок `X-Admin-Token: <ADMIN_TOKEN>`, тело JSON по схеме блюда (см. `/docs`).

`POST /admin/import-xlsx` — импорт меню из `.xlsx` (multipart upload, заголовок `X-Admin-Token`).
В админке это доступно в разделе «Токен и доступ» через кнопку «Импорт XLSX».

`GET/PUT /admin/vacancies/settings`, `GET/POST/PUT/DELETE /admin/vacancies`, `GET /admin/vacancy-applications` — управление блоком вакансий, позициями и откликами (вкладка «Вакансии» в админке).

Публичные эндпоинты вакансий:
- `GET /api/vacancies` — настройки показа + активные вакансии для главной.
- `POST /api/vacancies/apply` — отправка отклика (сохранение в БД; email отправляется при настроенном SMTP).

Минимальные колонки:
- `name` (или `название`)
- `price` (или `цена`) **или** `volume_options` в формате `250:220;350:260`

Также поддерживаются ваши названия колонок:
- `наименование` -> `name`
- `вес - объем` -> используется как вес для кухни и как объем для напитков (по колонке категории)
- `состав` -> `description`
- `калорийность` -> `calories`
- `бжус` -> добавляется в `calories` как `БЖУ: ...`

Как связать с подкатегорией:
- либо `subcategory_id`
- либо `category` + `subcategory` (если их нет, создаются автоматически)

Пример:

```bash
curl -X POST "http://127.0.0.1:8000/admin/import-xlsx" \
  -H "X-Admin-Token: YOUR_ADMIN_TOKEN" \
  -F "file=@menu.xlsx"
```

Строгий режим (по умолчанию включен): `?strict=true` — если в файле есть ошибки, импорт не применится.
