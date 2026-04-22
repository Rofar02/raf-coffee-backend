-- Сезонность меню: отдельные сезоны и связи блюд с сезонами.
-- Скрипт безопасно запускать повторно.

BEGIN;

CREATE TABLE IF NOT EXISTS menu_seasons (
    id SERIAL PRIMARY KEY,
    name VARCHAR(120) NOT NULL,
    slug VARCHAR(120) NOT NULL UNIQUE,
    is_active BOOLEAN NOT NULL DEFAULT FALSE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS season_dishes (
    season_id INTEGER NOT NULL REFERENCES menu_seasons(id) ON DELETE CASCADE,
    dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    sort_order INTEGER NOT NULL DEFAULT 0,
    is_visible BOOLEAN NOT NULL DEFAULT TRUE,
    PRIMARY KEY (season_id, dish_id)
);

CREATE INDEX IF NOT EXISTS idx_menu_seasons_is_active ON menu_seasons(is_active);
CREATE INDEX IF NOT EXISTS idx_season_dishes_season_sort ON season_dishes(season_id, sort_order, dish_id);

-- Гарантируем, что есть хотя бы один активный сезон.
INSERT INTO menu_seasons (name, slug, is_active, sort_order)
SELECT 'Базовый сезон', 'default', TRUE, 1
WHERE NOT EXISTS (SELECT 1 FROM menu_seasons);

-- Если активного нет, активируем самый ранний по sort_order/id.
WITH first_season AS (
    SELECT id
    FROM menu_seasons
    ORDER BY sort_order, id
    LIMIT 1
)
UPDATE menu_seasons
SET is_active = CASE WHEN id = (SELECT id FROM first_season) THEN TRUE ELSE FALSE END
WHERE NOT EXISTS (SELECT 1 FROM menu_seasons WHERE is_active = TRUE);

-- Привязываем все текущие блюда к активному сезону (однократно).
WITH active_season AS (
    SELECT id
    FROM menu_seasons
    WHERE is_active = TRUE
    ORDER BY sort_order, id
    LIMIT 1
)
INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT
    (SELECT id FROM active_season),
    d.id,
    d.id,
    TRUE
FROM dishes d
WHERE (SELECT id FROM active_season) IS NOT NULL
ON CONFLICT (season_id, dish_id) DO NOTHING;

COMMIT;
