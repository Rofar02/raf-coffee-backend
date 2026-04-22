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

DELETE FROM season_dishes;
DELETE FROM menu_seasons;
DELETE FROM dishes;
DELETE FROM subcategories;
DELETE FROM categories;

INSERT INTO categories (name, sort_order) VALUES
  ('Еда', 1),
  ('Напитки', 2);

INSERT INTO subcategories (category_id, name, sort_order)
SELECT c.id, v.sub_name, v.sort_order
FROM (
  VALUES
    ('Еда', 'Завтраки', 1),
    ('Еда', 'Основные блюда', 2),
    ('Еда', 'Салаты', 3),
    ('Еда', 'Десерты', 4),
    ('Еда', 'Закуски', 5),
    ('Напитки', 'Кофе', 1),
    ('Напитки', 'Чай', 2),
    ('Напитки', 'Лимонады', 3),
    ('Напитки', 'Смузи', 4),
    ('Напитки', 'Фреши', 5)
) AS v(cat_name, sub_name, sort_order)
JOIN categories c ON c.name = v.cat_name;

INSERT INTO menu_seasons (name, slug, is_active, sort_order) VALUES
  ('Лето 2026', 'summer-2026', TRUE, 1),
  ('Осень 2026', 'autumn-2026', FALSE, 2),
  ('Зима 2026', 'winter-2026', FALSE, 3);

INSERT INTO dishes (name, price, weight_grams, description, calories, image_url, video_url, subcategory_id)
SELECT v.name, v.price, v.weight_grams, v.description, v.calories, v.image_url, v.video_url, s.id
FROM (
  VALUES
    -- Завтраки (5)
    ('Завтрак фермера', 420, 320, 'Омлет с овощами, зеленью и тостом.', '420 ккал', NULL, NULL, 'Завтраки'),
    ('Сырники со сметаной', 360, 240, 'Творожные сырники с ванилью и ягодным соусом.', '380 ккал', NULL, NULL, 'Завтраки'),
    ('Овсянка с бананом', 290, 280, 'Овсяная каша на молоке с бананом и медом.', '310 ккал', NULL, NULL, 'Завтраки'),
    ('Тост с авокадо и яйцом', 390, 210, 'Цельнозерновой тост, авокадо, яйцо пашот.', '340 ккал', NULL, NULL, 'Завтраки'),
    ('Блинчики с творогом', 350, 260, 'Нежные блинчики с творожной начинкой.', '360 ккал', NULL, NULL, 'Завтраки'),

    -- Основные блюда (5)
    ('Паста с курицей', 520, 340, 'Паста в сливочном соусе с куриным филе.', '560 ккал', NULL, NULL, 'Основные блюда'),
    ('Куриный боул', 490, 330, 'Рис, курица терияки, овощи и соус.', '510 ккал', NULL, NULL, 'Основные блюда'),
    ('Салат Цезарь с курицей', 450, 280, 'Классический цезарь с соусом и пармезаном.', '430 ккал', NULL, NULL, 'Основные блюда'),
    ('Суп дня', 280, 300, 'Ежедневный домашний суп, уточняйте у бариста.', '220 ккал', NULL, NULL, 'Основные блюда'),
    ('Кесадилья с сыром и курицей', 470, 290, 'Хрустящая тортилья с сыром и курицей.', '540 ккал', NULL, NULL, 'Основные блюда'),

    -- Кофе (5)
    ('Эспрессо', 170, 35, 'Классический насыщенный эспрессо.', '5 ккал', NULL, NULL, 'Кофе'),
    ('Американо', 190, 250, 'Эспрессо с горячей водой.', '10 ккал', NULL, NULL, 'Кофе'),
    ('Капучино', 240, 300, 'Эспрессо с молоком и плотной пеной.', '140 ккал', NULL, NULL, 'Кофе'),
    ('Латте', 260, 350, 'Мягкий кофейно-молочный напиток.', '170 ккал', NULL, NULL, 'Кофе'),
    ('Раф ванильный', 290, 300, 'Сливочный раф с ванильным сиропом.', '230 ккал', NULL, NULL, 'Кофе'),

    -- Чай (5)
    ('Чай Ассам', 190, 400, 'Крепкий черный чай.', '0 ккал', NULL, NULL, 'Чай'),
    ('Чай Эрл Грей', 210, 400, 'Черный чай с бергамотом.', '0 ккал', NULL, NULL, 'Чай'),
    ('Зеленый Сенча', 210, 400, 'Свежий японский зеленый чай.', '0 ккал', NULL, NULL, 'Чай'),
    ('Ягодный чай', 250, 450, 'Фруктово-ягодный чай с легкой кислинкой.', '40 ккал', NULL, NULL, 'Чай'),
    ('Облепиховый чай', 260, 450, 'Теплый чай с облепихой и медом.', '90 ккал', NULL, NULL, 'Чай')

    -- Доп. подкатегории (по 1 позиции)
   ,('Греческий салат', 390, 260, 'Свежие овощи, фета и оливковая заправка.', '290 ккал', NULL, NULL, 'Салаты')
   ,('Чизкейк классический', 310, 140, 'Нежный чизкейк с ванильной ноткой.', '410 ккал', NULL, NULL, 'Десерты')
   ,('Картофель по-деревенски', 240, 180, 'Хрустящий картофель с фирменным соусом.', '330 ккал', NULL, NULL, 'Закуски')
   ,('Лимонад цитрус-мята', 260, 450, 'Домашний лимонад с мятой и лаймом.', '120 ккал', NULL, NULL, 'Лимонады')
   ,('Смузи манго-маракуйя', 330, 350, 'Тропический смузи на пюре манго.', '190 ккал', NULL, NULL, 'Смузи')
   ,('Апельсиновый фреш', 320, 300, 'Свежевыжатый апельсиновый сок.', '130 ккал', NULL, NULL, 'Фреши')
) AS v(name, price, weight_grams, description, calories, image_url, video_url, subcategory_name)
JOIN subcategories s ON s.name = v.subcategory_name;

-- Активный сезон (Лето): включает всё тестовое меню.
INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT ms.id, d.id, d.id, TRUE
FROM dishes d
JOIN menu_seasons ms ON ms.slug = 'summer-2026';

-- Осень: ограниченный пример набора позиций.
INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT ms.id, d.id, d.id, TRUE
FROM dishes d
JOIN menu_seasons ms ON ms.slug = 'autumn-2026'
WHERE d.name IN (
  'Завтрак фермера',
  'Сырники со сметаной',
  'Суп дня',
  'Латте',
  'Чай Эрл Грей',
  'Чизкейк классический'
);

-- Зима: отдельный небольшой набор.
INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT ms.id, d.id, d.id, TRUE
FROM dishes d
JOIN menu_seasons ms ON ms.slug = 'winter-2026'
WHERE d.name IN (
  'Блинчики с творогом',
  'Кесадилья с сыром и курицей',
  'Раф ванильный',
  'Облепиховый чай'
);

COMMIT;
