# ⚡ Быстрая настройка системы комментариев

## 🎯 Что добавлено

✅ **Кнопка "📝 Сохраненные комментарии"** в меню закладок  
✅ **Просмотр комментариев** с пагинацией (16 в 2 столбца)  
✅ **Удаление комментариев** по ID  
✅ **Поддержка Supabase/PostgreSQL** (SQLite не поддерживается)

## 🚀 Быстрый запуск

### Если у вас Supabase:

1. **Проверьте таблицу** в Supabase Dashboard:
   ```sql
   SELECT * FROM saved_commentaries LIMIT 1;
   ```

2. **Если таблицы нет, создайте:**
   ```sql
   CREATE TABLE saved_commentaries (
       id BIGSERIAL PRIMARY KEY,
       user_id BIGINT NOT NULL,
       book_id INTEGER NOT NULL,
       chapter_start INTEGER NOT NULL,
       chapter_end INTEGER,
       verse_start INTEGER,
       verse_end INTEGER,
       reference_text TEXT NOT NULL,
       commentary_text TEXT NOT NULL,
       commentary_type VARCHAR(20) DEFAULT 'ai',
       created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
       updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
   );
   
   CREATE INDEX idx_saved_commentaries_user_id ON saved_commentaries(user_id);
   ```

3. **Установите переменные окружения:**
   ```bash
   USE_SUPABASE=true
   SUPABASE_URL=your_url
   SUPABASE_KEY=your_key
   ```

4. **Перезапустите бота** - готово! 🎉

### Если у вас PostgreSQL:

1. **Установите переменные:**
   ```bash
   USE_POSTGRES=true
   POSTGRES_HOST=localhost
   POSTGRES_DB=your_db
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   ```

2. **Перезапустите бота** - таблица создастся автоматически! 🎉

## 🎮 Как использовать

1. **Откройте бота** → "📝 Мои закладки"
2. **Выберите** "📝 Сохраненные комментарии"
3. **Просматривайте** сохраненные комментарии
4. **Нажмите на комментарий** для просмотра полного текста
5. **Используйте "🗑️ Удалить"** при необходимости

## ⚠️ Важно

- **SQLite не поддерживается** - будет пустой список
- **Нужна Supabase или PostgreSQL** для работы системы
- **Комментарии сохраняются автоматически** при использовании ИИ помощника

## 🔧 Если что-то не работает

1. **Проверьте переменные окружения**
2. **Убедитесь, что таблица создана**
3. **Перезапустите бота**
4. **Проверьте логи на ошибки**

**Готово! Система комментариев работает!** ✨