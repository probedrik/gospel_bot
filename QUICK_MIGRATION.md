# ⚡ Быстрая миграция Supabase

## 🎯 Что нужно сделать
Добавить поля `chapter_start` и `chapter_end` в таблицу `bookmarks` в Supabase.

## 🚀 Быстрые шаги

### 1. Откройте Supabase Dashboard
- Перейдите в ваш проект Supabase
- Откройте SQL Editor

### 2. Выполните миграцию
Скопируйте и выполните этот SQL:

```sql
-- Добавляем новые колонки
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS chapter_start INTEGER;
ALTER TABLE bookmarks ADD COLUMN IF NOT EXISTS chapter_end INTEGER;

-- Заполняем данными из старой колонки
UPDATE bookmarks 
SET chapter_start = chapter, chapter_end = NULL 
WHERE chapter_start IS NULL;

-- Делаем chapter_start обязательным
ALTER TABLE bookmarks ALTER COLUMN chapter_start SET NOT NULL;

-- Создаем индекс
CREATE INDEX IF NOT EXISTS idx_bookmarks_chapters 
ON bookmarks(user_id, book_id, chapter_start, chapter_end);
```

### 3. Проверьте результат
```sql
-- Проверьте структуру
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bookmarks' 
ORDER BY ordinal_position;

-- Проверьте данные
SELECT * FROM bookmarks LIMIT 3;
```

### 4. Протестируйте бота
```bash
python check_bookmarks_compatibility.py
```

## ✅ Готово!
После выполнения этих шагов система закладок будет полностью работать с диапазонами глав и стихов.

## 🔧 Если что-то пошло не так
1. Проверьте логи в Supabase Dashboard
2. Убедитесь, что все SQL команды выполнились без ошибок
3. Запустите проверочный скрипт еще раз