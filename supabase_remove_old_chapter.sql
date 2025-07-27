-- Удаление старого поля chapter из таблицы bookmarks в Supabase
-- Выполните этот скрипт после того, как убедитесь, что новые поля работают

-- Сначала проверим, что новые поля заполнены
SELECT 
    COUNT(*) as total_bookmarks,
    COUNT(chapter_start) as with_chapter_start,
    COUNT(chapter) as with_old_chapter
FROM bookmarks;

-- Если все закладки имеют chapter_start, можно удалить старое поле
-- ВНИМАНИЕ: Это необратимая операция!

-- Удаляем старое поле chapter
ALTER TABLE bookmarks DROP COLUMN IF EXISTS chapter;

-- Проверяем результат
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bookmarks' 
ORDER BY ordinal_position;