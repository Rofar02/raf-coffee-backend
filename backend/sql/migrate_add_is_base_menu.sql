-- Базовое меню + сезонные добавки.
-- В основном меню показываются только dishes.is_base_menu = TRUE.
-- Сезонные позиции добавляются через таблицу season_dishes.

ALTER TABLE dishes
ADD COLUMN IF NOT EXISTS is_base_menu BOOLEAN NOT NULL DEFAULT TRUE;
