# Исправления навигации и планов чтения v2.8.3

## Описание проблем

### 1. Ошибка при открытии планов чтения
**Проблема**: При попытке открыть план чтения возникала ошибка:
```
AttributeError: 'UniversalDatabaseManager' object has no attribute 'get_reading_parts_progress'
```

**Причина**: В новых менеджерах (UniversalDatabaseManager, SupabaseManager, PostgreSQLManager) метод называется `get_reading_part_progress` (без 's'), но в коде использовался старый вариант `get_reading_parts_progress`.

### 2. Неправильное отображение кнопок закладок при навигации
**Проблема**: При переходе между главами (например, с главы 21 на 22 и обратно) кнопка "Удалить закладку" меняется на "Добавить закладку", хотя закладка существует.

**Причина**: Функции `is_chapter_bookmarked` в `handlers/callbacks.py` и `handlers/text_messages.py` ожидали данные в формате кортежей (SQLite), но Supabase возвращает словари.

## Исправления

### 1. Исправление метода планов чтения
**Файлы**: `handlers/text_messages.py`, `database/db_manager.py`

- Исправлены вызовы `get_reading_parts_progress` на `get_reading_part_progress`
- Добавлен `await` для асинхронных вызовов
- Добавлен alias-метод в SQLite менеджер для обратной совместимости

```python
# В handlers/text_messages.py
completed_parts = set(
    await db_manager.get_reading_part_progress(user_id, plan_id, day_num))

# В database/db_manager.py
async def get_reading_part_progress(self, user_id: int, plan_id: str, day: int) -> list:
    """Alias для get_reading_parts_progress для совместимости с новыми менеджерами."""
    return self.get_reading_parts_progress(user_id, plan_id, day)
```

### 2. Исправление проверки статуса закладок
**Файлы**: `handlers/callbacks.py`, `handlers/text_messages.py`

Добавлена поддержка разных форматов данных - кортежей (SQLite) и словарей (Supabase/PostgreSQL):

```python
# Поддержка разных форматов данных
for bookmark in bookmarks:
    if isinstance(bookmark, dict):
        # Формат словаря (Supabase/PostgreSQL)
        bm_book_id = bookmark['book_id']
        bm_chapter = bookmark['chapter']
    else:
        # Формат кортежа (SQLite)
        bm_book_id, bm_chapter, _ = bookmark
    
    if bm_book_id == book_id and bm_chapter == chapter:
        return True
```

## Развертывание

### Обновление Docker образа
Образ `probedrik/gospel-bot:v2.8.3` опубликован на Docker Hub.

### Обновление docker-compose.supabase-sdk.yml
```yaml
services:
  bible-bot:
    image: probedrik/gospel-bot:v2.8.3  # Обновлено с v2.8.1
```

### Команды для применения исправлений

```bash
# Остановить текущий контейнер
docker-compose -f docker-compose.supabase-sdk.yml down

# Загрузить новый образ
docker pull probedrik/gospel-bot:v2.8.3

# Запустить обновленный контейнер
docker-compose -f docker-compose.supabase-sdk.yml up -d

# Проверить логи
docker-compose -f docker-compose.supabase-sdk.yml logs -f
```

## Результат

✅ **Планы чтения работают корректно** - исправлена ошибка с методом `get_reading_parts_progress`

✅ **Кнопки закладок отображаются правильно** - статус закладки корректно определяется при навигации между главами

✅ **Универсальная совместимость** - поддержка SQLite, PostgreSQL и Supabase форматов данных

## Тестирование

После обновления рекомендуется протестировать:

1. **Планы чтения**: открыть любой план чтения и убедиться, что нет ошибок
2. **Навигация с закладками**: 
   - Добавить закладку на главу
   - Перейти на следующую/предыдущую главу
   - Вернуться к закладке
   - Убедиться, что кнопка "Удалить закладку" отображается корректно

## Версия

**v2.8.3** - 30 декабря 2024
- Исправлена ошибка планов чтения
- Исправлено отображение кнопок закладок при навигации
- Улучшена совместимость с разными типами баз данных 