-- Скрипт создания базы данных для локальной разработки
-- Выполнить в PostgreSQL под суперпользователем (обычно postgres)

-- Создать базу данных
CREATE DATABASE wb_promotion_app
    WITH 
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'Russian_Russia.1251'
    LC_CTYPE = 'Russian_Russia.1251'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1;

-- Комментарий к базе данных
COMMENT ON DATABASE wb_promotion_app IS 'Wildberries Promotion API Manager - локальная БД';

-- Примечание: 
-- Если пользователь postgres уже существует и имеет пароль 'postgres',
-- то дополнительных действий не требуется.
-- 
-- Если нужно создать отдельного пользователя:
-- CREATE USER wb_user WITH PASSWORD 'wb_password';
-- GRANT ALL PRIVILEGES ON DATABASE wb_promotion_app TO wb_user;
