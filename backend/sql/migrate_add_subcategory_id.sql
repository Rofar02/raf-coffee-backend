-- Если таблица `dishes` уже была без колонки subcategory_id (старый том PostgreSQL):
ALTER TABLE dishes ADD COLUMN IF NOT EXISTS subcategory_id INTEGER;
