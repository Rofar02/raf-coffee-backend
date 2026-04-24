-- Опционально: как в `init.sql` — при удалении рубрики обнулять subcategory_id у блюд.
-- Запустите на существующей БД, если раньше таблицу `dishes` создавали без ON DELETE SET NULL.

BEGIN;

ALTER TABLE dishes DROP CONSTRAINT IF EXISTS dishes_subcategory_id_fkey;

ALTER TABLE dishes
  ADD CONSTRAINT dishes_subcategory_id_fkey
  FOREIGN KEY (subcategory_id) REFERENCES subcategories(id) ON DELETE SET NULL;

COMMIT;
