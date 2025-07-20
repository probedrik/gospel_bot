-- Инициализация базы данных Gospel Bot для PostgreSQL
-- Этот файл выполняется автоматически при первом запуске контейнера PostgreSQL

-- Устанавливаем кодировку UTF-8
SET client_encoding = 'UTF8';

-- Создаем пользователя бота (если не существует)
DO $$ 
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'gospel_bot_user') THEN
        CREATE ROLE gospel_bot_user WITH LOGIN PASSWORD 'gospel_bot_pass';
    END IF;
END
$$;

-- Даем права пользователю на базу данных
GRANT ALL PRIVILEGES ON DATABASE gospel_bot TO gospel_bot_user;

-- Комментарий о назначении базы
COMMENT ON DATABASE gospel_bot IS 'База данных для Telegram бота изучения Библии'; 