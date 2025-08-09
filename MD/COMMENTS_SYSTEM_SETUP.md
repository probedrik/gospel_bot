# 📝 Система сохраненных комментариев - Настройка

## 🎯 Обзор

Система сохраненных комментариев позволяет пользователям сохранять и просматривать толкования библейских отрывков. Комментарии хранятся в таблице `saved_commentaries` и доступны через интерфейс "Мои закладки".

## 🏗️ Архитектура

### Поддерживаемые базы данных:
- ✅ **Supabase** - полная поддержка
- ✅ **PostgreSQL** - полная поддержка  
- ❌ **SQLite** - не поддерживается (только заглушки)

### Структура таблицы `saved_commentaries`:
```sql
CREATE TABLE saved_commentaries (
    id SERIAL PRIMARY KEY,
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
```

## 🚀 Новые возможности

### 1. Кнопка "📝 Сохраненные комментарии"
Добавлена в главное меню закладок:
- 📖 Закладки Библии
- 💬 Сохраненные разборы  
- **📝 Сохраненные комментарии** ← НОВОЕ

### 2. Интерфейс просмотра
- **Пагинация**: 16 комментариев на странице в 2 столбца
- **Сортировка**: по дате создания (новые сверху)
- **Действия**: просмотр и удаление комментариев

### 3. Формат отображения
```
📝 Ин 3:16    📝 Быт 1:1
📝 Мф 5:3     📝 Пс 23:1
...
```

## 🔧 Настройка

### Для Supabase:

1. **Убедитесь, что таблица создана:**
   ```sql
   -- Таблица должна существовать в вашей Supabase базе
   SELECT * FROM saved_commentaries LIMIT 1;
   ```

2. **Настройте переменные окружения:**
   ```bash
   USE_SUPABASE=true
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```

3. **Установите зависимости:**
   ```bash
   pip install supabase
   ```

### Для PostgreSQL:

1. **Таблица создается автоматически** при инициализации `PostgreSQLManager`

2. **Настройте переменные окружения:**
   ```bash
   USE_POSTGRES=true
   POSTGRES_HOST=localhost
   POSTGRES_DB=your_db
   POSTGRES_USER=your_user
   POSTGRES_PASSWORD=your_password
   ```

## 📋 API функции

### Основные методы:

```python
# Сохранение комментария
await db_manager.save_commentary(
    user_id=user_id,
    book_id=43,  # Иоанн
    chapter_start=3,
    verse_start=16,
    reference_text="Ин 3:16",
    commentary_text="Толкование стиха...",
    commentary_type="ai"
)

# Получение комментариев пользователя
comments = await db_manager.get_saved_commentaries(user_id)

# Удаление комментария по ID
await db_manager.delete_saved_commentary(user_id, commentary_id=comment_id)
```

### Структура возвращаемых данных:
```python
{
    'id': 123,
    'book_id': 43,
    'chapter_start': 3,
    'chapter_end': None,
    'verse_start': 16,
    'verse_end': None,
    'reference_text': 'Ин 3:16',
    'commentary_text': 'Толкование стиха...',
    'commentary_type': 'ai',
    'created_at': '2025-01-27T10:30:00'
}
```

## 🎮 Использование

### Для пользователей:

1. **Откройте "📝 Мои закладки"**
2. **Выберите "📝 Сохраненные комментарии"**
3. **Просматривайте список комментариев**
4. **Нажмите на комментарий для просмотра**
5. **Используйте "🗑️ Удалить" при необходимости**

### Навигация:
- **⬅️ Назад / Далее ➡️** - переключение страниц
- **📄 1/3** - текущая страница
- **⬅️ К типам закладок** - возврат в меню

## 🔍 Отладка

### Проверка подключения:
```python
# Проверьте, какая база используется
from database.universal_manager import universal_db_manager as db_manager
print(f"Supabase: {db_manager.is_supabase}")
print(f"PostgreSQL: {db_manager.is_postgres}")
```

### Тестирование функций:
```python
# Тест сохранения
success = await db_manager.save_commentary(
    user_id=123, book_id=1, chapter_start=1,
    reference_text="Быт 1:1", commentary_text="Тест"
)
print(f"Сохранение: {success}")

# Тест получения
comments = await db_manager.get_saved_commentaries(123)
print(f"Комментариев: {len(comments)}")
```

## ⚠️ Ограничения

### SQLite:
- **Не поддерживается** - функции возвращают пустые результаты
- Кнопка "📝 Сохраненные комментарии" будет показывать пустой список
- Для разработки рекомендуется использовать PostgreSQL/Supabase

### Производительность:
- **Лимит**: 50 комментариев по умолчанию
- **Индексы**: созданы для быстрого поиска по user_id
- **Пагинация**: 16 элементов на странице

## 🚀 Развертывание

### Продакшн (Supabase):
1. Создайте таблицу в Supabase Dashboard
2. Настройте RLS (Row Level Security) политики
3. Установите переменные окружения
4. Перезапустите бота

### Разработка (PostgreSQL):
1. Установите PostgreSQL локально
2. Создайте базу данных
3. Настройте переменные окружения
4. Запустите бота - таблицы создадутся автоматически

## ✅ Проверочный список

- [ ] База данных настроена (Supabase/PostgreSQL)
- [ ] Переменные окружения установлены
- [ ] Зависимости установлены
- [ ] Таблица `saved_commentaries` создана
- [ ] Кнопка "📝 Сохраненные комментарии" появилась в меню
- [ ] Комментарии сохраняются и отображаются
- [ ] Удаление комментариев работает
- [ ] Пагинация функционирует

**Система готова к использованию!** 🎯