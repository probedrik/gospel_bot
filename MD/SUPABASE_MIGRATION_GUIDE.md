# 🔄 Миграция таблицы bookmarks в Supabase

## 📋 Проблема
В текущей таблице `bookmarks` в Supabase отсутствуют поля `chapter_start` и `chapter_end`, которые необходимы для поддержки диапазонов глав и стихов.

## 🎯 Цель миграции
Добавить поля для поддержки:
- **Диапазонов глав**: "Быт 1-3", "Пс 1-5"
- **Диапазонов стихов**: "Ин 3:16-18", "Мф 5:3-12"
- **Заметок к закладкам**: поле `note`

## 🚀 Пошаговая инструкция

### Шаг 1: Резервное копирование
```sql
-- Создаем резервную копию таблицы
CREATE TABLE bookmarks_backup AS SELECT * FROM bookmarks;
```

### Шаг 2: Выполнение миграции
Выполните SQL скрипт `supabase_bookmarks_migration.sql`:

```sql
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
```

### Шаг 3: Проверка миграции
Запустите скрипт проверки:
```bash
python check_bookmarks_compatibility.py
```

### Шаг 4: Удаление старой колонки (опционально)
После успешной миграции и тестирования:
```sql
-- ОСТОРОЖНО! Выполняйте только после полного тестирования
ALTER TABLE bookmarks DROP COLUMN chapter;
```

## 📊 Структура до и после

### До миграции:
```sql
CREATE TABLE bookmarks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id INTEGER NOT NULL,
    chapter INTEGER NOT NULL,        -- Старое поле
    verse_start INTEGER,
    verse_end INTEGER,
    display_text TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### После миграции:
```sql
CREATE TABLE bookmarks (
    id BIGSERIAL PRIMARY KEY,
    user_id BIGINT NOT NULL,
    book_id INTEGER NOT NULL,
    chapter INTEGER,                 -- Старое поле (можно удалить)
    chapter_start INTEGER NOT NULL, -- Новое поле
    chapter_end INTEGER,            -- Новое поле
    verse_start INTEGER,
    verse_end INTEGER,
    display_text TEXT,
    note TEXT,                      -- Новое поле
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 🔍 Проверка результата

### Проверьте структуру таблицы:
```sql
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'bookmarks' 
ORDER BY ordinal_position;
```

### Проверьте данные:
```sql
SELECT user_id, book_id, chapter, chapter_start, chapter_end, verse_start, verse_end, display_text
FROM bookmarks 
LIMIT 5;
```

### Ожидаемый результат:
- ✅ Поле `chapter_start` заполнено значениями из `chapter`
- ✅ Поле `chapter_end` содержит `NULL` (для одиночных глав)
- ✅ Все старые закладки сохранены и работают
- ✅ Новые закладки могут использовать диапазоны

## 🚨 Откат миграции (если что-то пошло не так)

```sql
-- Восстанавливаем из резервной копии
DROP TABLE bookmarks;
ALTER TABLE bookmarks_backup RENAME TO bookmarks;

-- Восстанавливаем индексы
CREATE INDEX idx_bookmarks_user_id ON bookmarks(user_id);
```

## ✅ Проверочный список

- [ ] Создана резервная копия таблицы
- [ ] Выполнена миграция SQL скриптом
- [ ] Запущена проверка совместимости
- [ ] Протестировано добавление новых закладок
- [ ] Протестировано отображение старых закладок
- [ ] Протестированы диапазоны глав и стихов
- [ ] Удалена резервная копия (после полного тестирования)

## 🔧 Альтернативный вариант: Пересоздание таблицы

Если миграция вызывает проблемы, можно пересоздать таблицу:

1. Экспортируйте данные: `pg_dump --table=bookmarks`
2. Выполните `supabase_bookmarks_create.sql`
3. Импортируйте данные с преобразованием полей

## 📞 Поддержка

При возникновении проблем:
1. Проверьте логи Supabase
2. Запустите `check_bookmarks_compatibility.py`
3. Убедитесь, что все индексы созданы
4. Проверьте права доступа (RLS policies)