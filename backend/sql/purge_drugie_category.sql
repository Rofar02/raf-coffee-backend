-- Удалить категории «Другие» / «Другое» и все их рубрики (в т.ч. «пиво»).
-- Сначала снять subcategory_id у блюд (как в purge_bar).
-- Имена через chr() — без проблем с кодировкой файла/консоли.
--
-- «Другие» = chr(1044)…chr(1077) ; «Другое» = … chr(1086) chr(1077) (о вместо и)

BEGIN;

UPDATE dishes d
SET subcategory_id = NULL
FROM subcategories s
JOIN categories c ON c.id = s.category_id
WHERE d.subcategory_id = s.id
  AND (
    LOWER(TRIM(c.name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1080) || chr(1077)))
    OR LOWER(TRIM(c.name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1086) || chr(1077)))
  );

DELETE FROM subcategories
WHERE category_id IN (
  SELECT id
  FROM categories
  WHERE
    LOWER(TRIM(name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1080) || chr(1077)))
    OR LOWER(TRIM(name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1086) || chr(1077)))
);

DELETE FROM categories
WHERE
  LOWER(TRIM(name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1080) || chr(1077)))
  OR LOWER(TRIM(name)) = LOWER((chr(1044) || chr(1088) || chr(1091) || chr(1075) || chr(1086) || chr(1077)));

COMMIT;
