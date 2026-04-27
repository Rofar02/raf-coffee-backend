BEGIN;

CREATE TABLE IF NOT EXISTS vacancy_settings (
    id INTEGER PRIMARY KEY CHECK (id = 1),
    show_on_homepage BOOLEAN NOT NULL DEFAULT FALSE
);

INSERT INTO vacancy_settings (id, show_on_homepage)
VALUES (1, FALSE)
ON CONFLICT (id) DO NOTHING;

CREATE TABLE IF NOT EXISTS vacancies (
    id SERIAL PRIMARY KEY,
    title VARCHAR(160) NOT NULL,
    city VARCHAR(120),
    branch VARCHAR(160),
    description TEXT,
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS vacancy_applications (
    id SERIAL PRIMARY KEY,
    vacancy_id INTEGER NOT NULL REFERENCES vacancies(id) ON DELETE CASCADE,
    full_name VARCHAR(160) NOT NULL,
    phone VARCHAR(40) NOT NULL,
    contact_email VARCHAR(254),
    contact_telegram VARCHAR(120),
    message TEXT,
    status VARCHAR(40) NOT NULL DEFAULT 'new',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_vacancies_active_sort ON vacancies(is_active, sort_order, id);
CREATE INDEX IF NOT EXISTS idx_vacancy_applications_created ON vacancy_applications(created_at DESC, id DESC);

COMMIT;
