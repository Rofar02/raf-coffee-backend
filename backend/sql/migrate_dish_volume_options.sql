CREATE TABLE IF NOT EXISTS dish_volume_options (
    id SERIAL PRIMARY KEY,
    dish_id INTEGER NOT NULL REFERENCES dishes(id) ON DELETE CASCADE,
    volume_ml INTEGER NOT NULL CHECK (volume_ml >= 0 AND volume_ml <= 2000),
    price INTEGER NOT NULL CHECK (price >= 0),
    sort_order INTEGER NOT NULL DEFAULT 0,
    UNIQUE (dish_id, volume_ml)
);

-- Миграция: один вариант из legacy volume_ml
INSERT INTO dish_volume_options (dish_id, volume_ml, price, sort_order)
SELECT d.id, d.volume_ml, d.price, 0
FROM dishes d
WHERE d.volume_ml IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM dish_volume_options o WHERE o.dish_id = d.id)
ON CONFLICT (dish_id, volume_ml) DO NOTHING;
