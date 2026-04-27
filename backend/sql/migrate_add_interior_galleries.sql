BEGIN;

CREATE TABLE IF NOT EXISTS interior_galleries (
  slug TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  images_json TEXT NOT NULL DEFAULT '[]',
  updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO interior_galleries (slug, title, description, images_json)
VALUES
  (
    'kirova-45a',
    'Кирова 45а',
    'Первая кофейня: компактный зал, столы у окна, удобно и «на бегу» с кофе, и с ноутбуком. Тёплые оттенки дерева и мягкий свет — фирменный уют «Рафчика».',
    '[]'
  ),
  (
    'kirova-12',
    'Кирова 12',
    'Вторая точка: просторнее посадка, тот же кофе и десерты, своё сочетание света и зоны для встреч. Заходите — найдёте «свой» угол.',
    '[]'
  )
ON CONFLICT (slug) DO NOTHING;

COMMIT;
