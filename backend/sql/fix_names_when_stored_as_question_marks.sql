-- Если при прогоне сидов на Windows/через psql названия в UTF-8 превратились
-- в настоящие знаки "?" (байт 0x3F), а не в кракозябры — обновим через chr().
-- init.sql в репозитории в UTF-8, но в уже существующем томе PostgreSQL старые INSERT не перезапускаются.
--
-- Кухня:  К у х н я
-- Напитки, Базовый сезон: см. codepoints в комментариях

BEGIN;

UPDATE categories SET name = chr(1050) || chr(1091) || chr(1093) || chr(1085) || chr(1103) WHERE id = 1;
UPDATE categories SET name = chr(1053) || chr(1072) || chr(1087) || chr(1080) || chr(1090) || chr(1082) || chr(1080) WHERE id = 2;

-- «Базовый сезон» (id обычно 1, slug default)
UPDATE menu_seasons
SET name = chr(1041) || chr(1072) || chr(1079) || chr(1086) || chr(1074) || chr(1099) || chr(1081)
    || chr(32) || chr(1089) || chr(1077) || chr(1079) || chr(1086) || chr(1085)
WHERE slug = 'default' OR id = 1;

COMMIT;
