-- Снести категорию «Бар» и рубрику «пиво»/«Пиво».
-- Сначала снимаем subcategory_id у блюд (у старых БД FK часто без ON DELETE SET NULL).
-- Имя «Бар» в условиях — через chr() (достоверно в UTF-8, без проблем кодировки файла в Windows).

BEGIN;

-- «Бар» = chr(1041)||chr(1072)||chr(1088) ; «пиво» = chr(1087)||chr(1080)||chr(1074)||chr(1086)

UPDATE dishes d
SET subcategory_id = NULL
FROM subcategories s
JOIN categories c ON c.id = s.category_id
WHERE d.subcategory_id = s.id
  AND c.name = (chr(1041) || chr(1072) || chr(1088));

UPDATE dishes
SET subcategory_id = NULL
WHERE subcategory_id IN (
  SELECT id
  FROM subcategories
  WHERE LOWER(TRIM(name)) = (chr(1087) || chr(1080) || chr(1074) || chr(1086))
);

DELETE FROM subcategories
WHERE LOWER(TRIM(name)) = (chr(1087) || chr(1080) || chr(1074) || chr(1086));

DELETE FROM subcategories
WHERE category_id IN (
  SELECT id FROM categories WHERE name = (chr(1041) || chr(1072) || chr(1088))
);

DELETE FROM categories
WHERE name = (chr(1041) || chr(1072) || chr(1088));

COMMIT;
