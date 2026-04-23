-- Объём напитка в миллилитрах (опционально; для кофе, соков и т.д.).

ALTER TABLE dishes
ADD COLUMN IF NOT EXISTS volume_ml INTEGER CHECK (volume_ml IS NULL OR (volume_ml >= 0 AND volume_ml <= 2000));
