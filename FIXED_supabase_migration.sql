-- ПОЛНАЯ МИГРАЦИЯ SUPABASE: chapter -> chapter_start + chapter_end  
-- Выполните этот скрипт ПОЛНОСТЬЮ в Supabase SQL Editor

-- 1. Добавляем новые поля
ALTER TABLE saved_commentaries 
ADD COLUMN IF NOT EXISTS chapter_start INTEGER,
ADD COLUMN IF NOT EXISTS chapter_end INTEGER;

-- 2. Копируем данные из старого поля в новые (если есть старые данные)
UPDATE saved_commentaries 
SET chapter_start = chapter,
    chapter_end = NULL  -- Для старых записей chapter_end = NULL (одна глава)
WHERE chapter_start IS NULL AND chapter IS NOT NULL;

-- 3. Делаем chapter_start обязательным
ALTER TABLE saved_commentaries 
ALTER COLUMN chapter_start SET NOT NULL;

-- 4. УДАЛЯЕМ старое поле chapter (это важно!)
ALTER TABLE saved_commentaries DROP COLUMN IF EXISTS chapter;

-- 5. Пересоздаем индексы с новой схемой
DROP INDEX IF EXISTS idx_saved_commentaries_reference;
DROP INDEX IF EXISTS idx_saved_commentaries_full;

CREATE INDEX idx_saved_commentaries_reference ON saved_commentaries(user_id, book_id, chapter_start);
CREATE INDEX idx_saved_commentaries_full ON saved_commentaries(user_id, book_id, chapter_start, chapter_end, verse_start, verse_end);

-- 6. Добавляем комментарии
COMMENT ON COLUMN saved_commentaries.chapter_start IS 'Начальная глава (для диапазонов глав)';
COMMENT ON COLUMN saved_commentaries.chapter_end IS 'Конечная глава (NULL для одной главы)';

-- 7. Проверяем результат
SELECT column_name, data_type, is_nullable, column_default 
FROM information_schema.columns 
WHERE table_name = 'saved_commentaries' 
ORDER BY ordinal_position; 