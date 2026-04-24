-- Пересоздать только верхние категории: «Кухня» и «Напитки», без рубрик (добавьте в админке).
-- Связи блюд с подкатегориями (subcategory_id) сбросятся при удалении рубрик — убедитесь, что FK
-- на dishes — ON DELETE SET NULL (см. migrate_subcategory_fk_set_null.sql).
--
-- Полный сброс блюд/сезонов/всего — лучше reset_all_data_kitchen_drink.sql

BEGIN;

ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE subcategories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;

UPDATE dishes SET subcategory_id = NULL WHERE subcategory_id IS NOT NULL;
DELETE FROM subcategories;
DELETE FROM categories;

INSERT INTO categories (name, sort_order) VALUES
    ('Кухня', 1),
    ('Напитки', 2);

COMMIT;
