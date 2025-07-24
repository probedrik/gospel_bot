# 🎉 Миграция на Supabase SDK завершена!

## 📋 Что было сделано

### ✅ 1. Создание Supabase SDK менеджера
- ✅ Создан `database/supabase_manager.py` - менеджер для работы через Python SDK
- ✅ Обновлен `database/universal_manager.py` - добавлена поддержка Supabase
- ✅ Добавлена зависимость `supabase>=2.3.0` в `requirements.txt`

### ✅ 2. Docker образ v2.8.0
- ✅ Собран и опубликован новый Docker образ `probedrik/gospel-bot:v2.8.0`
- ✅ Образ включает поддержку Supabase SDK
- ✅ Все зависимости обновлены

### ✅ 3. Импорт планов чтения
- ✅ Планы чтения импортированы из CSV в Supabase таблицы
- ✅ Названия планов сокращены и улучшены:
  - 📖 **Евангелие на каждый день** (45 дней)
  - 📚 **Классический план за год** (366 дней) 
  - ⚖️ **План ВЗ и НЗ** (365 дней)

### ✅ 4. Тестирование и проверка
- ✅ Полное тестирование Supabase SDK
- ✅ Тестирование планов чтения и прогресса
- ✅ Все функции работают корректно

## 🚀 Как использовать

### Настройка .env файла
```bash
# Основные настройки
BOT_TOKEN=your_bot_token
ADMIN_ID=your_admin_id

# Supabase настройки
USE_SUPABASE=true
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_KEY=your_anon_key

# ИИ настройки
OPENAI_API_KEY=your_openai_key
AI_LIMIT_PER_DAY=10
```

### Запуск через Docker
```bash
# Использовать новый Docker Compose для Supabase
docker-compose -f docker-compose.supabase-sdk.yml up -d

# Или напрямую
docker run -d \
  --name gospel-bot \
  --env-file .env \
  probedrik/gospel-bot:v2.8.0
```

### Локальный запуск
```bash
# Установить зависимости
pip install -r requirements.txt

# Запустить бота
python bot.py
```

## 📚 Планы чтения

### Доступные планы:
1. **📖 Евангелие на каждый день** (`gospel-daily`)
   - 45 дней чтения Евангелий
   - Пример: "Мф 1; Мф 2"

2. **📚 Классический план за год** (`classic-1-year`)
   - 366 дней чтения всей Библии
   - Пример: "Лк 5:27-39; Быт 1:1-2:25; Пс 1"

3. **⚖️ План ВЗ и НЗ** (`ot-nt-plan`)
   - 365 дней параллельного чтения
   - Ветхий и Новый Завет

### Изменение названий планов:
Отредактируйте список `PLANS` в файле `import_reading_plans_simple.py`:

```python
PLANS = [
    {
        "id": "gospel-daily",
        "title": "📖 Ваше название",  # ← Измените здесь
        "description": "Ваше описание"
    },
    # ... остальные планы
]
```

Затем перезапустите импорт:
```bash
python import_reading_plans_simple.py
```

## 🔧 Техническая информация

### Архитектура
```
Bot (bot.py)
├── Universal Database Manager
│   ├── SQLite Manager (для локальной разработки)
│   ├── PostgreSQL Manager (для прямого подключения)
│   └── Supabase Manager (для Supabase SDK) ← НОВОЕ
│
├── Handlers (обработчики команд)
├── Services (планы чтения, локальная Библия)
└── Utils (вспомогательные функции)
```

### Переменные окружения
- `USE_SUPABASE=true` - использовать Supabase SDK
- `USE_POSTGRES=true` - использовать прямое подключение к PostgreSQL
- По умолчанию - SQLite

### Таблицы в Supabase
```sql
-- Основные таблицы
users                    -- Пользователи бота
bookmarks               -- Закладки пользователей
ai_usage                -- Использование ИИ
user_reading_plans      -- Планы чтения пользователей
reading_progress        -- Прогресс по дням
reading_parts_progress  -- Прогресс по частям дня

-- Планы чтения
reading_plans           -- Описание планов
reading_plan_days       -- Дни планов с текстом
```

## 🎯 Преимущества Supabase SDK

### ✅ По сравнению с прямым PostgreSQL:
- **Нет проблем с SSL** - работает через HTTPS API
- **Простая настройка** - только URL и API ключ
- **Надежность** - официальный SDK от Supabase
- **Безопасность** - встроенная поддержка RLS

### ✅ По сравнению с SQLite:
- **Облачная база данных** - доступ из любого места
- **Масштабируемость** - не ограничена размером файла
- **Надежность** - автоматические бэкапы
- **Планы чтения в БД** - не зависят от CSV файлов

## 🔍 Мониторинг и отладка

### Логи бота
```bash
# Локально
tail -f logs/bot.log

# Docker
docker logs -f gospel-bot-supabase
```

### Проверка подключения
```bash
# Тест Supabase SDK
python test_supabase_sdk.py

# Тест планов чтения
python test_reading_plans_supabase.py
```

### Supabase Dashboard
1. Перейдите в [Supabase Dashboard](https://app.supabase.com/)
2. Выберите ваш проект
3. **Database → Tables** - просмотр данных
4. **Logs** - мониторинг запросов

## 🛠️ Устранение неисправностей

### Проблема: "SUPABASE_URL и SUPABASE_KEY должны быть установлены"
**Решение:**
1. Проверьте `.env` файл
2. Убедитесь, что переменные заданы корректно
3. Перезапустите бот

### Проблема: "404 Not Found" для таблиц
**Решение:**
1. Выполните SQL скрипт `supabase_tables.sql` в Supabase
2. Или запустите `fix_supabase_tables.sql` для исправления

### Проблема: "401 Unauthorized"
**Решение:**
1. Проверьте правильность API ключа (должен быть `anon` ключ)
2. Убедитесь, что RLS правила настроены корректно

## 📋 Файлы проекта

### Новые файлы:
- `database/supabase_manager.py` - Менеджер Supabase SDK
- `docker-compose.supabase-sdk.yml` - Docker Compose для Supabase
- `env.supabase.example` - Пример настроек для Supabase
- `import_reading_plans_simple.py` - Импорт планов в Supabase
- `test_supabase_sdk.py` - Тест Supabase SDK
- `test_reading_plans_supabase.py` - Тест планов чтения
- `SUPABASE_SDK_SETUP.md` - Детальная инструкция

### Обновленные файлы:
- `database/universal_manager.py` - Добавлена поддержка Supabase
- `requirements.txt` - Добавлена зависимость supabase
- `supabase_tables.sql` - Исправлена структура таблиц

## 🎉 Готово!

Бот полностью готов к работе с Supabase через Python SDK. Все планы чтения импортированы и протестированы. 

**Docker образ v2.8.0 доступен на Docker Hub:** `probedrik/gospel-bot:v2.8.0`

### Следующие шаги:
1. ✅ Настройте `.env` с параметрами Supabase
2. ✅ Запустите бота: `docker-compose -f docker-compose.supabase-sdk.yml up -d`
3. ✅ Проверьте работу планов чтения в Telegram боте
4. ✅ При необходимости измените названия планов и переимпортируйте

**Миграция завершена успешно!** 🚀 