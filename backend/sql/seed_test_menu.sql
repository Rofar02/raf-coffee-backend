-- Полная пересборка демо-меню: мало позиций, у напитков — объём (мл).
-- Строки с кириллицей — только через U&'...' (ASCII-файл), иначе при
--   PowerShell: Get-Content | docker exec psql
--   без UTF-8 в БД попадут «??????».
--
-- Применение (рекомендуется): docker cp в контейнер и psql -f, либо:
--   Get-Content -Path seed_test_menu.sql -Encoding UTF8 -Raw | docker exec -i raf-postgres psql -U rafuser -d rafcoffee

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

ALTER TABLE dishes ADD COLUMN IF NOT EXISTS is_base_menu BOOLEAN NOT NULL DEFAULT TRUE;
ALTER TABLE dishes
ADD COLUMN IF NOT EXISTS volume_ml INTEGER
CHECK (volume_ml IS NULL OR (volume_ml >= 0 AND volume_ml <= 2000));

CREATE TABLE IF NOT EXISTS dish_volume_options (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    volume_ml INTEGER NOT NULL CHECK (volume_ml >= 0 AND volume_ml <= 2000),
    price INTEGER NOT NULL CHECK (price >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE (dish_id, volume_ml)
);

DELETE FROM season_dishes;
DELETE FROM menu_seasons;
DELETE FROM dishes;
DELETE FROM subcategories;
DELETE FROM categories;

INSERT INTO categories (name, sort_order) VALUES
  (U&'\0415\0434\0430', 1),
  (U&'\041d\0430\043f\0438\0442\043a\0438', 2);

INSERT INTO subcategories (category_id, name, sort_order)
SELECT c.id, v.sub_name, v.sort_order
FROM (
  VALUES
    (U&'\0415\0434\0430', U&'\0421\044b\0442\043d\043e\0435', 1),
    (U&'\0415\0434\0430', U&'\0421\043b\0430\0434\043a\043e\0435', 2),
    (U&'\041d\0430\043f\0438\0442\043a\0438', U&'\041a\043e\0444\0435', 1),
    (U&'\041d\0430\043f\0438\0442\043a\0438', U&'\0425\043e\043b\043e\0434\043d\044b\0435', 2)
) AS v(cat_name, sub_name, sort_order)
JOIN categories c ON c.name = v.cat_name;

INSERT INTO menu_seasons (name, slug, is_active, sort_order) VALUES
  (U&'\041b\0435\0442\043e\0020\0032\0030\0032\0036', 'summer-2026', TRUE, 1),
  (U&'\041e\0441\0435\043d\044c\0020\0032\0030\0032\0036', 'autumn-2026', FALSE, 2);

INSERT INTO dishes (name, price, weight_grams, volume_ml, description, calories, image_url, video_url, is_base_menu, subcategory_id)
SELECT v.dname, v.price, v.wg, v.vm, v.descr, v.kcal, NULL, NULL, TRUE, s.id
FROM (
  VALUES
    (U&'\0421\044d\043d\0434\0432\0438\0447\0020\0441\0020\043a\0443\0440\0438\0446\0435\0439', 320, 220, NULL, U&'\0421\044b\0442\043d\044b\0439\0020\0441\044d\043d\0434\0432\0438\0447\0020\043d\0430\0020\0447\0438\0430\0431\0430\0442\0442\0435\002e', U&'\0034\0032\0030\0020\043a\043a\0430\043b', U&'\0421\044b\0442\043d\043e\0435'),
    (U&'\0411\043e\0443\043b\0020\0441\0020\043b\043e\0441\043e\0441\0435\043c', 420, 320, NULL, U&'\0420\0438\0441\002c\0020\043b\043e\0441\043e\0441\044c\002c\0020\043e\0432\043e\0449\0438\002c\0020\0441\043e\0443\0441\002e', U&'\0035\0031\0030\0020\043a\043a\0430\043b', U&'\0421\044b\0442\043d\043e\0435'),
    (U&'\0421\044b\0440\043d\0438\043a', 180, 140, NULL, U&'\0414\043e\043c\0430\0448\043d\0438\0435\0020\0441\044b\0440\043d\0438\043a\0438\0020\0441\0020\044f\0433\043e\0434\043d\044b\043c\0020\0441\043e\0443\0441\043e\043c\002e', U&'\0032\0038\0030\0020\043a\043a\0430\043b', U&'\0421\043b\0430\0434\043a\043e\0435'),
    (U&'\041a\0440\0443\0430\0441\0441\0430\043d', 150, 90, NULL, U&'\0421\043b\043e\0451\043d\044b\0439\0020\043a\0440\0443\0430\0441\0441\0430\043d\0020\0441\0020\043c\0430\0441\043b\043e\043c\002e', U&'\0032\0034\0030\0020\043a\043a\0430\043b', U&'\0421\043b\0430\0434\043a\043e\0435'),
    (U&'\041a\0430\043f\0443\0447\0438\043d\043e', 200, NULL, 200, U&'\042d\0441\043f\0440\0435\0441\0441\043e\0020\0438\0020\043c\043e\043b\043e\0447\043d\0430\044f\0020\043f\0435\043d\0430\002e', U&'\0031\0032\0030\0020\043a\043a\0430\043b', U&'\041a\043e\0444\0435'),
    (U&'\041b\0430\0442\0442\0435', 220, NULL, 300, U&'\041d\0435\0436\043d\043e\0435\0020\043c\043e\043b\043e\043a\043e\0020\0438\0020\044d\0441\043f\0440\0435\0441\0441\043e\002e', U&'\0031\0038\0030\0020\043a\043a\0430\043b', U&'\041a\043e\0444\0435'),
    (U&'\041b\0438\043c\043e\043d\0430\0434\0020\043a\043b\0443\0431\043d\0438\043a\0430', 180, NULL, 400, U&'\041e\0441\0432\0435\0436\0430\044e\0449\0438\0439\0020\043b\0438\043c\043e\043d\0430\0434\0020\0441\0020\043a\043b\0443\0431\043d\0438\043a\043e\0439\002e', U&'\0039\0030\0020\043a\043a\0430\043b', U&'\0425\043e\043b\043e\0434\043d\044b\0435'),
    (U&'\0421\043c\0443\0437\0438\0020\043c\0430\043d\0433\043e', 250, NULL, 350, U&'\041c\0430\043d\0433\043e\002c\0020\0431\0430\043d\0430\043d\002c\0020\0441\043e\043a\002e', U&'\0032\0030\0030\0020\043a\043a\0430\043b', U&'\0425\043e\043b\043e\0434\043d\044b\0435')
) AS v(dname, price, wg, vm, descr, kcal, sub_name)
JOIN subcategories s ON s.name = v.sub_name;

-- Варианты объёма (капучино, латте) — min(price) в dishes
INSERT INTO dish_volume_options (dish_id, volume_ml, price, sort_order)
SELECT d.id, v.vm, v.pr, v.so
FROM dishes d
JOIN (
  VALUES
    (U&'\041a\0430\043f\0443\0447\0438\043d\043e', 200, 180, 0),
    (U&'\041a\0430\043f\0443\0447\0438\043d\043e', 300, 200, 1),
    (U&'\041a\0430\043f\0443\0447\0438\043d\043e', 400, 230, 2),
    (U&'\041b\0430\0442\0442\0435', 200, 200, 0),
    (U&'\041b\0430\0442\0442\0435', 300, 220, 1),
    (U&'\041b\0430\0442\0442\0435', 400, 250, 2)
) AS v(dname, vm, pr, so) ON d.name = v.dname
ON CONFLICT (dish_id, volume_ml) DO NOTHING;

UPDATE dishes SET price = 180, volume_ml = NULL WHERE name = U&'\041a\0430\043f\0443\0447\0438\043d\043e';
UPDATE dishes SET price = 200, volume_ml = NULL WHERE name = U&'\041b\0430\0442\0442\0435';

INSERT INTO dishes (name, price, weight_grams, volume_ml, description, calories, image_url, video_url, is_base_menu, subcategory_id)
SELECT
  ms.name || U&'\0020\2014\0020' || s.name,
  CASE
    WHEN c.name = U&'\0415\0434\0430' THEN 350
    ELSE 200
  END,
  CASE WHEN c.name = U&'\0415\0434\0430' THEN 200 ELSE NULL END,
  CASE WHEN c.name = U&'\041d\0430\043f\0438\0442\043a\0438' THEN 300 ELSE NULL END,
  U&'\0421\0435\0437\043e\043d\043d\0430\044f\0020\043f\043e\0437\0438\0446\0438\044f\0020\0434\043b\044f\0020\00ab' || ms.name || U&'\00bb\002e',
  (200 + s.sort_order * 15) || U&'\0020\043a\043a\0430\043b',
  NULL,
  NULL,
  FALSE,
  s.id
FROM menu_seasons ms
CROSS JOIN subcategories s
JOIN categories c ON c.id = s.category_id
WHERE ms.is_active = TRUE
ORDER BY s.sort_order, s.id;

INSERT INTO season_dishes (season_id, dish_id, sort_order, is_visible)
SELECT
  ms.id,
  d.id,
  s.sort_order * 10,
  TRUE
FROM dishes d
JOIN subcategories s ON s.id = d.subcategory_id
JOIN menu_seasons ms ON d.is_base_menu = FALSE
  AND d.name LIKE ms.name || U&'\0020\2014\0020' || U&'\0025'
  AND ms.is_active = TRUE;

COMMIT;
