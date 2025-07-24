# 🔧 Исправления закладок в v2.8.1

## 🐛 Проблема
При использовании Supabase SDK возникала ошибка при удалении закладок:
```
KeyError: 0
bookmark_exists = any(bm[0] == book_id and bm[1] == chapter for bm in bookmarks)
```

## 🔍 Причина
Код пытался обращаться к закладкам как к кортежам (`bm[0]`, `bm[1]`), но Supabase возвращает данные как словари с ключами `book_id`, `chapter`, `display_text`.

## ✅ Исправления

### Исправленные файлы:
1. **`handlers/bookmark_callbacks.py`** - 3 места с проверкой закладок
2. **`handlers/commands.py`** - 2 места с проверкой закладок  
3. **`handlers/bookmarks.py`** - 1 место с обработкой закладок
4. **`keyboards/main.py`** - добавлена поддержка словарей для кнопок

### Добавлена универсальная поддержка форматов:
```python
# Поддержка разных форматов данных
if bookmarks:
    if isinstance(bookmarks[0], dict):
        # Формат словаря (Supabase/PostgreSQL)
        bookmark_exists = any(bm['book_id'] == book_id and bm['chapter'] == chapter for bm in bookmarks)
    else:
        # Формат кортежа (SQLite)
        bookmark_exists = any(bm[0] == book_id and bm[1] == chapter for bm in bookmarks)
else:
    bookmark_exists = False
```

## 🐳 Docker образ v2.8.1

### Обновления:
- ✅ Исправлена работа с закладками в Supabase
- ✅ Поддержка всех форматов данных (SQLite, PostgreSQL, Supabase)
- ✅ Обратная совместимость с существующими данными

### Установка:
```bash
# Обновить и запустить
docker-compose -f docker-compose.supabase-sdk.yml down
docker-compose -f docker-compose.supabase-sdk.yml pull
docker-compose -f docker-compose.supabase-sdk.yml up -d

# Или напрямую
docker pull probedrik/gospel-bot:v2.8.1
```

## 🧪 Протестированные функции:
- ✅ Добавление закладок
- ✅ Удаление закладок  
- ✅ Просмотр списка закладок
- ✅ Проверка существования закладок
- ✅ Работа с планами чтения

## 📋 Проверка работы:

После обновления:
1. Добавьте закладку через бота
2. Попробуйте удалить закладку
3. Проверьте, что ошибка `KeyError: 0` больше не возникает

**Теперь закладки работают корректно со всеми типами баз данных!** ✅ 