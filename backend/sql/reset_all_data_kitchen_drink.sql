-- Полный сброс данных: пустой каталог, две категории «Кухня» и «Напитки», подкатегорий нет.
-- Один активный сезон — чтобы админка и меню не ломались на пустом списке сезонов.
-- Выполняйте вручную на своей БД; после — сбросьте кеш меню (админка) или рестарт Redis.

BEGIN;

TRUNCATE
  season_dishes,
  dish_volume_options,
  dishes,
  subcategories,
  menu_seasons,
  categories
RESTART IDENTITY;

INSERT INTO categories (name, sort_order) VALUES
  ('Кухня', 1),
  ('Напитки', 2);

INSERT INTO menu_seasons (name, slug, is_active, sort_order)
VALUES ('Базовый сезон', 'default', TRUE, 1);

COMMIT;
