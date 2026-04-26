CREATE TABLE IF NOT EXISTS categories (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS subcategories (
    id SERIAL PRIMARY KEY,
    category_id INTEGER NOT NULL REFERENCES categories(id) ON DELETE CASCADE,
    name VARCHAR(200) NOT NULL,
    sort_order INTEGER NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS dishes (
    id SERIAL PRIMARY KEY,
    name VARCHAR(200) NOT NULL,
    price INTEGER NOT NULL CHECK (price >= 0),
    weight_grams INTEGER CHECK (weight_grams IS NULL OR weight_grams >= 0),
    volume_ml INTEGER CHECK (volume_ml IS NULL OR (volume_ml >= 0 AND volume_ml <= 2000)),
    description VARCHAR(1000),
    calories TEXT,
    image_url TEXT,
    video_url TEXT,
    is_base_menu BOOLEAN NOT NULL DEFAULT TRUE,
    subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE SET NULL
);

-- Варианты объёма/цены для напитков (на одну позицию — несколько стаканов)
CREATE TABLE IF NOT EXISTS dish_volume_options (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    volume_ml INTEGER NOT NULL CHECK (volume_ml >= 0 AND volume_ml <= 2000),
    price INTEGER NOT NULL CHECK (price >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    nutrition_kcal TEXT,
    nutrition_bju TEXT,
    UNIQUE (dish_id, volume_ml)
);

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

-- Старт без подкатегорий: их добавляют в админке. Две категории верхнего уровня.
INSERT INTO categories (name, sort_order)
SELECT v.name, v.sort_order
FROM (VALUES
    ('Кухня', 1),
    ('Напитки', 2)
) AS v(name, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM categories LIMIT 1);

-- Один активный сезон; дополнительные — через админку
INSERT INTO menu_seasons (name, slug, is_active, sort_order)
SELECT v.name, v.slug, v.is_active, v.sort_order
FROM (VALUES
    ('Базовый сезон', 'default', TRUE, 1)
) AS v(name, slug, is_active, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM menu_seasons LIMIT 1);

INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT ms.id, d.id, d.id, TRUE
FROM dishes d
JOIN menu_seasons ms ON ms.is_active = TRUE
WHERE NOT EXISTS (SELECT 1 FROM season_dishes LIMIT 1);
