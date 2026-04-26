-- Ккал и БЖУ на каждую опцию объёма (а не в одной строке dishes.calories)
ALTER TABLE dish_volume_options
  ADD COLUMN IF NOT EXISTS nutrition_kcal TEXT,
  ADD COLUMN IF NOT EXISTS nutrition_bju TEXT;
