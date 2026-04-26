-- JSON-массив URL фото, порядок = порядок в карусели; image_url = первый для обратной совместимости
ALTER TABLE dishes ADD COLUMN IF NOT EXISTS image_urls TEXT;
