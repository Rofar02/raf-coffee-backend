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
