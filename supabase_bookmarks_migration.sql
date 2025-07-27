-- Миграция таблицы bookmarks в Supabase
-- Добавляем поля chapter_start и chapter_end для поддержки диапазонов глав

-- Добавляем новые колонки
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS chapter_start INTEGER;
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS chapter_end INTEGER;

-- Заполняем новые колонки данными из старой колонки chapter
UPDATE bookmarks 
SET chapter_start = chapter, chapter_end = NULL 
WHERE chapter_start IS NULL;

-- Делаем chapter_start обязательным полем
ALTER TABLE bookmarks ALTER COLUMN chapter_start SET NOT NULL;

-- Создаем индекс для быстрого поиска по диапазонам глав
CREATE INDEX IF NOT EXISTS idx_bookmarks_chapters 
ON bookmarks(user_id, book_id, chapter_start, chapter_end);

-- Можем оставить старую колонку chapter для совместимости или удалить её
-- Если хотите удалить старую колонку, раскомментируйте следующую строку:
-- ALTER TABLE bookmarks DROP COLUMN chapter;