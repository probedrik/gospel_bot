# Настройка Supabase через Python SDK

Этот гайд поможет настроить подключение бота к Supabase через официальный Python SDK вместо прямого подключения к PostgreSQL. Это решает все проблемы с SSL сертификатами и упрощает настройку.

## 🎯 Преимущества Supabase SDK

- ✅ **Нет проблем с SSL** - работает через HTTPS API
- ✅ **Простая настройка** - только URL и API ключ
- ✅ **Автоматическая аутентификация** - встроенная в SDK
- ✅ **Надежность** - официальный SDK от Supabase
- ✅ **Безопасность** - поддержка Row Level Security (RLS)

## 📋 Пошаговая настройка

### 1. Получение данных из Supabase Dashboard

1. Откройте ваш проект в [Supabase Dashboard](https://app.supabase.com/)
2. Перейдите в **Settings → API**
3. Скопируйте:
   - **Project URL** (например: `https://abcdefgh.supabase.co`)
   - **Anon Key** (публичный API ключ)

### 2. Настройка переменных окружения

Создайте `.env` файл по примеру `env.supabase.example`:

```bash
# === НАСТРОЙКИ БОТА ===
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_user_id_here

# === НАСТРОЙКИ БАЗЫ ДАННЫХ ===
# Используем Supabase через Python SDK
USE_SUPABASE=true

# === НАСТРОЙКИ SUPABASE ===
SUPABASE_URL=https://your-project-ref.supabase.co
SUPABASE_KEY=your_supabase_anon_key_here

# === НАСТРОЙКИ ИИ ===
OPENAI_API_KEY=your_openai_api_key_here
AI_LIMIT_PER_DAY=10

# === ЛОГИРОВАНИЕ ===
LOG_LEVEL=INFO
```

### 3. Создание таблиц в Supabase

Используйте SQL редактор в Supabase Dashboard для создания таблиц:

```sql
-- Выполните скрипт из файла supabase_tables.sql
-- Или скопируйте SQL команды и выполните в SQL Editor
```

### 4. Установка зависимостей

```bash
pip install supabase
```

Или обновите все зависимости:

```bash
pip install -r requirements.txt
```

### 5. Тестирование подключения

Запустите тестовый скрипт:

```bash
python test_supabase_sdk.py
```

Вы должны увидеть:
```
=== ТЕСТИРОВАНИЕ SUPABASE SDK ===

🔄 Тестирование подключения к Supabase через SDK...
📋 URL: https://your-project.supabase.co
🔑 Key: eyJhbGciOiJIUzI1NiIs...
✅ Supabase менеджер создан
✅ Подключение инициализировано

🧪 Тестирование базовых операций...
📝 Тестирование пользователя 123456789...
✅ Пользователь добавлен
✅ Пользователь получен: test_user
📖 Тестирование закладок...
✅ Закладка добавлена
📋 Найдено закладок: 1
🤖 Тестирование AI лимитов...
✅ AI счетчик увеличен
📊 AI использований сегодня: 1
📚 Тестирование планов чтения...
✅ План чтения установлен
📅 Планов чтения у пользователя: 1

🧹 Очистка тестовых данных...
✅ Тестовые данные очищены
✅ Соединение закрыто

🎉 Все тесты прошли успешно!
✅ Supabase SDK готов к использованию

✅ Тестирование завершено успешно!
```

## 🚀 Запуск бота

### Локально

```bash
python bot.py
```

### Docker

```bash
# Используйте специальный Docker Compose для Supabase SDK
docker-compose -f docker-compose.supabase-sdk.yml up -d
```

## 🔍 Устранение неисправностей

### Ошибка "SUPABASE_URL и SUPABASE_KEY должны быть установлены"

**Решение:**
1. Проверьте наличие `.env` файла
2. Убедитесь, что переменные `SUPABASE_URL` и `SUPABASE_KEY` заданы
3. Перезапустите приложение

### Ошибка "No module named 'supabase'"

**Решение:**
```bash
pip install supabase
```

### Ошибка "401 Unauthorized"

**Решение:**
1. Проверьте правильность API ключа (должен быть `anon` ключ)
2. Убедитесь, что RLS правила настроены корректно
3. Проверьте, что таблицы созданы в правильной схеме

### Ошибка "404 Not Found" для таблиц

**Решение:**
1. Убедитесь, что все таблицы созданы в Supabase
2. Запустите SQL скрипт `supabase_tables.sql`
3. Проверьте права доступа к таблицам

### Проблемы с RLS (Row Level Security)

Если включен RLS, но нет правил доступа:

```sql
-- Отключить RLS для всех таблиц (только для разработки!)
ALTER TABLE users DISABLE ROW LEVEL SECURITY;
ALTER TABLE bookmarks DISABLE ROW LEVEL SECURITY;
ALTER TABLE ai_usage DISABLE ROW LEVEL SECURITY;
ALTER TABLE user_reading_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE reading_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE reading_parts_progress DISABLE ROW LEVEL SECURITY;
ALTER TABLE reading_plans DISABLE ROW LEVEL SECURITY;
ALTER TABLE reading_plan_days DISABLE ROW LEVEL SECURITY;
```

## 📊 Мониторинг

### Логи бота

```bash
# Локально
tail -f logs/bot.log

# Docker
docker logs -f gospel-bot-supabase
```

### Мониторинг в Supabase

1. Откройте Supabase Dashboard
2. Перейдите в **Database → Tables** для просмотра данных
3. Используйте **Logs** для мониторинга запросов

## 🔄 Переход с PostgreSQL на Supabase SDK

Если вы уже используете прямое подключение к PostgreSQL:

1. **Обновите .env файл:**
   ```bash
   # Замените
   USE_POSTGRES=true
   # На
   USE_SUPABASE=true
   ```

2. **Добавьте Supabase настройки:**
   ```bash
   SUPABASE_URL=https://your-project.supabase.co
   SUPABASE_KEY=your_anon_key
   ```

3. **Удалите PostgreSQL настройки:**
   - Можете оставить или удалить `POSTGRES_*` переменные

4. **Перезапустите бот**

## 💡 Рекомендации

### Безопасность

1. **Никогда не используйте `service_role` ключ** в продакшене
2. **Используйте только `anon` ключ** для клиентских приложений
3. **Настройте RLS правила** для защиты данных
4. **Регулярно ротируйте API ключи**

### Производительность

1. **Индексы:** Убедитесь, что созданы индексы для часто запрашиваемых полей
2. **Кэширование:** Рассмотрите кэширование часто используемых данных
3. **Пагинация:** Используйте пагинацию для больших наборов данных

### Мониторинг

1. **Настройте алерты** в Supabase Dashboard
2. **Мониторьте использование API** quota
3. **Отслеживайте логи ошибок**

## 🎉 Готово!

Теперь ваш бот использует Supabase через официальный Python SDK без проблем с SSL сертификатами! 