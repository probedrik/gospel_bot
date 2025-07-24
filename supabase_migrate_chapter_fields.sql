-- Миграция таблицы saved_commentaries: chapter -> chapter_start + chapter_end
-- Выполните этот скрипт в Supabase SQL Editor ИЛИ в PostgreSQL

-- ==========================================
-- МИГРАЦИЯ ДЛЯ SUPABASE
-- ==========================================

-- Добавляем новые поля
ALTER TABLE saved_commentaries 
ADD COLUMN IF NOT EXISTS chapter_start INTEGER,
ADD COLUMN IF NOT EXISTS chapter_end INTEGER;

-- Копируем данные из старого поля chapter в новое поле chapter_start
UPDATE saved_commentaries 
SET chapter_start = chapter, 
    chapter_end = chapter 
WHERE chapter_start IS NULL;

-- Делаем chapter_start обязательным
ALTER TABLE saved_commentaries 
ALTER COLUMN chapter_start SET NOT NULL;

-- Удаляем старое поле chapter (если есть)
-- ВНИМАНИЕ: Раскомментируйте следующую строку только после проверки данных!
-- ALTER TABLE saved_commentaries DROP COLUMN IF EXISTS chapter;

-- Пересоздаем индексы
DROP INDEX IF EXISTS idx_saved_commentaries_reference;
DROP INDEX IF EXISTS idx_saved_commentaries_full;

CREATE INDEX idx_saved_commentaries_reference ON saved_commentaries(user_id, book_id, chapter_start);
CREATE INDEX idx_saved_commentaries_full ON saved_commentaries(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end);

-- Комментарии к новым полям
COMMENT ON COLUMN saved_commentaries.chapter_start IS 'Начальная глава (для диапазонов глав)';
COMMENT ON COLUMN saved_commentaries.chapter_end IS 'Конечная глава (NULL для одной главы)';

-- ==========================================
-- МИГРАЦИЯ ДЛЯ POSTGRESQL (если используется)
-- ==========================================

-- Примечание: PostgreSQL не поддерживает IF NOT EXISTS для ALTER TABLE ADD COLUMN
-- Используйте этот блок только если у вас есть существующие данные в PostgreSQL

/*
-- Добавляем новые поля (только если их еще нет)
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'saved_commentaries' AND column_name = 'chapter_start') THEN
        ALTER TABLE saved_commentaries ADD COLUMN chapter_start INTEGER;
    END IF;
    
    IF NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'saved_commentaries' AND column_name = 'chapter_end') THEN
        ALTER TABLE saved_commentaries ADD COLUMN chapter_end INTEGER;
    END IF;
END $$;

-- Копируем данные из старого поля chapter в новое поле chapter_start
UPDATE saved_commentaries 
SET chapter_start = chapter, 
    chapter_end = NULL  -- Для PostgreSQL устанавливаем NULL явно
WHERE chapter_start IS NULL;

-- Делаем chapter_start обязательным
ALTER TABLE saved_commentaries 
ALTER COLUMN chapter_start SET NOT NULL;

-- Удаляем старое поле chapter (если есть)
-- ВНИМАНИЕ: Раскомментируйте следующую строку только после проверки данных!
-- ALTER TABLE saved_commentaries DROP COLUMN IF EXISTS chapter;

-- Пересоздаем индексы для PostgreSQL
DROP INDEX IF EXISTS idx_saved_commentaries_user_id;
DROP INDEX IF EXISTS idx_saved_commentaries_reference;

CREATE INDEX idx_saved_commentaries_user_id ON saved_commentaries(user_id);
CREATE INDEX idx_saved_commentaries_reference ON saved_commentaries(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end, commentary_type);
*/ 