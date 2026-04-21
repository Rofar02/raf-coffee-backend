-- Пересоздать категории и подкатегории под актуальное меню Rafchik.
-- Связи блюд с подкатегориями (subcategory_id) сбросятся в NULL — назначьте подкатегории заново в админке.
--
-- Если раньше база создавалась без sort_order — колонки добавятся автоматически.

BEGIN;

ALTER TABLE categories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;
ALTER TABLE subcategories ADD COLUMN IF NOT EXISTS sort_order INTEGER NOT NULL DEFAULT 0;

DELETE FROM subcategories;
DELETE FROM categories;

INSERT INTO categories (name, sort_order) VALUES
    ('Сезонное предложение', 1),
    ('Бар', 2),
    ('Кухня', 3);

INSERT INTO subcategories (category_id, name, sort_order)
SELECT c.id, v.sub_name, v.sort_order
FROM (VALUES
    ('Сезонное предложение', 'Кофе', 1),
    ('Сезонное предложение', 'Смузи', 2),
    ('Бар', 'Чёрный кофе', 1),
    ('Бар', 'Альтернатива', 2),
    ('Бар', 'Не кофе', 3),
    ('Бар', 'Классика', 4),
    ('Бар', 'Авторские рафы', 5),
    ('Кухня', 'Сытные блюда', 1),
    ('Кухня', 'Сэндвичи', 2),
    ('Кухня', 'Салаты', 3),
    ('Кухня', 'Закуски', 4),
    ('Кухня', 'Сладкие блюда', 5)
) AS v(cat_name, sub_name, sort_order)
JOIN categories c ON c.name = v.cat_name;

COMMIT;
