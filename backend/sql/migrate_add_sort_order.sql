-- Добавить sort_order, если база создавалась по старой схеме без этих колонок.
-- Безопасно запускать повторно.

ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE subcategories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;
