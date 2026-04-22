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
    description VARCHAR(1000),
    calories TEXT,
    image_url TEXT,
    video_url TEXT,
    subcategory_id INTEGER REFERENCES subcategories(id) ON DELETE SET NULL
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

-- Демо-дерево меню (только если таблицы пустые — первый запуск init)
INSERT INTO categories (name, sort_order)
SELECT v.name, v.sort_order
FROM (VALUES
    ('Сезонное предложение', 1),
    ('Бар', 2),
    ('Кухня', 3)
) AS v(name, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM categories LIMIT 1);

INSERT INTO subcategories (category_id, name, sort_order)
SELECT c.id, v.sub_name, v.sort_order
FROM (VALUES
    ('Сезонное предложение', 'Кофе', 1),
    ('Сезонное предложение', 'Смузи', 2),
    ('Бар', 'Чёрный кофе', 1),
    ('Бар', 'Альтернатива', 2),
    ('Бар', 'Не кофе', 3),
    ('Бар', 'Классика', 4),
    ('Бар', 'Авторские рафы', 5),
    ('Кухня', 'Сытные блюда', 1),
    ('Кухня', 'Сэндвичи', 2),
    ('Кухня', 'Салаты', 3),
    ('Кухня', 'Закуски', 4),
    ('Кухня', 'Сладкие блюда', 5)
) AS v(cat_name, sub_name, sort_order)
JOIN categories c ON c.name = v.cat_name
WHERE NOT EXISTS (SELECT 1 FROM subcategories LIMIT 1);

INSERT INTO menu_seasons (name, slug, is_active, sort_order)
SELECT v.name, v.slug, v.is_active, v.sort_order
FROM (VALUES
    ('Базовый сезон', 'default', TRUE, 1),
    ('Лето 2026', 'summer-2026', FALSE, 2),
    ('Осень 2026', 'autumn-2026', FALSE, 3)
) AS v(name, slug, is_active, sort_order)
WHERE NOT EXISTS (SELECT 1 FROM menu_seasons LIMIT 1);

INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT ms.id, d.id, d.id, TRUE
FROM dishes d
JOIN menu_seasons ms ON ms.is_active = TRUE
WHERE NOT EXISTS (SELECT 1 FROM season_dishes LIMIT 1);
