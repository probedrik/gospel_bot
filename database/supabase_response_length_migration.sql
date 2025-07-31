-- Миграция для Supabase: Добавление поля response_length в таблицу users
-- Выполните этот скрипт в SQL Editor вашего Supabase проекта

-- Добавляем поле response_length в таблицу users
-- Это поле будет хранить настройку размера ответа ИИ для премиум пользователей
DO $$
BEGIN
    -- Проверяем, существует ли уже столбец
    IF NOT EXISTS (
        SELECT 1 
        FROM information_schema.columns 
        WHERE table_name = 'users' 
        AND column_name = 'response_length'
    ) THEN
        -- Добавляем столбец только если его еще нет
        ALTER TABLE users ADD COLUMN response_length TEXT DEFAULT 'full';
        
        -- Обновляем существующих пользователей, устанавливая значение по умолчанию
        UPDATE users SET response_length = 'full' WHERE response_length IS NULL;
        
        RAISE NOTICE 'Поле response_length добавлено в таблицу users';
    ELSE
        RAISE NOTICE 'Поле response_length уже существует в таблице users';
    END IF;
END $$;

-- Создаем комментарий для поля
COMMENT ON COLUMN users.response_length IS 'Настройка размера ответа ИИ: short (краткий) или full (полный)';

-- Проверяем результат
SELECT column_name, data_type, column_default, is_nullable
FROM information_schema.columns 
WHERE table_name = 'users' 
AND column_name = 'response_length';